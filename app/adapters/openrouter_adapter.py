import time

import httpx

from app.adapters.base import BaseAdapter, GenerationResponse


class OpenRouterAdapter(BaseAdapter):
    """Adapter for OpenRouter — a unified API gateway to 200+ LLM models.

    Uses the OpenAI-compatible chat completions endpoint at
    https://openrouter.ai/api/v1/chat/completions
    """

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> GenerationResponse:
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is not configured.")

        start = time.perf_counter()
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model.api_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/sakshiasati17/LLm-Evaluation-Analytics",
            "X-Title": "SentinelAI LLM Evaluation Platform",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers,
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise ValueError(
                    f"OpenRouter API error {exc.response.status_code}: {exc.response.text}"
                ) from exc
            data = response.json()

        latency_ms = (time.perf_counter() - start) * 1000
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})

        return GenerationResponse(
            text=text or "",
            latency_ms=latency_ms,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            raw=data,
        )
