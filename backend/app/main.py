"""FastAPI application factory for Synapse.

Creates and configures the FastAPI app with:
- CORS middleware for frontend access
- Lifespan events for startup/shutdown
- Exception handlers for custom error types
- Health check endpoint
- API route registration (added as routes are built)
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.core.exceptions import (
    NotFoundError,
    ProviderAuthError,
    ProviderError,
    ProviderRateLimitError,
    SynapseError,
    ValidationError,
)
from app.core.logging import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle.

    Startup: initialize logging, verify database connectivity.
    Shutdown: clean up connections.
    """
    settings = get_settings()
    setup_logging(debug=settings.debug)
    logger.info(
        "starting_synapse",
        version=settings.app_version,
        debug=settings.debug,
    )

    # Verify database connectivity
    from app.db.session import engine

    async with engine.begin() as conn:
        await conn.execute(
            __import__("sqlalchemy").text("SELECT 1")
        )
    logger.info("database_connected")

    yield

    # Shutdown
    from app.db.session import engine as db_engine

    await db_engine.dispose()
    logger.info("synapse_shutdown_complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Synapse API",
        description="Visual multi-agent AI orchestration platform",
        version=settings.app_version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # ── CORS Middleware ──────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception Handlers ───────────────────────────
    _register_exception_handlers(app)

    # ── Routes ───────────────────────────────────────
    _register_routes(app)

    return app


def _register_exception_handlers(app: FastAPI) -> None:
    """Map custom exceptions to HTTP responses."""

    @app.exception_handler(NotFoundError)
    async def not_found_handler(_req: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"error": exc.code, "message": exc.message},
        )

    @app.exception_handler(ValidationError)
    async def validation_handler(_req: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"error": exc.code, "message": exc.message},
        )

    @app.exception_handler(ProviderAuthError)
    async def provider_auth_handler(_req: Request, exc: ProviderAuthError) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={"error": exc.code, "message": exc.message},
        )

    @app.exception_handler(ProviderRateLimitError)
    async def rate_limit_handler(_req: Request, exc: ProviderRateLimitError) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={"error": exc.code, "message": exc.message},
        )

    @app.exception_handler(ProviderError)
    async def provider_handler(_req: Request, exc: ProviderError) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content={"error": exc.code, "message": exc.message},
        )

    @app.exception_handler(SynapseError)
    async def synapse_handler(_req: Request, exc: SynapseError) -> JSONResponse:
        logger.error("unhandled_synapse_error", code=exc.code, message=exc.message)
        return JSONResponse(
            status_code=500,
            content={"error": exc.code, "message": exc.message},
        )


def _register_routes(app: FastAPI) -> None:
    """Register all API routes.

    Routes are added incrementally as we build each feature.
    """

    @app.get("/api/health", tags=["system"])
    async def health_check() -> dict:
        """Health check endpoint for deployment platforms and monitoring."""
        settings = get_settings()
        return {
            "status": "ok",
            "app": settings.app_name,
            "version": settings.app_version,
        }

    # API v1 routes will be registered here as we build them:
    # from app.api.v1.router import api_v1_router
    # app.include_router(api_v1_router, prefix="/api/v1")


# Create the app instance — this is what uvicorn imports
app = create_app()