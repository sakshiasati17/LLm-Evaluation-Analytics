from statistics import mean

from app.schemas.evaluation import (
    MetricsResponse,
    MetricsSummary,
    ModelComparisonItem,
    ModelComparisonResponse,
    RunEvalResponse,
    RunMetricItem,
)
from app.services.run_store import RunStore


class AnalyticsService:
    def __init__(self, run_store: RunStore) -> None:
        self.run_store = run_store

    def get_metrics(
        self,
        model_id: str | None = None,
        prompt_version: str | None = None,
        dataset_version: str | None = None,
        limit: int = 100,
    ) -> MetricsResponse:
        runs = self._filtered_runs(
            model_id=model_id,
            prompt_version=prompt_version,
            dataset_version=dataset_version,
            limit=limit,
        )
        items = [self._to_item(run) for run in runs]
        summary = self._summarize(items)
        return MetricsResponse(total_runs=len(items), summary=summary, items=items)

    def get_model_comparison(
        self,
        prompt_version: str | None = None,
        dataset_version: str | None = None,
        limit: int = 400,
    ) -> ModelComparisonResponse:
        runs = self._filtered_runs(
            model_id=None,
            prompt_version=prompt_version,
            dataset_version=dataset_version,
            limit=limit,
        )
        by_model: dict[str, list[RunEvalResponse]] = {}
        for run in runs:
            by_model.setdefault(run.model_id, []).append(run)

        models: list[ModelComparisonItem] = []
        for mid, model_runs in by_model.items():
            models.append(
                ModelComparisonItem(
                    model_id=mid,
                    runs=len(model_runs),
                    avg_accuracy=round(mean(r.summary.avg_accuracy for r in model_runs), 3),
                    avg_hallucination_risk=round(
                        mean(r.summary.avg_hallucination_risk for r in model_runs), 3
                    ),
                    avg_safety_risk=round(mean(r.summary.avg_safety_risk for r in model_runs), 3),
                    avg_latency_ms=round(mean(r.summary.avg_latency_ms for r in model_runs), 2),
                    total_cost_usd=round(sum(r.summary.total_cost_usd for r in model_runs), 6),
                    total_cases=sum(r.summary.total_cases for r in model_runs),
                )
            )

        models.sort(key=lambda item: item.avg_accuracy, reverse=True)
        return ModelComparisonResponse(total_models=len(models), models=models)

    def _filtered_runs(
        self,
        model_id: str | None,
        prompt_version: str | None,
        dataset_version: str | None,
        limit: int,
    ) -> list[RunEvalResponse]:
        runs = self.run_store.list_runs(limit=max(limit * 4, 100))
        filtered = [
            run
            for run in runs
            if (not model_id or run.model_id == model_id)
            and (not prompt_version or run.version_info.prompt_version == prompt_version)
            and (not dataset_version or run.version_info.dataset_version == dataset_version)
        ]
        return filtered[:limit]

    def _to_item(self, run: RunEvalResponse) -> RunMetricItem:
        return RunMetricItem(
            run_id=run.run_id,
            created_at=run.created_at or "",
            model_id=run.model_id,
            prompt_version=run.version_info.prompt_version,
            dataset_version=run.version_info.dataset_version,
            avg_accuracy=run.summary.avg_accuracy,
            avg_hallucination_risk=run.summary.avg_hallucination_risk,
            avg_safety_risk=run.summary.avg_safety_risk,
            avg_latency_ms=run.summary.avg_latency_ms,
            total_cost_usd=run.summary.total_cost_usd,
            total_cases=run.summary.total_cases,
        )

    def _summarize(self, items: list[RunMetricItem]) -> MetricsSummary:
        if not items:
            return MetricsSummary(
                avg_accuracy=0.0,
                avg_hallucination_risk=0.0,
                avg_safety_risk=0.0,
                avg_latency_ms=0.0,
                total_cost_usd=0.0,
                total_cases=0,
            )

        return MetricsSummary(
            avg_accuracy=round(mean(item.avg_accuracy for item in items), 3),
            avg_hallucination_risk=round(mean(item.avg_hallucination_risk for item in items), 3),
            avg_safety_risk=round(mean(item.avg_safety_risk for item in items), 3),
            avg_latency_ms=round(mean(item.avg_latency_ms for item in items), 2),
            total_cost_usd=round(sum(item.total_cost_usd for item in items), 6),
            total_cases=sum(item.total_cases for item in items),
        )
