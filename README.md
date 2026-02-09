# LLM Evaluation & Monitoring Platform

Production-focused platform for evaluating, comparing, and monitoring LLMs across quality, latency, safety, and cost.

## Why this project

Most AI projects stop at building a chatbot. This repo targets the next step: operating LLM systems reliably in production.

Core goals:
- Benchmark multiple providers/models with the same test cases
- Track accuracy, hallucination indicators, latency, and token cost
- Detect regressions before deployment
- Expose data for BI dashboards (Power BI/Tableau/etc.)

## Tech stack

- Python 3.11+
- FastAPI
- PostgreSQL (planned persistence integration)
- YAML-based model registry
- Multi-provider adapter layer (OpenAI, Anthropic, Google, Cohere)

## Repository structure

```text
.
├── .github/workflows      # CI including eval gate
├── app
│   ├── adapters          # Provider-specific model adapters
│   ├── api               # FastAPI routes
│   ├── core              # Settings/config loading
│   ├── schemas           # Pydantic request/response contracts
│   └── services          # Evaluation logic and model registry
├── config
│   └── models.yaml       # Model catalog + pricing metadata
├── datasets              # Versioned benchmark datasets
├── scripts               # CI gate scripts and utilities
├── tests
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

## Quickstart

1. Create virtual environment and install deps:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

2. Configure environment:

```bash
cp .env.example .env
```

3. Run API:

```bash
uvicorn app.main:app --reload
```

4. Open docs:

- Swagger UI: `http://127.0.0.1:8000/docs`

## API endpoints

- `GET /api/v1/health` - service health
- `GET /api/v1/models` - available model IDs/config
- `POST /api/v1/run-eval` - run evaluation on one model
- `POST /api/v1/compare` - run side-by-side comparison across models
- `POST /api/v1/eval-gate` - run eval and apply CI/CD gate thresholds

## Example request

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/run-eval" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "gpt-5-mini",
    "cases": [
      {"id":"c1","question":"What is 12 * 9?","reference_answer":"108"},
      {"id":"c2","question":"Capital of France?","reference_answer":"Paris"}
    ]
  }'
```

## Notes

- Default config includes 4 major providers and one local mock model.
- Cost is estimated via configurable per-1k token pricing in `config/models.yaml`.
- Scoring is intentionally lightweight in v0.1 and designed for extension.

## Must-have features implemented

### 1) Prompt/Dataset versioning

- `POST /api/v1/run-eval` supports:
  - `prompt_version`
  - `dataset_version`
- Every run response includes `version_info`.
- Run artifacts are persisted as JSON in `artifacts/runs/` for reproducibility.

### 2) CI/CD eval gate

- `POST /api/v1/eval-gate` applies threshold checks:
  - `min_accuracy`
  - `max_hallucination_risk`
  - optional `max_latency_ms`
  - optional `max_cost_usd`
- Gate output includes `passed` plus detailed fail reasons.
- GitHub Actions workflow: `.github/workflows/eval-gate.yml`.

### 3) Alerting (Slack/Email)

- When gate fails and `ALERT_ON_GATE_FAIL=true`, alerts can be sent to:
  - Slack webhook (`SLACK_WEBHOOK_URL`)
  - SMTP email recipients (`ALERT_TO_EMAILS`)
- Alerting is non-blocking. Eval result is still returned if alert delivery fails.

## CI gate run

```bash
python scripts/ci_eval_gate.py
```

## Next roadmap

- Drift monitoring worker (weekly trend comparisons)
- Human-in-the-loop review queue
- PostgreSQL persistence + Power BI semantic model
