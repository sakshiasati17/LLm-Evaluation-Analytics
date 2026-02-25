# SentinelAI

# LLM Evaluation & Monitoring Platform

### Production AI Reliability, Testing & Observability System

---

## 1. One-Line Summary (Layman)

**SentinelAI is like Google Analytics + unit testing for AI models.**

It automatically:

- tests answers
- measures accuracy
- checks hallucinations
- compares models
- tracks latency
- tracks token cost
- shows dashboards

So companies always know:

> *"Is our AI working correctly?"*

---

## 2. Why This Project Exists

### Real-world problem

When companies deploy LLMs:

- answers silently degrade  
- hallucinations increase  
- costs spike  
- latency increases  
- prompt updates break behavior  
- no visibility  

Unlike normal software, AI has **no monitoring or testing by default**.

### What companies need

They need:

- automated testing  
- evaluation  
- regression detection  
- observability  
- dashboards  

This is exactly what **AI infra teams** at OpenAI, Anthropic, Databricks, and Amazon build internally.

### The solution

**SentinelAI** — a full-stack platform to **evaluate + monitor + benchmark LLMs in production**.

---

## 3. System Architecture

### High-level flow

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

### Data flow

```
Users / CI Pipeline
        ↓
POST /run-eval, /compare, /eval-gate
        ↓
Evaluator Service → Model Registry → LLM APIs
        ↓
Compute: accuracy, hallucination_risk, safety_risk, latency, cost
        ↓
Persist: artifacts/runs/*.json + PostgreSQL (when configured)
        ↓
Analytics: GET /metrics, GET /model-comparison
        ↓
Web Dashboard (/dashboard) or Power BI (CSV export)
```

### Tech stack

| Layer        | Technology                          |
| ------------ | ----------------------------------- |
| API          | FastAPI                             |
| Runtime      | Python 3.11+                        |
| Adapters     | OpenAI, Anthropic, Google, Cohere   |
| Config       | YAML (`config/models.yaml`)         |
| Persistence  | JSON artifacts + PostgreSQL         |
| Analytics    | Built-in Web Dashboard + Power BI via CSV |
| CI/CD        | GitHub Actions                      |

---

## 4. Core Features

| Feature                | Description                                      |
| ---------------------- | ------------------------------------------------ |
| **Automated testing**  | Run 100–1000 test prompts automatically          |
| **Accuracy scoring**   | Measure correctness vs ground truth              |
| **Hallucination detection** | Check unsupported claims                    |
| **Latency monitoring** | Track response time (ms)                         |
| **Cost tracking**      | Monitor token spend (configurable per 1k pricing)|
| **Model benchmarking** | GPT vs Claude vs Gemini vs Cohere                |
| **Regression detection** | Catch performance drops before deploy         |
| **Dashboards**         | Built-in web dashboard at `/dashboard`           |
| **CI/CD eval gate**    | Block bad models before deploy                   |
| **Alerting**           | Slack / email on gate failure                    |
| **Prompt & dataset versioning** | Reproducible runs with version tracking  |

---

## 5. Component Breakdown

### Evaluation Engine (Python)

**Responsibilities**

- Send prompts to LLM APIs via adapters  
- Collect responses, token usage, latency  
- Compute accuracy, hallucination_risk, safety_risk  
- Store results as versioned JSON artifacts  

**Stack:** Python, Pydantic, async/await

**Example flow**

```python
start = time()
response = await adapter.complete(prompt)
latency_ms = (time() - start) * 1000
scores = compute_scores(response, ground_truth)
cost = estimate_cost(prompt_tokens, completion_tokens)
```

### Backend API (FastAPI)

| Endpoint                     | Method | Purpose                          |
| ---------------------------- | ------ | -------------------------------- |
| `/api/v1/health`             | GET    | Service health                   |
| `/api/v1/models`             | GET    | Available models from registry   |
| `/api/v1/run-eval`           | POST   | Run evaluation on one model      |
| `/api/v1/compare`            | POST   | Side-by-side comparison (multi-model) |
| `/api/v1/eval-gate`          | POST   | Run eval + apply CI gate         |
| `/api/v1/metrics`            | GET    | Aggregated run metrics           |
| `/api/v1/model-comparison`   | GET    | Model-level comparison summary   |

### LLM layer

| Provider   | Example models        |
| ---------- | --------------------- |
| OpenAI     | gpt-4o-mini           |
| Anthropic  | claude-sonnet-4-5     |
| Google     | gemini-2.0-flash      |
| Cohere     | command-a-03-2025     |
| Mock       | mock-local (dev)      |

### Database (PostgreSQL)

**Tables** (from `sql/analytics_schema.sql`)

| Table         | Key columns                                      |
| ------------- | ------------------------------------------------ |
| `runs`        | run_id, created_at, model_id, prompt_version, dataset_version, avg_accuracy, avg_hallucination_risk, avg_safety_risk, avg_latency_ms, total_cost_usd, total_cases |
| `evaluations` | run_id, case_id, question, response, latency_ms, prompt_tokens, completion_tokens, total_tokens, cost_usd |
| `scores`      | run_id, case_id, accuracy, hallucination_risk, safety_risk |

**View:** `v_run_overview` — BI-friendly run summary

### Web Analytics Dashboard

Built-in interactive dashboard at `/dashboard` with:

- KPI summary cards (total runs, best accuracy, fastest latency, total spend)
- Model comparison charts (accuracy, hallucination risk, latency, cost)
- Model scorecards with accuracy progress bars
- Run history table
- Dark/Light theme toggle
- Auto-refresh every 30 seconds

Alternatively, export CSV for Power BI:

```bash
python scripts/export_artifacts_csv.py
```

---

## 6. Metrics Computed

| Metric             | Meaning                     |
| ------------------ | --------------------------- |
| **Accuracy**       | Correctness vs ground truth |
| **Hallucination risk** | Unsupported / fabricated claims |
| **Safety risk**    | Policy / content violations |
| **Latency**        | Response time (ms)          |
| **Cost**           | Token spend (USD)           |
| **BLEU/F1** (planned) | Text similarity scores   |

---

## 7. Repository Structure

```
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
│   └── export_artifacts_csv.py  # CSV export
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

## 8. API Examples

### Run evaluation

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/run-eval" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "gpt-4o-mini",
    "prompt_version": "v1",
    "dataset_version": "v1",
    "cases": [
      {"id": "c1", "question": "What is 12 * 9?", "reference_answer": "108"},
      {"id": "c2", "question": "Capital of France?", "reference_answer": "Paris"}
    ]
  }'
```

### Compare models

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/compare" \
  -H "Content-Type: application/json" \
  -d '{
    "model_ids": ["gpt-4o-mini", "claude-sonnet-4-5"],
    "cases": [...]
  }'
```

### CI gate (block deploy on failure)

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/eval-gate" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "gpt-4o-mini",
    "cases": [...],
    "thresholds": {
      "min_accuracy": 0.85,
      "max_hallucination_risk": 0.15,
      "max_latency_ms": 3000,
      "max_cost_usd": 0.50
    }
  }'
```

---

## 9. Advanced Features

| Feature       | Description                                      |
| ------------- | ------------------------------------------------- |
| **Guardrails**| Safety risk, policy checks (extensible)           |
| **A/B testing** | Multi-model comparison via `/compare`          |
| **CI/CD gate**| Threshold-based pass/fail, blocks bad deploys     |
| **Slack/email alerts** | Notify on gate failure (`ALERT_ON_GATE_FAIL=true`) |
| **Docker + Cloud** | Dockerfile + docker-compose (PostgreSQL included) |
| **Versioning**| `prompt_version` + `dataset_version` on every run  |
| **Web Dashboard** | Interactive analytics at `/dashboard` with dark/light themes |

---

### Option 1: Web Dashboard (built-in)

Navigate to `http://127.0.0.1:8000/dashboard` for interactive analytics.

### Option 2: CSV Export for Power BI

```bash
python scripts/export_artifacts_csv.py
```

Load `artifacts/exports/evaluations.csv` into Power BI Desktop.

### Option 3: PostgreSQL (for scale)

Set `DATABASE_URL` in `.env` and run `docker-compose up`.  
The API automatically applies `sql/analytics_schema.sql` on startup and persists all runs.
Connect Power BI to PostgreSQL and model around `runs`, `evaluations`, `scores`, and `v_run_overview`.

---

## 11. Market Comparison

| Feature           | Typical chatbot | SentinelAI |
| ----------------- | --------------- | ---------- |
| Testing           | ❌               | ✅          |
| Monitoring        | ❌               | ✅          |
| Metrics           | ❌               | ✅          |
| Dashboards        | ❌               | ✅          |
| CI gate           | ❌               | ✅          |
| Multi-provider    | ❌               | ✅          |
| Production-ready  | ❌               | ✅          |

---

## 12. Use Cases

| Domain              | SentinelAI use                              |
| ------------------- | ------------------------------------------- |
| **RAG systems**     | Check hallucinations, retrieval quality      |
| **SQL agents**      | Check correctness of generated queries       |
| **Customer bots**   | Check tone, safety, policy compliance        |
| **Medical summarizers** | Check missing info, factual errors      |
| **Code assistants** | Check correctness, security                 |

---

## 13. Expected Impact

### Technical

- Fewer production failures  
- Faster mean response time  
- Reduced hallucination rate  
- Reproducible eval runs  

### Business

- Trust in AI deployments  
- Lower cost via model comparison  
- Safe, gated releases  
- Stakeholder visibility via dashboards  

---

## 14. Resume Value

This project signals:

- **AI systems engineering**  
- **ML platform / ML ops**  
- **Production reliability**  

Instead of: *“built a chatbot”*.

### Resume bullet

> **SentinelAI – LLM Reliability & Monitoring Platform**  
> Built a full-stack system to benchmark model accuracy, hallucination rate, latency, and cost using Python, FastAPI, PostgreSQL, and interactive web dashboards, with automated testing, versioned evaluations, and CI/CD evaluation gates.

---

## 15. CI/CD Eval Gate

- **Workflow:** `.github/workflows/eval-gate.yml`  
- **Script:** `python scripts/ci_eval_gate.py`  
- **Thresholds:** `min_accuracy`, `max_hallucination_risk`, `max_latency_ms`, `max_cost_usd`  
- **On failure:** Optional Slack/email alerts via `ALERT_ON_GATE_FAIL`, `SLACK_WEBHOOK_URL`, `ALERT_TO_EMAILS`  

---

## 16. Future Enhancements

- Drift monitoring worker (week-over-week comparisons)  
- Human-in-the-loop review queue  
- Auto rollback on regression  
- Governance UI  
- Real-time monitoring  
- LLM-as-judge scoring (replace heuristics)
- BLEU/F1 scoring metrics
- Guardrails (toxicity/PII detection)

---

## 17. Conclusion

**SentinelAI** transforms:

> ❌ AI demos  
> into  
> ✅ Reliable production AI systems  

It demonstrates:

- Backend engineering  
- SQL and analytics  
- Python services  
- Monitoring and observability  
- Infrastructure thinking  
- Business dashboards  

Which is what **AI/ML platform engineers build in industry**.

---

*Docs: `docs/architecture.md` | `docs/powerbi.md` | `docs/SENTINELAI_REPORT.md`*
