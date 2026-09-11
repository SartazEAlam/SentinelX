"""SentinelX Backend — FastAPI application entry point."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes_health import router as health_router
from app.api.v1.router import api_router
from app.config import get_settings
from app.core.exceptions import SentinelXError
from app.db.database import SessionLocal, engine
from app.logging_config import setup_logging
from app.services.auth_service import create_initial_admin_if_needed

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler — startup and shutdown logic."""
    settings = get_settings()

    # Initialize logging
    setup_logging(settings.LOG_LEVEL)

    logger.info(
        "Starting %s v%s [%s]",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.ENVIRONMENT,
    )

    # Log database target
    db_target = (
        settings.DATABASE_URL.split("@")[-1]
        if "@" in settings.DATABASE_URL
        else settings.DATABASE_URL.split("///")[-1]
    )
    logger.info("Database initialized - %s", db_target)

    # Bootstrap operations
    try:
        with SessionLocal() as db:
            create_initial_admin_if_needed(db)
    except Exception as e:
        logger.error("Failed to run bootstrap tasks: %s", e)

    yield

    # Shutdown
    engine.dispose()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Intelligent Data Loss Prevention and Exfiltration Detection System",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handler — never expose stack traces
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch unhandled exceptions and return a structured error response."""
        logger.error("Unhandled exception on %s %s: %s", request.method, request.url.path, exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred.",
                }
            },
        )

    @app.exception_handler(SentinelXError)
    async def sentinelx_exception_handler(request: Request, exc: SentinelXError) -> JSONResponse:
        """Catch custom SentinelX exceptions."""
        status_code = 400
        if exc.code == "NOT_FOUND":
            status_code = 404
        elif exc.code == "CONFLICT":
            status_code = 409
        elif exc.code == "UNAUTHORIZED":
            status_code = 401
        elif exc.code == "FORBIDDEN":
            status_code = 403

        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                }
            },
        )

    # Mount versioned API routes
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
