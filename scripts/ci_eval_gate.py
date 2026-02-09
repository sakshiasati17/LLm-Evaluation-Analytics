#!/usr/bin/env python3
import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import create_app


def load_cases(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")
    cases: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        cases.append(
            {
                "id": row["id"],
                "question": row["question"],
                "reference_answer": row.get("reference_answer"),
            }
        )
    return cases


def main() -> int:
    dataset_path = Path("datasets/baseline_v1.jsonl")
    cases = load_cases(dataset_path)

    payload = {
        "model_id": "mock-local",
        "prompt_version": "prompt-v1",
        "dataset_version": "baseline-v1",
        "cases": cases,
        "thresholds": {"min_accuracy": 0.0, "max_hallucination_risk": 1.0},
    }

    client = TestClient(create_app())
    response = client.post("/api/v1/eval-gate", json=payload)
    if response.status_code != 200:
        print(f"Eval gate request failed: {response.status_code} {response.text}")
        return 2

    result = response.json()
    print(json.dumps(result["run"]["summary"], indent=2))
    if not result["passed"]:
        print("Eval gate failed:")
        for reason in result["reasons"]:
            print(f"- {reason}")
        return 1

    print("Eval gate passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
