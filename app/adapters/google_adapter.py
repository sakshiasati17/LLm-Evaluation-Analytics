import time

import httpx

from app.adapters.base import BaseAdapter, GenerationResponse


class GoogleAdapter(BaseAdapter):
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> GenerationResponse:
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is not configured.")

        start = time.perf_counter()
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        payload = {
            "contents": [{"role": "user", "parts": [{"text": full_prompt}]}],
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
        }
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model.api_model}:generateContent?key={self.api_key}"
        )

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, json=payload)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise ValueError(
                    f"Google API error {exc.response.status_code}: {exc.response.text}"
                ) from exc
            data = response.json()

        latency_ms = (time.perf_counter() - start) * 1000
        candidates = data.get("candidates", [])
        text = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            # Filter out "thought" parts (gemini-2.5-pro thinking mode)
            text_parts = [
                part.get("text", "")
                for part in parts
                if "thought" not in part and part.get("text")
            ]
            # Fallback: if no non-thought parts, grab any text
            if not text_parts:
                text_parts = [part.get("text", "") for part in parts if part.get("text")]
            text = "".join(text_parts)

        usage = data.get("usageMetadata", {})
        return GenerationResponse(
            text=text,
            latency_ms=latency_ms,
            prompt_tokens=usage.get("promptTokenCount", 0),
            completion_tokens=usage.get("candidatesTokenCount", usage.get("totalTokenCount", 0)),
            raw=data,
        )
