import time

from anthropic import AsyncAnthropic

from app.adapters.base import BaseAdapter, GenerationResponse


class AnthropicAdapter(BaseAdapter):
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> GenerationResponse:
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is not configured.")

        start = time.perf_counter()

        client = AsyncAnthropic(api_key=self.api_key)

        kwargs: dict[str, object] = {
            "model": self.model.api_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        try:
            message = await client.messages.create(**kwargs)
        except Exception as exc:
            raise ValueError(f"Anthropic API error: {exc}") from exc

        latency_ms = (time.perf_counter() - start) * 1000

        text_chunks = [
            block.text for block in message.content if hasattr(block, "text") and block.text
        ]
        text = "".join(text_chunks) if text_chunks else ""

        usage = message.usage or {}
        prompt_tokens = getattr(usage, "input_tokens", 0) or 0
        completion_tokens = getattr(usage, "output_tokens", 0) or 0

        raw: dict = {}
        if hasattr(message, "model_dump"):
            raw = message.model_dump()
        else:
            raw = {
                "content": [{"type": "text", "text": t} for t in text_chunks] if text_chunks else [],
                "usage": {"input_tokens": prompt_tokens, "output_tokens": completion_tokens},
            }

        return GenerationResponse(
            text=text,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            raw=raw,
        )
