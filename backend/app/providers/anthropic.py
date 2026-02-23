"""Anthropic (Claude) LLM provider implementation.

Supports Claude Sonnet, Opus, and Haiku models.
Uses httpx for async streaming via the Anthropic messages API.

API docs: https://docs.anthropic.com/en/api/messages
"""

import json
from collections.abc import AsyncGenerator

import httpx

from app.core.exceptions import ProviderAuthError, ProviderError, ProviderRateLimitError
from app.core.logging import get_logger
from app.providers.base import BaseLLMProvider, LLMChunk, LLMConfig, LLMMessage, LLMResponse

logger = get_logger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API provider.

    Note: Anthropic uses a different API format than OpenAI:
    - System message is a top-level field, not in the messages array
    - Streaming uses Server-Sent Events with different event types
    - Auth uses x-api-key header, not Bearer token
    """

    def __init__(self, api_key: str, base_url: str | None = None) -> None:
        self.api_key = api_key
        self.base_url = base_url or ANTHROPIC_API_URL

    def _build_headers(self) -> dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "Content-Type": "application/json",
        }

    def _build_payload(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
        *,
        stream: bool = False,
    ) -> dict:
        """Build payload, extracting system message to top level.

        Anthropic requires the system prompt as a separate field,
        not as a message with role "system".
        """
        system_prompt = ""
        api_messages = []

        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                api_messages.append({"role": msg.role, "content": msg.content})

        payload: dict = {
            "model": config.model,
            "messages": api_messages,
            "max_tokens": config.max_tokens,
            "stream": stream,
        }

        if system_prompt:
            payload["system"] = system_prompt

        # Anthropic doesn't support temperature for all models
        if config.temperature is not None:
            payload["temperature"] = config.temperature

        return payload

    async def stream(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> AsyncGenerator[LLMChunk, None]:
        """Stream response tokens from Anthropic.

        Anthropic's streaming format uses SSE with typed events:
        - message_start: contains the message metadata
        - content_block_delta: contains text chunks
        - message_delta: contains stop reason and usage
        - message_stop: stream is complete
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
                        raise ProviderAuthError("anthropic")
                    if response.status_code == 429:
                        raise ProviderRateLimitError("anthropic")
                    if response.status_code != 200:
                        body = await response.aread()
                        raise ProviderError(
                            "anthropic", f"HTTP {response.status_code}: {body.decode()}"
                        )

                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data = line[6:]

                        try:
                            event = json.loads(data)
                            event_type = event.get("type", "")

                            if event_type == "content_block_delta":
                                delta = event.get("delta", {})
                                text = delta.get("text", "")
                                if text:
                                    full_content += text
                                    yield LLMChunk(content=text)

                            elif event_type == "message_start":
                                # Extract input token count from initial message
                                usage = event.get("message", {}).get("usage", {})
                                tokens_used += usage.get("input_tokens", 0)

                            elif event_type == "message_delta":
                                # Extract output token count from final delta
                                usage = event.get("usage", {})
                                tokens_used += usage.get("output_tokens", 0)

                        except (json.JSONDecodeError, KeyError):
                            continue

            except httpx.TimeoutException as exc:
                raise ProviderError("anthropic", f"Request timed out: {exc}") from exc
            except (ProviderAuthError, ProviderRateLimitError, ProviderError):
                raise
            except Exception as exc:
                raise ProviderError("anthropic", f"Unexpected error: {exc}") from exc

        yield LLMChunk(content="", is_final=True, tokens_used=tokens_used)
        logger.info(
            "anthropic_stream_complete",
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
                    raise ProviderAuthError("anthropic")
                if response.status_code == 429:
                    raise ProviderRateLimitError("anthropic")
                if response.status_code != 200:
                    raise ProviderError(
                        "anthropic", f"HTTP {response.status_code}: {response.text}"
                    )

                data = response.json()
                content = data["content"][0]["text"]
                usage = data.get("usage", {})
                tokens_used = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)

                return LLMResponse(
                    content=content,
                    tokens_used=tokens_used,
                    model=config.model,
                )
            except (ProviderAuthError, ProviderRateLimitError, ProviderError):
                raise
            except Exception as exc:
                raise ProviderError("anthropic", f"Unexpected error: {exc}") from exc

    def validate_api_key(self, api_key: str) -> bool:
        return api_key.startswith("sk-ant-") and len(api_key) > 20