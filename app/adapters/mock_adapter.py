import time

from app.adapters.base import BaseAdapter, GenerationResponse


class MockAdapter(BaseAdapter):
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> GenerationResponse:
        start = time.perf_counter()
        content = f"[mock:{self.model.id}] {prompt[: min(len(prompt), max_tokens)]}"
        latency_ms = (time.perf_counter() - start) * 1000
        prompt_tokens = max(1, len(prompt.split()))
        completion_tokens = max(1, len(content.split()))

        return GenerationResponse(
            text=content,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            raw={"provider": "mock"},
        )
