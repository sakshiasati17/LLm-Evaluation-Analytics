from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_settings
from app.services.alerts import AlertService
from app.services.analytics import AnalyticsService
from app.services.evaluator import EvaluatorService
from app.services.gate import EvalGateService
from app.services.model_registry import ModelRegistry
from app.services.run_store import RunStore


def create_app() -> FastAPI:
    settings = get_settings()
    registry = ModelRegistry(settings=settings)
    run_store = RunStore(artifact_dir=settings.run_artifacts_path)
    analytics = AnalyticsService(run_store=run_store)
    evaluator = EvaluatorService(registry=registry, run_store=run_store)
    eval_gate = EvalGateService()
    alerts = AlertService(settings=settings)

    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.state.settings = settings
    app.state.registry = registry
    app.state.evaluator = evaluator
    app.state.analytics = analytics
    app.state.eval_gate = eval_gate
    app.state.alerts = alerts
    app.include_router(router, prefix="/api/v1", tags=["evaluation"])
    return app


app = create_app()
