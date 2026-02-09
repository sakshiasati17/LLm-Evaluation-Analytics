# Power BI Setup

## Goal

Visualize LLM evaluation analytics:
- Accuracy trend
- Hallucination risk trend
- Latency trend
- Cost trend
- Model vs model comparison

## Option A: CSV ingestion (quick start)

1. Generate CSV from local run artifacts:

```bash
python scripts/export_artifacts_csv.py
```

2. Open Power BI Desktop.
3. Get Data -> Text/CSV.
4. Select `artifacts/exports/evaluations.csv`.
5. Build visuals using these columns:
- `run_id`
- `timestamp_utc`
- `model_id`
- `prompt_version`
- `dataset_version`
- `avg_accuracy`
- `avg_hallucination_risk`
- `avg_latency_ms`
- `total_cost_usd`
- `total_cases`

## Option B: PostgreSQL ingestion (production path)

1. Apply schema from `sql/analytics_schema.sql`.
2. Load run/evaluation data into those tables.
3. In Power BI:
- Get Data -> PostgreSQL database
- Choose DirectQuery or Import mode
- Import:
  - `runs`
  - `evaluations`
  - `scores`

## Suggested dashboard pages

1. Model Health
- Cards: avg accuracy, avg hallucination risk, avg latency, total cost
- Trend lines over time

2. Regression Tracking
- Slicer: `prompt_version`, `dataset_version`, `model_id`
- Delta vs previous run

3. Cost & Throughput
- Cost by model
- Tokens by model
- Cases processed over time

4. Comparison
- Bar charts comparing models per metric
