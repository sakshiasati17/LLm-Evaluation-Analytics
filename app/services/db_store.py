"""PostgreSQL persistence for evaluation runs.

Writes run summaries and per-case results to PostgreSQL when DATABASE_URL
is configured.  Falls back gracefully (logs a warning) when the database
is unavailable so the API never crashes due to DB issues.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import psycopg

if TYPE_CHECKING:
    from app.schemas.evaluation import RunEvalResponse

logger = logging.getLogger(__name__)


class DBStore:
    """Thin sync writer – called once per run after JSON persistence."""

    def __init__(self, database_url: str | None) -> None:
        self._dsn = database_url
        if self._dsn and self._dsn.startswith("postgresql+psycopg://"):
            # Normalise SQLAlchemy-style DSN → plain libpq-style
            self._dsn = self._dsn.replace("postgresql+psycopg://", "postgresql://", 1)

    @property
    def enabled(self) -> bool:
        return bool(self._dsn)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------
    def save(self, run: RunEvalResponse) -> None:
        """Persist run + evaluations + scores to PostgreSQL."""
        if not self.enabled:
            return
        try:
            with psycopg.connect(self._dsn) as conn:  # type: ignore[arg-type]
                self._insert_run(conn, run)
                self._insert_evaluations(conn, run)
                self._insert_scores(conn, run)
                conn.commit()
            logger.info("DB: saved run %s (%s)", run.run_id, run.model_id)
        except Exception:
            logger.warning("DB: failed to save run %s – skipping", run.run_id, exc_info=True)

    def init_schema(self) -> None:
        """Apply schema idempotently (CREATE IF NOT EXISTS)."""
        if not self.enabled:
            return
        try:
            from pathlib import Path

            sql_path = Path(__file__).resolve().parents[2] / "sql" / "analytics_schema.sql"
            schema_sql = sql_path.read_text(encoding="utf-8")
            with psycopg.connect(self._dsn) as conn:  # type: ignore[arg-type]
                conn.execute(schema_sql)
                conn.commit()
            logger.info("DB: schema applied successfully")
        except Exception:
            logger.warning("DB: schema init failed – skipping", exc_info=True)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    @staticmethod
    def _insert_run(conn: psycopg.Connection, run: RunEvalResponse) -> None:
        conn.execute(
            """
            INSERT INTO runs (run_id, created_at, model_id, prompt_version,
                              dataset_version, avg_accuracy, avg_hallucination_risk,
                              avg_safety_risk, avg_latency_ms, total_cost_usd,
                              total_cases)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (run_id) DO NOTHING
            """,
            (
                str(run.run_id),
                run.created_at,
                run.model_id,
                run.version_info.prompt_version if run.version_info else "v1",
                run.version_info.dataset_version if run.version_info else "v1",
                run.summary.avg_accuracy,
                run.summary.avg_hallucination_risk,
                run.summary.avg_safety_risk,
                run.summary.avg_latency_ms,
                run.summary.total_cost_usd,
                run.summary.total_cases,
            ),
        )

    @staticmethod
    def _insert_evaluations(conn: psycopg.Connection, run: RunEvalResponse) -> None:
        for r in run.results:
            conn.execute(
                """
                INSERT INTO evaluations (run_id, case_id, question, response,
                                         latency_ms, prompt_tokens,
                                         completion_tokens, total_tokens, cost_usd)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(run.run_id),
                    r.case_id,
                    r.question,
                    r.response,
                    r.latency_ms,
                    r.token_usage.get("prompt_tokens", 0) if r.token_usage else 0,
                    r.token_usage.get("completion_tokens", 0) if r.token_usage else 0,
                    r.token_usage.get("total_tokens", 0) if r.token_usage else 0,
                    r.cost_usd,
                ),
            )

    @staticmethod
    def _insert_scores(conn: psycopg.Connection, run: RunEvalResponse) -> None:
        for r in run.results:
            conn.execute(
                """
                INSERT INTO scores (run_id, case_id, accuracy,
                                    hallucination_risk, safety_risk)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    str(run.run_id),
                    r.case_id,
                    r.scores.accuracy,
                    r.scores.hallucination_risk,
                    r.scores.safety_risk,
                ),
            )
