"""TaskRecommender — maps task categories to recommended models and benchmarks."""

from pathlib import Path

import yaml

from app.schemas.evaluation import RunEvalResponse
from app.services.benchmark import BenchmarkService
from app.services.model_registry import ModelRegistry


class TaskRecommender:
    def __init__(
        self,
        tasks_path: Path,
        registry: ModelRegistry,
        benchmark_service: BenchmarkService,
    ) -> None:
        self.registry = registry
        self.benchmark_service = benchmark_service
        self.tasks: list[dict] = []
        self._load(tasks_path)

    # ── Load ──────────────────────────────────────────────────────────
    def _load(self, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"Tasks config not found: {path}")
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.tasks = payload.get("tasks", [])

    # ── List ──────────────────────────────────────────────────────────
    def list_tasks(self) -> list[dict]:
        return [
            {
                "id": t["id"],
                "name": t["name"],
                "description": t["description"],
                "benchmark": t["benchmark"],
                "recommended_models": t["recommended_models"],
            }
            for t in self.tasks
        ]

    # ── Get single task ──────────────────────────────────────────────
    def get_task(self, task_id: str) -> dict:
        for t in self.tasks:
            if t["id"] == task_id:
                return t
        raise KeyError(f"Unknown task_id: {task_id}. Available: {[t['id'] for t in self.tasks]}")

    # ── Recommend ────────────────────────────────────────────────────
    def get_recommendations(self, task_id: str) -> dict:
        task = self.get_task(task_id)
        # Filter to only models that are actually enabled in the registry
        available = []
        for mid in task["recommended_models"]:
            try:
                model = self.registry.get_model(mid)
                available.append({
                    "id": model.id,
                    "provider": str(model.provider),
                    "api_model": model.api_model,
                    "enabled": model.enabled,
                    "pricing": {
                        "prompt_per_1k": model.pricing.prompt_per_1k,
                        "completion_per_1k": model.pricing.completion_per_1k,
                    },
                })
            except (KeyError, ValueError):
                # Model not found or disabled — skip
                continue

        return {
            "task": {
                "id": task["id"],
                "name": task["name"],
                "description": task["description"],
                "benchmark": task["benchmark"],
                "recommended_models": task["recommended_models"],
            },
            "available_models": available,
        }

    # ── Run ───────────────────────────────────────────────────────────
    async def run_task_evaluation(
        self,
        task_id: str,
        model_id: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> tuple[dict, RunEvalResponse]:
        task = self.get_task(task_id)
        # Use provided model or first available recommended model
        if model_id is None:
            for mid in task["recommended_models"]:
                try:
                    self.registry.get_model(mid)
                    model_id = mid
                    break
                except (KeyError, ValueError):
                    continue
        if model_id is None:
            raise ValueError(f"No available models for task '{task_id}'.")

        run = await self.benchmark_service.run_benchmark(
            name=task["benchmark"],
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return task, run
