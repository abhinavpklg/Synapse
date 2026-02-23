"""LLM Provider registry and factory.

Maps provider type strings to their implementation classes.
The execution engine calls get_provider() to get the right
provider instance for each agent's configuration.

Adding a new provider:
1. Create a new file in app/providers/ implementing BaseLLMProvider
2. Register it in PROVIDER_MAP below
That's it — no changes to the engine, API, or frontend needed.
"""

from app.core.exceptions import ProviderAuthError, ProviderError
from app.core.logging import get_logger
from app.providers.base import BaseLLMProvider
from app.providers.openai import OpenAIProvider
from app.providers.anthropic import AnthropicProvider
from app.providers.gemini import GeminiProvider
from app.providers.groq import GroqProvider
from app.providers.openrouter import OpenRouterProvider

logger = get_logger(__name__)

# Map provider type strings to implementation classes
PROVIDER_MAP: dict[str, type[BaseLLMProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "groq": GroqProvider,
    "openrouter": OpenRouterProvider,
}


def get_provider(
    provider_type: str,
    api_key: str,
    base_url: str | None = None,
) -> BaseLLMProvider:
    """Get an instantiated LLM provider.

    Args:
        provider_type: Provider identifier ("openai", "anthropic", etc.).
        api_key: The API key for this provider.
        base_url: Optional custom endpoint URL.

    Returns:
        An instance of the appropriate provider.

    Raises:
        ProviderError: If the provider type is not supported.
        ProviderAuthError: If no API key is provided.
    """
    if not api_key:
        raise ProviderAuthError(provider_type)

    provider_class = PROVIDER_MAP.get(provider_type)
    if not provider_class:
        raise ProviderError(
            provider_type,
            f"Unsupported provider: '{provider_type}'. "
            f"Available: {list(PROVIDER_MAP.keys())}",
        )

    logger.debug("provider_instantiated", provider=provider_type)
    return provider_class(api_key=api_key, base_url=base_url)


def list_available_providers() -> list[str]:
    """Return list of registered provider type strings."""
    return list(PROVIDER_MAP.keys())