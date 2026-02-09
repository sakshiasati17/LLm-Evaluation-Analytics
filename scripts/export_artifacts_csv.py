#!/usr/bin/env python3
import csv
import json
from pathlib import Path


def main() -> int:
    runs_dir = Path("artifacts/runs")
    out_dir = Path("artifacts/exports")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "evaluations.csv"

    rows: list[dict[str, object]] = []
    if runs_dir.exists():
        for path in sorted(runs_dir.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            summary = payload.get("summary", {})
            version_info = payload.get("version_info", {})
            rows.append(
                {
                    "run_id": payload.get("run_id"),
                    "timestamp_utc": path.name.split("_")[0] if "_" in path.name else "",
                    "model_id": payload.get("model_id"),
                    "prompt_version": version_info.get("prompt_version"),
                    "dataset_version": version_info.get("dataset_version"),
                    "avg_accuracy": summary.get("avg_accuracy"),
                    "avg_hallucination_risk": summary.get("avg_hallucination_risk"),
                    "avg_safety_risk": summary.get("avg_safety_risk"),
                    "avg_latency_ms": summary.get("avg_latency_ms"),
                    "total_cost_usd": summary.get("total_cost_usd"),
                    "total_cases": summary.get("total_cases"),
                }
            )

    fieldnames = [
        "run_id",
        "timestamp_utc",
        "model_id",
        "prompt_version",
        "dataset_version",
        "avg_accuracy",
        "avg_hallucination_risk",
        "avg_safety_risk",
        "avg_latency_ms",
        "total_cost_usd",
        "total_cases",
    ]

    with out_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows -> {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
