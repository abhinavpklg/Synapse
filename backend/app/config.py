"""Application configuration loaded from environment variables.

Uses pydantic-settings to validate and parse all config at startup.
If a required variable is missing, the app fails fast with a clear error.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application settings.

    All values are read from environment variables or a .env file.
    Variable names are case-insensitive (APP_NAME, app_name both work).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Application ──────────────────────────────────
    app_name: str = "synapse"
    app_version: str = "0.1.0"
    debug: bool = False

    # ── Server ───────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173"]

    # ── Database ─────────────────────────────────────
    database_url: str

    # ── Redis ────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Security ─────────────────────────────────────
    secret_key: str = "change-me-in-production"
    encryption_key: str = "change-me-generate-a-real-fernet-key"

    # ── LLM Providers (optional env-based keys) ─────
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None
    groq_api_key: str | None = None
    deepseek_api_key: str | None = None
    openrouter_api_key: str | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance.

    Using lru_cache ensures we parse env vars only once,
    not on every request. The Settings object is immutable
    after creation.
    """
    return Settings()