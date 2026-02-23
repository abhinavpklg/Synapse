"""OpenAI LLM provider implementation.

Supports GPT-4o, GPT-4o-mini, GPT-4-turbo, o1, o3-mini.
Uses httpx for async streaming via the OpenAI chat completions API.

API docs: https://platform.openai.com/docs/api-reference/chat
"""

import json
from collections.abc import AsyncGenerator

import httpx

from app.core.exceptions import ProviderAuthError, ProviderError, ProviderRateLimitError
from app.core.logging import get_logger
from app.providers.base import BaseLLMProvider, LLMChunk, LLMConfig, LLMMessage, LLMResponse

logger = get_logger(__name__)

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider.

    Implements streaming and non-streaming chat completions
    using the OpenAI-compatible API format.
    """

    def __init__(self, api_key: str, base_url: str | None = None) -> None:
        """Initialize with API key and optional custom base URL.

        Args:
            api_key: OpenAI API key.
            base_url: Custom endpoint URL (for Azure, proxies, etc.).
        """
        self.api_key = api_key
        self.base_url = (base_url or OPENAI_API_URL).rstrip("/")
        if not self.base_url.endswith("/chat/completions"):
            self.base_url = f"{self.base_url}/chat/completions"

    def _build_headers(self) -> dict[str, str]:
        """Build HTTP headers for the API request."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_payload(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
        *,
        stream: bool = False,
    ) -> dict:
        """Build the request payload for the chat completions API."""
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
        """Stream response tokens from OpenAI.

        Uses Server-Sent Events (SSE) format from OpenAI's streaming API.
        Each line starting with "data: " contains a JSON chunk.
        The stream ends with "data: [DONE]".
        """
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
                        raise ProviderAuthError("openai")
                    if response.status_code == 429:
                        raise ProviderRateLimitError("openai")
                    if response.status_code != 200:
                        body = await response.aread()
                        raise ProviderError("openai", f"HTTP {response.status_code}: {body.decode()}")

                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data = line[6:]  # Strip "data: " prefix
                        if data == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data)
                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                full_content += content
                                yield LLMChunk(content=content)

                            # Check for usage in the final chunk
                            usage = chunk.get("usage")
                            if usage:
                                tokens_used = usage.get("total_tokens", 0)
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

            except httpx.TimeoutException as exc:
                raise ProviderError("openai", f"Request timed out: {exc}") from exc
            except (ProviderAuthError, ProviderRateLimitError, ProviderError):
                raise
            except Exception as exc:
                raise ProviderError("openai", f"Unexpected error: {exc}") from exc

        # Final chunk with complete content and token usage
        yield LLMChunk(content="", is_final=True, tokens_used=tokens_used)
        logger.info(
            "openai_stream_complete",
            model=config.model,
            tokens=tokens_used,
            content_length=len(full_content),
        )

    async def complete(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> LLMResponse:
        """Get a complete response from OpenAI (non-streaming)."""
        payload = self._build_payload(messages, config, stream=False)

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    self.base_url,
                    headers=self._build_headers(),
                    json=payload,
                )
                if response.status_code == 401:
                    raise ProviderAuthError("openai")
                if response.status_code == 429:
                    raise ProviderRateLimitError("openai")
                if response.status_code != 200:
                    raise ProviderError("openai", f"HTTP {response.status_code}: {response.text}")

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
                raise ProviderError("openai", f"Unexpected error: {exc}") from exc

    def validate_api_key(self, api_key: str) -> bool:
        """Check if the key looks like an OpenAI API key."""
        return api_key.startswith("sk-") and len(api_key) > 20