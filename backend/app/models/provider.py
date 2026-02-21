"""Provider configuration ORM model.

Stores LLM provider API keys (encrypted) and endpoint configuration.
Each provider (OpenAI, Anthropic, etc.) can have one configuration row.
"""

from sqlalchemy import Boolean, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.workflow import ProviderType


class ProviderConfig(Base):
    """Configuration for an LLM provider, including encrypted API key.

    API keys are encrypted using Fernet symmetric encryption before
    storage. They are decrypted only when making API calls.
    The is_default flag marks the default provider for new agent nodes.
    """

    __tablename__ = "provider_configs"

    provider: Mapped[ProviderType] = mapped_column(
        Enum(ProviderType),
        unique=True,
    )
    api_key_encrypted: Mapped[str] = mapped_column(Text)
    base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<ProviderConfig provider={self.provider.value}>"