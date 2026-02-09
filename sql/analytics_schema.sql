-- Analytics schema for LLM Evaluation & Monitoring Platform
-- Designed for Power BI-friendly querying.

CREATE TABLE IF NOT EXISTS runs (
    run_id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    model_id TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    dataset_version TEXT NOT NULL,
    avg_accuracy NUMERIC(5,4) NOT NULL,
    avg_hallucination_risk NUMERIC(5,4) NOT NULL,
    avg_safety_risk NUMERIC(5,4) NOT NULL,
    avg_latency_ms NUMERIC(10,2) NOT NULL,
    total_cost_usd NUMERIC(12,6) NOT NULL,
    total_cases INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS evaluations (
    id BIGSERIAL PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    case_id TEXT NOT NULL,
    question TEXT NOT NULL,
    response TEXT NOT NULL,
    latency_ms NUMERIC(10,2) NOT NULL,
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    cost_usd NUMERIC(12,6) NOT NULL
);

CREATE TABLE IF NOT EXISTS scores (
    id BIGSERIAL PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    case_id TEXT NOT NULL,
    accuracy NUMERIC(5,4) NOT NULL,
    hallucination_risk NUMERIC(5,4) NOT NULL,
    safety_risk NUMERIC(5,4) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_runs_created_at ON runs(created_at);
CREATE INDEX IF NOT EXISTS idx_runs_model_id ON runs(model_id);
CREATE INDEX IF NOT EXISTS idx_runs_prompt_dataset ON runs(prompt_version, dataset_version);
CREATE INDEX IF NOT EXISTS idx_evaluations_run_id ON evaluations(run_id);
CREATE INDEX IF NOT EXISTS idx_scores_run_id ON scores(run_id);

CREATE OR REPLACE VIEW v_run_overview AS
SELECT
    r.run_id,
    r.created_at,
    r.model_id,
    r.prompt_version,
    r.dataset_version,
    r.avg_accuracy,
    r.avg_hallucination_risk,
    r.avg_safety_risk,
    r.avg_latency_ms,
    r.total_cost_usd,
    r.total_cases
FROM runs r;
