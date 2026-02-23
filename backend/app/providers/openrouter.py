"""OpenRouter LLM provider implementation.

OpenRouter is a unified API gateway that provides access to
hundreds of models (OpenAI, Anthropic, Meta, Mistral, etc.)
through a single OpenAI-compatible endpoint.

API docs: https://openrouter.ai/docs
"""

import json
from collections.abc import AsyncGenerator

import httpx

from app.core.exceptions import ProviderAuthError, ProviderError, ProviderRateLimitError
from app.core.logging import get_logger
from app.providers.base import BaseLLMProvider, LLMChunk, LLMConfig, LLMMessage, LLMResponse

logger = get_logger(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter API provider (OpenAI-compatible).

    Key differences from plain OpenAI:
    - Requires HTTP-Referer and X-Title headers for attribution
    - Model names use org/model format (e.g., "google/gemini-2.0-flash-exp:free")
    - Some models are free, others are paid per-token
    """

    def __init__(self, api_key: str, base_url: str | None = None) -> None:
        self.api_key = api_key
        self.base_url = base_url or OPENROUTER_API_URL

    def _build_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/synapse-ai",
            "X-Title": "Synapse",
        }

    def _build_payload(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
        *,
        stream: bool = False,
    ) -> dict:
        return {
            "model": config.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "stream": stream,
        }

    async def stream(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> AsyncGenerator[LLMChunk, None]:
        """Stream response tokens from OpenRouter (OpenAI SSE format)."""
        payload = self._build_payload(messages, config, stream=True)
        full_content = ""
        tokens_used = 0

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                async with client.stream(
                    "POST",
                    self.base_url,
                    headers=self._build_headers(),
                    json=payload,
                ) as response:
                    if response.status_code == 401:
                        raise ProviderAuthError("openrouter")
                    if response.status_code == 429:
                        raise ProviderRateLimitError("openrouter")
                    if response.status_code != 200:
                        body = await response.aread()
                        raise ProviderError(
                            "openrouter", f"HTTP {response.status_code}: {body.decode()}"
                        )

                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data = line[6:]
                        if data == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data)
                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                full_content += content
                                yield LLMChunk(content=content)

                            usage = chunk.get("usage")
                            if usage:
                                tokens_used = usage.get("total_tokens", 0)
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

            except httpx.TimeoutException as exc:
                raise ProviderError("openrouter", f"Request timed out: {exc}") from exc
            except (ProviderAuthError, ProviderRateLimitError, ProviderError):
                raise
            except Exception as exc:
                raise ProviderError("openrouter", f"Unexpected error: {exc}") from exc

        yield LLMChunk(content="", is_final=True, tokens_used=tokens_used)
        logger.info(
            "openrouter_stream_complete",
            model=config.model,
            tokens=tokens_used,
            content_length=len(full_content),
        )

    async def complete(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> LLMResponse:
        payload = self._build_payload(messages, config, stream=False)

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    self.base_url,
                    headers=self._build_headers(),
                    json=payload,
                )
                if response.status_code == 401:
                    raise ProviderAuthError("openrouter")
                if response.status_code == 429:
                    raise ProviderRateLimitError("openrouter")
                if response.status_code != 200:
                    raise ProviderError(
                        "openrouter", f"HTTP {response.status_code}: {response.text}"
                    )

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                tokens_used = data.get("usage", {}).get("total_tokens", 0)

                return LLMResponse(
                    content=content,
                    tokens_used=tokens_used,
                    model=config.model,
                )
            except (ProviderAuthError, ProviderRateLimitError, ProviderError):
                raise
            except Exception as exc:
                raise ProviderError("openrouter", f"Unexpected error: {exc}") from exc

    def validate_api_key(self, api_key: str) -> bool:
        return api_key.startswith("sk-or-") and len(api_key) > 20