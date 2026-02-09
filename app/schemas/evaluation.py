from typing import Any

from pydantic import BaseModel, Field


class EvaluationCase(BaseModel):
    id: str = Field(description="Unique case identifier within a run.")
    question: str = Field(description="Prompt/question to send to the model.")
    reference_answer: str | None = Field(default=None, description="Ground-truth answer if available.")
    metadata: dict[str, Any] = Field(default_factory=dict)


class RunEvalRequest(BaseModel):
    model_id: str | None = Field(default=None, description="Model ID from config/models.yaml")
    cases: list[EvaluationCase]
    system_prompt: str | None = None
    prompt_version: str = Field(default="v1", description="Prompt bundle version identifier.")
    dataset_version: str = Field(default="v1", description="Dataset version identifier.")
    prompt_template: str = Field(
        default="{question}",
        description="Template used to build final prompt. Must include {question}.",
    )
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int = Field(default=512, ge=1, le=4096)


class CaseScore(BaseModel):
    accuracy: float = Field(ge=0.0, le=1.0)
    hallucination_risk: float = Field(ge=0.0, le=1.0)
    safety_risk: float = Field(ge=0.0, le=1.0)


class CaseResult(BaseModel):
    case_id: str
    question: str
    response: str
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    scores: CaseScore


class RunSummary(BaseModel):
    avg_accuracy: float
    avg_hallucination_risk: float
    avg_safety_risk: float
    avg_latency_ms: float
    total_cost_usd: float
    total_cases: int


class VersionInfo(BaseModel):
    prompt_version: str
    dataset_version: str


class RunEvalResponse(BaseModel):
    run_id: str
    created_at: str | None = None
    model_id: str
    version_info: VersionInfo
    summary: RunSummary
    results: list[CaseResult]


class CompareRequest(BaseModel):
    model_ids: list[str]
    cases: list[EvaluationCase]
    system_prompt: str | None = None
    prompt_version: str = Field(default="v1")
    dataset_version: str = Field(default="v1")
    prompt_template: str = Field(default="{question}")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int = Field(default=512, ge=1, le=4096)


class CompareResponse(BaseModel):
    runs: list[RunEvalResponse]


class EvalGateThresholds(BaseModel):
    min_accuracy: float = Field(default=0.75, ge=0.0, le=1.0)
    max_hallucination_risk: float = Field(default=0.30, ge=0.0, le=1.0)
    max_latency_ms: float | None = Field(default=None, ge=0.0)
    max_cost_usd: float | None = Field(default=None, ge=0.0)


class EvalGateRequest(RunEvalRequest):
    thresholds: EvalGateThresholds = Field(default_factory=EvalGateThresholds)


class EvalGateResponse(BaseModel):
    passed: bool
    reasons: list[str]
    run: RunEvalResponse


class RunMetricItem(BaseModel):
    run_id: str
    created_at: str
    model_id: str
    prompt_version: str
    dataset_version: str
    avg_accuracy: float
    avg_hallucination_risk: float
    avg_safety_risk: float
    avg_latency_ms: float
    total_cost_usd: float
    total_cases: int


class MetricsSummary(BaseModel):
    avg_accuracy: float
    avg_hallucination_risk: float
    avg_safety_risk: float
    avg_latency_ms: float
    total_cost_usd: float
    total_cases: int


class MetricsResponse(BaseModel):
    total_runs: int
    summary: MetricsSummary
    items: list[RunMetricItem]


class ModelComparisonItem(BaseModel):
    model_id: str
    runs: int
    avg_accuracy: float
    avg_hallucination_risk: float
    avg_safety_risk: float
    avg_latency_ms: float
    total_cost_usd: float
    total_cases: int


class ModelComparisonResponse(BaseModel):
    total_models: int
    models: list[ModelComparisonItem]
