import time

import httpx

from app.adapters.base import BaseAdapter, GenerationResponse


class CohereAdapter(BaseAdapter):
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> GenerationResponse:
        if not self.api_key:
            raise ValueError("COHERE_API_KEY is not configured.")

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

        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.cohere.com/v2/chat",
                json=payload,
                headers=headers,
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise ValueError(
                    f"Cohere API error {exc.response.status_code}: {exc.response.text}"
                ) from exc
            data = response.json()

        latency_ms = (time.perf_counter() - start) * 1000
        message = data.get("message", {})
        content = message.get("content", [])
        text_parts = [item.get("text", "") for item in content if item.get("type") == "text"]
        usage = data.get("usage", {})
        input_tokens = usage.get("tokens", {}).get("input_tokens", 0)
        output_tokens = usage.get("tokens", {}).get("output_tokens", 0)

        return GenerationResponse(
            text="".join(text_parts),
            latency_ms=latency_ms,
            prompt_tokens=input_tokens,
            completion_tokens=output_tokens,
            raw=data,
        )
