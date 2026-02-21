"""Shared FastAPI dependency injection providers.

These are used with FastAPI's Depends() to inject shared resources
(database sessions, Redis connections, settings) into route handlers.

Usage:
    @router.get("/items")
    async def list_items(db: AsyncSession = Depends(get_db)):
        ...
"""

from collections.abc import AsyncGenerator

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db.session import async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session scoped to a single request.

    The session is committed on success, rolled back on exception,
    and always closed when the request completes.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_redis() -> AsyncGenerator[Redis, None]:
    """Yield a Redis connection for the request lifecycle.

    The connection is closed when the request completes.
    """
    settings = get_settings()
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield redis
    finally:
        await redis.aclose()


def get_config() -> Settings:
    """Return the application settings (cached singleton)."""
    return get_settings()