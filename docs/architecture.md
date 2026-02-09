# Architecture

## High-level flow

1. Client submits evaluation cases to FastAPI.
2. Evaluation service loads model adapter from registry (`config/models.yaml`).
3. Adapter sends requests to target provider (OpenAI/Anthropic/Google/Cohere).
4. Service computes score heuristics and cost estimates.
5. Eval gate optionally enforces thresholds (CI/CD policy).
6. Run metadata and results are stored as versioned JSON artifacts.
7. Optional alerts are sent on gate failure.
8. Analytics is exposed to Power BI via CSV export or PostgreSQL schema.

## Core boundaries

- `app/api`: HTTP contracts and validation
- `app/services`: evaluation orchestration and scoring
- `app/adapters`: provider-specific IO
- `config/models.yaml`: model catalog + pricing metadata
- `datasets/*`: versioned benchmark datasets
- `.github/workflows/eval-gate.yml`: release quality gate
- `sql/analytics_schema.sql`: BI-ready relational schema
- `docs/powerbi.md`: dashboard setup and visuals

## Extension points

- Replace heuristics with LLM-as-judge or custom rubric scorers
- Persist run outputs into PostgreSQL
- Add drift worker to compare week-over-week baseline metrics
- Add persistent run store in PostgreSQL
