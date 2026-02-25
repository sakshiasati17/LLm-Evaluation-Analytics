from pathlib import Path

import yaml

from app.adapters.anthropic_adapter import AnthropicAdapter
from app.adapters.base import BaseAdapter, ModelConfig, Pricing, Provider
from app.adapters.cohere_adapter import CohereAdapter
from app.adapters.google_adapter import GoogleAdapter
from app.adapters.mock_adapter import MockAdapter
from app.adapters.openai_adapter import OpenAIAdapter
from app.adapters.openrouter_adapter import OpenRouterAdapter
from app.core.config import Settings


class ModelRegistry:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.default_model_id: str = ""
        self.models: dict[str, ModelConfig] = {}
        self._load_from_yaml(settings.models_path)

    def _load_from_yaml(self, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"Model config not found: {path}")

        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.default_model_id = payload["default_model"]

        for item in payload.get("models", []):
            provider = Provider(item["provider"])
            pricing_cfg = item.get("pricing", {})
            pricing = Pricing(
                prompt_per_1k=float(pricing_cfg.get("prompt_per_1k", 0.0)),
                completion_per_1k=float(pricing_cfg.get("completion_per_1k", 0.0)),
            )
            model = ModelConfig(
                id=item["id"],
                provider=provider,
                api_model=item["api_model"],
                enabled=bool(item.get("enabled", True)),
                pricing=pricing,
            )
            self.models[model.id] = model

        if self.default_model_id not in self.models:
            raise ValueError("default_model must exist in models list.")

    def list_models(self) -> list[dict[str, object]]:
        return [
            {
                "id": model.id,
                "provider": model.provider,
                "api_model": model.api_model,
                "enabled": model.enabled,
                "pricing": {
                    "prompt_per_1k": model.pricing.prompt_per_1k,
                    "completion_per_1k": model.pricing.completion_per_1k,
                },
            }
            for model in self.models.values()
        ]

    def get_default_model_id(self) -> str:
        return self.default_model_id

    def get_model(self, model_id: str) -> ModelConfig:
        if model_id not in self.models:
            raise KeyError(f"Unknown model_id: {model_id}")
        model = self.models[model_id]
        if not model.enabled:
            raise ValueError(f"Model is disabled: {model_id}")
        return model

    def get_adapter(self, model_id: str) -> BaseAdapter:
        model = self.get_model(model_id)
        if model.provider == Provider.OPENAI:
            return OpenAIAdapter(model=model, api_key=self.settings.openai_api_key)
        if model.provider == Provider.ANTHROPIC:
            return AnthropicAdapter(model=model, api_key=self.settings.anthropic_api_key)
        if model.provider == Provider.GOOGLE:
            return GoogleAdapter(model=model, api_key=self.settings.google_api_key)
        if model.provider == Provider.COHERE:
            return CohereAdapter(model=model, api_key=self.settings.cohere_api_key)
        if model.provider == Provider.OPENROUTER:
            return OpenRouterAdapter(model=model, api_key=self.settings.openrouter_api_key)
        if model.provider == Provider.MOCK:
            return MockAdapter(model=model)
        raise ValueError(f"Unsupported provider: {model.provider}")
