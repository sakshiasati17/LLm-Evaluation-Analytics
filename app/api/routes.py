from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.config import Settings
from app.schemas.evaluation import (
    CompareRequest,
    CompareResponse,
    EvalGateRequest,
    EvalGateResponse,
    MetricsResponse,
    ModelComparisonResponse,
    RunEvalRequest,
    RunEvalResponse,
)
from app.services.alerts import AlertService
from app.services.analytics import AnalyticsService
from app.services.db_store import DBStore
from app.services.evaluator import EvaluatorService
from app.services.gate import EvalGateService
from app.services.model_registry import ModelRegistry

router = APIRouter()


def get_registry(request: Request) -> ModelRegistry:
    return request.app.state.registry


def get_evaluator(request: Request) -> EvaluatorService:
    return request.app.state.evaluator


def get_gate_service(request: Request) -> EvalGateService:
    return request.app.state.eval_gate


def get_alert_service(request: Request) -> AlertService:
    return request.app.state.alerts


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_analytics(request: Request) -> AnalyticsService:
    return request.app.state.analytics


def get_db_store(request: Request) -> DBStore:
    return request.app.state.db_store


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/models")
async def models(registry: ModelRegistry = Depends(get_registry)) -> dict[str, object]:
    return {"default_model": registry.get_default_model_id(), "models": registry.list_models()}


@router.get("/metrics", response_model=MetricsResponse)
async def metrics(
    model_id: str | None = None,
    prompt_version: str | None = None,
    dataset_version: str | None = None,
    limit: int = 100,
    analytics: AnalyticsService = Depends(get_analytics),
) -> MetricsResponse:
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="limit must be in range 1..500.")
    return analytics.get_metrics(
        model_id=model_id,
        prompt_version=prompt_version,
        dataset_version=dataset_version,
        limit=limit,
    )


@router.get("/model-comparison", response_model=ModelComparisonResponse)
async def model_comparison(
    prompt_version: str | None = None,
    dataset_version: str | None = None,
    limit: int = 400,
    analytics: AnalyticsService = Depends(get_analytics),
) -> ModelComparisonResponse:
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="limit must be in range 1..1000.")
    return analytics.get_model_comparison(
        prompt_version=prompt_version,
        dataset_version=dataset_version,
        limit=limit,
    )


@router.post("/run-eval", response_model=RunEvalResponse)
async def run_eval(
    payload: RunEvalRequest,
    evaluator: EvaluatorService = Depends(get_evaluator),
    db_store: DBStore = Depends(get_db_store),
) -> RunEvalResponse:
    try:
        result = await evaluator.run_eval(payload)
        db_store.save(result)
        # Broadcast to WebSocket clients for real-time dashboard updates
        from app.main import ws_manager
        await ws_manager.broadcast({"event": "eval_complete", "model_id": result.model_id, "run_id": result.run_id})
        return result
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/compare", response_model=CompareResponse)
async def compare(
    payload: CompareRequest,
    evaluator: EvaluatorService = Depends(get_evaluator),
    db_store: DBStore = Depends(get_db_store),
) -> CompareResponse:
    if not payload.model_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="model_ids must contain at least one model."
        )

    run_request = RunEvalRequest(
        model_id=None,
        cases=payload.cases,
        system_prompt=payload.system_prompt,
        prompt_version=payload.prompt_version,
        dataset_version=payload.dataset_version,
        prompt_template=payload.prompt_template,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
    )
    try:
        runs = await evaluator.compare(payload.model_ids, run_request)
        for run in runs:
            db_store.save(run)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return CompareResponse(runs=runs)


@router.post("/eval-gate", response_model=EvalGateResponse)
async def eval_gate(
    payload: EvalGateRequest,
    evaluator: EvaluatorService = Depends(get_evaluator),
    gate_service: EvalGateService = Depends(get_gate_service),
    alert_service: AlertService = Depends(get_alert_service),
    settings: Settings = Depends(get_settings),
) -> EvalGateResponse:
    run_request = RunEvalRequest(
        model_id=payload.model_id,
        cases=payload.cases,
        system_prompt=payload.system_prompt,
        prompt_version=payload.prompt_version,
        dataset_version=payload.dataset_version,
        prompt_template=payload.prompt_template,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
    )
    try:
        run = await evaluator.run_eval(run_request)
        gate_result = gate_service.evaluate(run=run, thresholds=payload.thresholds)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if settings.alert_on_gate_fail and not gate_result.passed:
        try:
            title = (
                f"[LLM Eval Gate Failed] model={gate_result.run.model_id} "
                f"prompt={gate_result.run.version_info.prompt_version} "
                f"dataset={gate_result.run.version_info.dataset_version}"
            )
            await alert_service.send_gate_failure(title=title, details=gate_result.reasons)
        except Exception as exc:  # noqa: BLE001
            gate_result.reasons.append(f"alerting_failed: {exc}")
    return gate_result
