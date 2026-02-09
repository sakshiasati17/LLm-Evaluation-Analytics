from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Provider(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    COHERE = "cohere"
    MOCK = "mock"


@dataclass(slots=True)
class Pricing:
    prompt_per_1k: float = 0.0
    completion_per_1k: float = 0.0


@dataclass(slots=True)
class ModelConfig:
    id: str
    provider: Provider
    api_model: str
    enabled: bool = True
    pricing: Pricing = field(default_factory=Pricing)


@dataclass(slots=True)
class GenerationResponse:
    text: str
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    raw: dict[str, Any]

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class BaseAdapter(ABC):
    def __init__(self, model: ModelConfig, api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> GenerationResponse:
        """Generate a model response."""
