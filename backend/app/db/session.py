"""Async database engine and session management.

Provides the SQLAlchemy async engine, session factory, and a
dependency-injectable session generator for FastAPI routes.

Usage in routes:
    @router.get("/items")
    async def list_items(db: AsyncSession = Depends(get_db_session)):
        ...
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ── Engine & Session Factory ─────────────────────────
# These are initialized at module import time using settings.
# The engine manages a connection pool to PostgreSQL.
# The session factory creates individual sessions per request.

_settings = get_settings()

engine = create_async_engine(
    _settings.database_url,
    echo=_settings.debug,       # Log SQL statements in debug mode
    pool_size=10,               # Max persistent connections
    max_overflow=20,            # Extra connections under load
    pool_pre_ping=True,         # Verify connections are alive before using
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,     # Don't expire objects after commit (avoids lazy-load issues)
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session for a single request lifecycle.

    Used as a FastAPI dependency. The session is automatically
    closed when the request completes, even if an error occurs.

    Yields:
        An async SQLAlchemy session.
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()