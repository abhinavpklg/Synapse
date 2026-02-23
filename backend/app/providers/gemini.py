"""Google Gemini LLM provider implementation.

Supports Gemini 2.5 Pro, 2.0 Flash, 2.5 Flash.
Uses the Gemini REST API with streaming via generateContent.

API docs: https://ai.google.dev/api/generate-content
"""

import json
from collections.abc import AsyncGenerator

import httpx

from app.core.exceptions import ProviderAuthError, ProviderError, ProviderRateLimitError
from app.core.logging import get_logger
from app.providers.base import BaseLLMProvider, LLMChunk, LLMConfig, LLMMessage, LLMResponse

logger = get_logger(__name__)

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API provider.

    Key differences from OpenAI:
    - Model name is in the URL path, not the request body
    - API key is passed as a query parameter, not a header
    - Messages use "parts" instead of "content" string
    - System instruction is a separate top-level field
    - Streaming returns JSON objects with "candidates" array
    """

    def __init__(self, api_key: str, base_url: str | None = None) -> None:
        self.api_key = api_key
        self.base_url = base_url or GEMINI_BASE_URL

    def _build_url(self, model: str, *, stream: bool = False) -> str:
        """Build the API URL with model and optional streaming suffix."""
        action = "streamGenerateContent" if stream else "generateContent"
        return f"{self.base_url}/{model}:{action}?key={self.api_key}"

    def _build_payload(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> dict:
        """Build the Gemini request payload.

        Extracts system prompt to systemInstruction field.
        Converts messages to Gemini's contents/parts format.
        """
        system_prompt = ""
        contents = []

        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                # Gemini uses "user" and "model" as roles
                role = "model" if msg.role == "assistant" else "user"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.content}],
                })

        payload: dict = {
            "contents": contents,
            "generationConfig": {
                "temperature": config.temperature,
                "maxOutputTokens": config.max_tokens,
            },
        }

        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}],
            }

        return payload

    async def stream(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> AsyncGenerator[LLMChunk, None]:
        """Stream response tokens from Gemini.

        Gemini streaming returns newline-delimited JSON objects,
        each containing a candidates array with text parts.
        The response includes &alt=sse for SSE format.
        """
        url = self._build_url(config.model, stream=True) + "&alt=sse"
        payload = self._build_payload(messages, config)
        full_content = ""
        tokens_used = 0

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                async with client.stream(
                    "POST",
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status_code == 401 or response.status_code == 403:
                        raise ProviderAuthError("gemini")
                    if response.status_code == 429:
                        raise ProviderRateLimitError("gemini")
                    if response.status_code != 200:
                        body = await response.aread()
                        raise ProviderError(
                            "gemini", f"HTTP {response.status_code}: {body.decode()}"
                        )

                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data = line[6:]

                        try:
                            chunk = json.loads(data)
                            candidates = chunk.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                for part in parts:
                                    text = part.get("text", "")
                                    if text:
                                        full_content += text
                                        yield LLMChunk(content=text)

                            # Extract token usage from usageMetadata
                            usage = chunk.get("usageMetadata", {})
                            total = usage.get("totalTokenCount", 0)
                            if total:
                                tokens_used = total

                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

            except httpx.TimeoutException as exc:
                raise ProviderError("gemini", f"Request timed out: {exc}") from exc
            except (ProviderAuthError, ProviderRateLimitError, ProviderError):
                raise
            except Exception as exc:
                raise ProviderError("gemini", f"Unexpected error: {exc}") from exc

        yield LLMChunk(content="", is_final=True, tokens_used=tokens_used)
        logger.info(
            "gemini_stream_complete",
            model=config.model,
            tokens=tokens_used,
            content_length=len(full_content),
        )

    async def complete(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> LLMResponse:
        url = self._build_url(config.model, stream=False)
        payload = self._build_payload(messages, config)

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                if response.status_code in (401, 403):
                    raise ProviderAuthError("gemini")
                if response.status_code == 429:
                    raise ProviderRateLimitError("gemini")
                if response.status_code != 200:
                    raise ProviderError(
                        "gemini", f"HTTP {response.status_code}: {response.text}"
                    )

                data = response.json()
                candidates = data.get("candidates", [])
                content = ""
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    content = "".join(p.get("text", "") for p in parts)

                usage = data.get("usageMetadata", {})
                tokens_used = usage.get("totalTokenCount", 0)

                return LLMResponse(
                    content=content,
                    tokens_used=tokens_used,
                    model=config.model,
                )
            except (ProviderAuthError, ProviderRateLimitError, ProviderError):
                raise
            except Exception as exc:
                raise ProviderError("gemini", f"Unexpected error: {exc}") from exc

    def validate_api_key(self, api_key: str) -> bool:
        return api_key.startswith("AI") and len(api_key) > 20