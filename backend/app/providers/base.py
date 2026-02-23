"""Base LLM provider interface.

All LLM providers (OpenAI, Anthropic, Gemini, etc.) implement this
abstract class. The execution engine interacts only with this interface,
making provider-swapping a runtime configuration change.

This is the Strategy Pattern:
- BaseLLMProvider = the strategy interface
- OpenAIProvider, AnthropicProvider = concrete strategies
- The execution engine = the context that uses the strategy

Adding a new provider requires only ONE new file implementing this class.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field


@dataclass
class LLMMessage:
    """A single message in a conversation.

    Attributes:
        role: "system", "user", or "assistant".
        content: The message text.
    """

    role: str
    content: str


@dataclass
class LLMConfig:
    """Configuration for an LLM call.

    These parameters are set per-agent in the workflow canvas.

    Attributes:
        model: Model identifier (e.g., "gpt-4o", "claude-sonnet-4-20250514").
        temperature: Sampling temperature (0.0 = deterministic, 2.0 = creative).
        max_tokens: Maximum tokens in the response.
    """

    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 2048


@dataclass
class LLMResponse:
    """Complete response from an LLM call.

    Attributes:
        content: The full response text.
        tokens_used: Total tokens consumed (prompt + completion).
        model: The model that generated the response.
    """

    content: str
    tokens_used: int = 0
    model: str = ""


@dataclass
class LLMChunk:
    """A single streaming chunk from an LLM.

    Attributes:
        content: The text fragment in this chunk.
        is_final: True if this is the last chunk.
        tokens_used: Total tokens (only set on final chunk).
    """

    content: str
    is_final: bool = False
    tokens_used: int = 0


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers.

    Every provider must implement stream() and complete().
    The stream() method is the primary interface used during
    workflow execution for real-time output.
    """

    @abstractmethod
    async def stream(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> AsyncGenerator[LLMChunk, None]:
        """Stream a response token-by-token.

        Args:
            messages: Conversation history (system + user messages).
            config: Model parameters (model name, temperature, max_tokens).

        Yields:
            LLMChunk objects containing text fragments.
            The final chunk has is_final=True and includes token count.
        """
        ...  # pragma: no cover

    @abstractmethod
    async def complete(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> LLMResponse:
        """Get a complete (non-streaming) response.

        Used for testing and cases where streaming isn't needed.

        Args:
            messages: Conversation history.
            config: Model parameters.

        Returns:
            Complete LLM response with full text and token usage.
        """
        ...  # pragma: no cover

    @abstractmethod
    def validate_api_key(self, api_key: str) -> bool:
        """Check if an API key is syntactically valid.

        This does NOT verify the key works — just checks format.
        For actual verification, use test_connection().

        Args:
            api_key: The API key to validate.

        Returns:
            True if the key format looks valid.
        """
        ...  # pragma: no cover