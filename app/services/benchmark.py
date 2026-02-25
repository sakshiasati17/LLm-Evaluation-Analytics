"""BenchmarkService — loads and runs standardised benchmark datasets."""

import json
from pathlib import Path

from app.schemas.evaluation import EvaluationCase, RunEvalRequest, RunEvalResponse
from app.services.evaluator import EvaluatorService


BENCHMARK_CATALOG: dict[str, dict] = {
    "mmlu_sample": {
        "name": "MMLU Sample",
        "description": "Multiple-choice knowledge questions across science, history, economics, and CS",
        "category": "knowledge",
    },
    "truthfulqa_sample": {
        "name": "TruthfulQA Sample",
        "description": "Questions designed to catch common misconceptions and hallucinations",
        "category": "hallucination",
    },
    "reasoning_sample": {
        "name": "Reasoning Sample",
        "description": "Multi-step logic, math, and pattern recognition problems",
        "category": "reasoning",
    },
    "coding_sample": {
        "name": "Coding Sample",
        "description": "Python programming tasks with expected implementations",
        "category": "coding",
    },
}


class BenchmarkService:
    def __init__(self, benchmarks_dir: Path, evaluator: EvaluatorService) -> None:
        self.benchmarks_dir = benchmarks_dir
        self.evaluator = evaluator

    # ── List ──────────────────────────────────────────────────────────
    def list_benchmarks(self) -> list[dict]:
        results = []
        for key, meta in BENCHMARK_CATALOG.items():
            cases = self._load_cases(key)
            results.append({
                "name": key,
                "display_name": meta["name"],
                "description": meta["description"],
                "category": meta["category"],
                "total_cases": len(cases),
            })
        return results

    # ── Load ──────────────────────────────────────────────────────────
    def load_benchmark(self, name: str) -> list[EvaluationCase]:
        if name not in BENCHMARK_CATALOG:
            raise KeyError(f"Unknown benchmark: {name}. Available: {list(BENCHMARK_CATALOG)}")
        return self._load_cases(name)

    # ── Run ───────────────────────────────────────────────────────────
    async def run_benchmark(
        self,
        name: str,
        model_id: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> RunEvalResponse:
        cases = self.load_benchmark(name)
        request = RunEvalRequest(
            model_id=model_id,
            cases=cases,
            prompt_version=f"benchmark-{name}",
            dataset_version=name,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return await self.evaluator.run_eval(request)

    # ── Internal ──────────────────────────────────────────────────────
    def _load_cases(self, name: str) -> list[EvaluationCase]:
        path = self.benchmarks_dir / f"{name}.jsonl"
        if not path.exists():
            raise FileNotFoundError(f"Benchmark dataset not found: {path}")
        cases: list[EvaluationCase] = []
        for line in path.read_text(encoding="utf-8").strip().splitlines():
            raw = json.loads(line)
            cases.append(
                EvaluationCase(
                    id=raw["id"],
                    question=raw["question"],
                    reference_answer=raw.get("reference_answer"),
                    metadata=raw.get("metadata", {}),
                )
            )
        return cases
