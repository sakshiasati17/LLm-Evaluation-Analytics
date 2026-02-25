from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="LLM Evaluation & Monitoring Platform", alias="APP_NAME")
    app_env: str = Field(default="dev", alias="APP_ENV")
    models_config_path: str = Field(default="config/models.yaml", alias="MODELS_CONFIG_PATH")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")
    cohere_api_key: str | None = Field(default=None, alias="COHERE_API_KEY")
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")

    database_url: str | None = Field(default=None, alias="DATABASE_URL")

    run_artifact_dir: str = Field(default="artifacts/runs", alias="RUN_ARTIFACT_DIR")

    alert_on_gate_fail: bool = Field(default=False, alias="ALERT_ON_GATE_FAIL")
    slack_webhook_url: str | None = Field(default=None, alias="SLACK_WEBHOOK_URL")

    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_username: str | None = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from_email: str | None = Field(default=None, alias="SMTP_FROM_EMAIL")
    alert_to_emails: str | None = Field(default=None, alias="ALERT_TO_EMAILS")

    @property
    def models_path(self) -> Path:
        return Path(self.models_config_path)

    @property
    def tasks_path(self) -> Path:
        return Path("config/tasks.yaml")

    @property
    def benchmarks_dir(self) -> Path:
        return Path("datasets/benchmarks")

    @property
    def run_artifacts_path(self) -> Path:
        return Path(self.run_artifact_dir)

    @property
    def alert_recipient_list(self) -> list[str]:
        if not self.alert_to_emails:
            return []
        return [item.strip() for item in self.alert_to_emails.split(",") if item.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
