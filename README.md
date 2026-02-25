# SentinelAI

## LLM Evaluation & Monitoring Platform

**Production AI reliability, testing & observability.**

---

## One-line summary

**SentinelAI is like Google Analytics + unit testing for AI models.** It automatically tests answers, measures accuracy, checks hallucinations, compares models, tracks latency and token cost, and exposes dashboards — so you always know *"Is our AI working correctly?"*

---

## Why this project

Most AI projects stop at building a chatbot. This repo targets the next step: **operating LLM systems reliably in production**.

### Real-world problem

When companies deploy LLMs:

- answers silently degrade  
- hallucinations increase  
- costs spike  
- latency grows  
- prompt updates break behavior  
- there is no visibility  

Unlike normal software, AI has **no monitoring or testing by default**.

### What companies need

- automated testing  
- evaluation  
- regression detection  
- observability  
- dashboards  

This is what **AI infra teams** at OpenAI, Anthropic, Databricks, and Amazon build internally.

### The solution

**SentinelAI** — a full-stack platform to **evaluate, monitor, and benchmark LLMs in production**.

---

## Architecture

```
Test Dataset (JSONL)
        ↓
FastAPI API Layer (/api/v1/*)
        ↓
Evaluation Engine (Python Services)
        ↓
Model Adapters (OpenAI | Anthropic | Google | Cohere | Mock)
        ↓
Scoring + Metrics + Versioned Artifacts
        ↓
Run Store (JSON) + PostgreSQL (optional)
        ↓
Web Analytics Dashboard (/dashboard)
```

---

## Tech stack

| Layer        | Technology |
| ------------ | ---------- |
| API          | FastAPI |
| Runtime      | Python 3.11+ |
| Adapters     | OpenAI, Anthropic, Google, Cohere, Mock (dev) |
| Config       | YAML (`config/models.yaml`) |
| Persistence  | JSON artifacts + PostgreSQL |
| Analytics    | Built-in Web Dashboard + Power BI via CSV export |
| CI/CD        | GitHub Actions |

- YAML-based model registry; multi-provider adapter layer.

---

## Core features

- **Automated testing** — run many test prompts automatically  
- **Accuracy scoring** — measure correctness vs ground truth  
- **Hallucination detection** — check unsupported claims  
- **Latency monitoring** — track response time (ms)  
- **Cost tracking** — monitor token spend (configurable per 1k pricing)  
- **Model benchmarking** — GPT vs Claude vs Gemini vs Cohere  
- **Regression detection** — catch performance drops before deploy  
- **Dashboards** — built-in web dashboard at `/dashboard` + Power BI analytics via CSV export  
- **CI/CD eval gate** — block bad models before deploy  
- **Alerting** — Slack / email on gate failure  
- **Prompt & dataset versioning** — reproducible runs  

---

## Repository structure

```text
.
├── app/
│   ├── adapters/          # Provider-specific model adapters
│   │   ├── base.py        # Base adapter interface
│   │   ├── openai_adapter.py
│   │   ├── anthropic_adapter.py
│   │   ├── google_adapter.py
│   │   ├── cohere_adapter.py
│   │   └── mock_adapter.py
│   ├── api/
│   │   └── routes.py      # FastAPI endpoints
│   ├── core/
│   │   └── config.py      # Settings
│   ├── schemas/
│   │   └── evaluation.py  # Pydantic models
│   ├── services/
│   │   ├── evaluator.py   # Evaluation orchestration
│   │   ├── analytics.py   # Metrics aggregation
│   │   ├── gate.py        # CI gate logic
│   │   ├── alerts.py      # Slack/email
│   │   ├── model_registry.py
│   │   ├── run_store.py   # JSON artifact persistence
│   │   └── db_store.py    # PostgreSQL persistence
│   ├── static/
│   │   └── dashboard.html # Web analytics dashboard
│   └── main.py
├── config/
│   └── models.yaml        # Model catalog + pricing
├── datasets/
│   └── baseline_v1.jsonl  # Versioned test cases
├── scripts/
│   ├── ci_eval_gate.py    # CI gate runner
│   └── export_artifacts_csv.py  # Power BI CSV export
├── sql/
│   └── analytics_schema.sql
├── docs/
│   ├── architecture.md
│   ├── powerbi.md
│   └── SENTINELAI_REPORT.md
├── tests/
│   └── test_api.py
├── .github/workflows/
│   └── eval-gate.yml      # GitHub Actions
├── .env.example           # Environment template
├── Makefile               # run, test, lint, gate, export-csv
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

---

## Quickstart

1. Create virtual environment and install deps:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Or: `make setup`

2. Configure environment:

```bash
cp .env.example .env
```

Set provider API keys in `.env` as needed (optional for `mock-local`).

3. Run API:

```bash
uvicorn app.main:app --reload
```

Or: `make run`

4. Open docs:

- Swagger UI: `http://127.0.0.1:8000/docs`
- Analytics Dashboard: `http://127.0.0.1:8000/dashboard`

---

## API endpoints

- `GET /api/v1/health` — service health  
- `GET /api/v1/models` — available model IDs/config  
- `GET /api/v1/metrics` — aggregated run metrics (query: `model_id`, `prompt_version`, `dataset_version`, `limit`)  
- `GET /api/v1/model-comparison` — model-level comparison (query: `prompt_version`, `dataset_version`, `limit`)  
- `POST /api/v1/run-eval` — run evaluation on one model  
- `POST /api/v1/compare` — side-by-side comparison across models  
- `POST /api/v1/eval-gate` — run eval and apply CI/CD gate thresholds  

---

## Example request

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/run-eval" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "gpt-4o-mini",
    "cases": [
      {"id":"c1","question":"What is 12 * 9?","reference_answer":"108"},
      {"id":"c2","question":"Capital of France?","reference_answer":"Paris"}
    ]
  }'
```

---

## Metrics computed

| Metric              | Meaning |
| ------------------- | ------- |
| Accuracy            | Correctness vs ground truth |
| Hallucination risk  | Unsupported / fabricated claims |
| Safety risk         | Policy / content violations |
| Latency             | Response time (ms) |
| Cost                | Token spend (USD) |

---

## LLM providers (from config)

| Provider   | Example model      |
| ---------- | ------------------ |
| OpenAI     | gpt-4o-mini        |
| Anthropic  | claude-sonnet-4-5  |
| Google     | gemini-2.0-flash   |
| Cohere     | command-a-03-2025  |
| Mock       | mock-local (dev)   |

---

## Notes

- Default config includes 4 major providers (OpenAI, Anthropic, Google, Cohere) and one local mock model (`mock-local`).
- Cost is estimated via configurable per-1k token pricing in `config/models.yaml`.
- Scoring computes accuracy, hallucination_risk, and safety_risk per case; lightweight in v0.1 and designed for extension.
- Run artifacts are stored as JSON in `artifacts/runs/` (configurable via `RUN_ARTIFACT_DIR`) and can be exported to CSV.
- When `DATABASE_URL` is configured, runs are also persisted to PostgreSQL (`sql/analytics_schema.sql`).
- The metrics endpoints read from stored run artifacts, so dashboards can query historical runs.

---

## Implemented features

### 1) Prompt/Dataset versioning

- `POST /api/v1/run-eval` supports `prompt_version` and `dataset_version`.
- Every run response includes `version_info`.
- Run artifacts are persisted as JSON in `artifacts/runs/` for reproducibility.

### 2) CI/CD eval gate

- `POST /api/v1/eval-gate` applies threshold checks: `min_accuracy`, `max_hallucination_risk`, optional `max_latency_ms`, optional `max_cost_usd`.
- Gate output includes `passed` plus detailed fail reasons.
- GitHub Actions: `.github/workflows/eval-gate.yml` (runs on PR and push to `main`).

### 3) Alerting (Slack/Email)

- When gate fails and `ALERT_ON_GATE_FAIL=true`, alerts can be sent to Slack webhook (`SLACK_WEBHOOK_URL`) and/or SMTP email (`ALERT_TO_EMAILS`).
- Alerting is non-blocking; eval result is still returned if alert delivery fails.

---

## Power BI analytics

**Option 1 — CSV (works now)**

```bash
python scripts/export_artifacts_csv.py
```

Or: `make export-csv`  
Load `artifacts/exports/evaluations.csv` into Power BI Desktop.

**Option 2 — PostgreSQL (recommended for scale)**

- Apply schema in `sql/analytics_schema.sql`.
- Connect Power BI to PostgreSQL and model around `runs`, `evaluations`, and `scores`.

Detailed setup: `docs/powerbi.md`.

---

## CI gate run

Runs eval against `datasets/baseline_v1.jsonl` with `mock-local` (no API keys required):

```bash
python scripts/ci_eval_gate.py
```

Or: `make gate`

---

## Docker

```bash
docker-compose up --build
```

This starts the FastAPI API on port 8000 and PostgreSQL on port 5432.  
The API automatically applies the analytics schema on startup.

---

## Roadmap

- Drift monitoring worker (weekly trend comparisons)  
- Human-in-the-loop review queue  
- BLEU/F1 scoring metrics  
- Guardrails (toxicity/PII detection)  

---

*Full design doc & portfolio report: `docs/SENTINELAI_REPORT.md`*
