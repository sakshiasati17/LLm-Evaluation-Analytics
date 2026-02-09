from app.schemas.evaluation import EvalGateResponse, EvalGateThresholds, RunEvalResponse


class EvalGateService:
    def evaluate(self, run: RunEvalResponse, thresholds: EvalGateThresholds) -> EvalGateResponse:
        reasons: list[str] = []
        summary = run.summary

        if summary.avg_accuracy < thresholds.min_accuracy:
            reasons.append(
                f"avg_accuracy {summary.avg_accuracy:.3f} is below min_accuracy {thresholds.min_accuracy:.3f}"
            )

        if summary.avg_hallucination_risk > thresholds.max_hallucination_risk:
            reasons.append(
                "avg_hallucination_risk "
                f"{summary.avg_hallucination_risk:.3f} exceeds max_hallucination_risk "
                f"{thresholds.max_hallucination_risk:.3f}"
            )

        if thresholds.max_latency_ms is not None and summary.avg_latency_ms > thresholds.max_latency_ms:
            reasons.append(
                f"avg_latency_ms {summary.avg_latency_ms:.2f} exceeds max_latency_ms {thresholds.max_latency_ms:.2f}"
            )

        if thresholds.max_cost_usd is not None and summary.total_cost_usd > thresholds.max_cost_usd:
            reasons.append(
                f"total_cost_usd {summary.total_cost_usd:.6f} exceeds max_cost_usd {thresholds.max_cost_usd:.6f}"
            )

        return EvalGateResponse(passed=not reasons, reasons=reasons, run=run)
