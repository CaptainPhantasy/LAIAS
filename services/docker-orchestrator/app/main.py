"""
FastAPI application for Docker Orchestrator Service.
"""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import cast

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.types import ExceptionHandler

from app.api.routes import analytics, containers, convert, deploy, filesystem, health, logs, outputs
from app.config import settings
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.services.docker_service import get_docker_service
from app.utils.exceptions import (
    OrchestratorException,
    exception_to_http_response,
)

# Configure structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events for proper resource management.
    """
    # Startup
    logger.info(
        "Starting Docker Orchestrator",
        version=settings.SERVICE_VERSION,
        docker_host=settings.DOCKER_HOST,
        agent_image=settings.AGENT_IMAGE_BASE,
    )

    # Initialize Docker service
    docker_service = get_docker_service()
    try:
        await docker_service.ping()
        logger.info("Docker connection verified")
    except Exception as e:
        logger.error("Docker connection failed", error=str(e))
        raise

    gc_task: asyncio.Task[None] | None = None

    async def container_gc_worker() -> None:
        while True:
            try:
                await docker_service.garbage_collect_containers()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.warning("Container GC run failed", error=str(e))

            await asyncio.sleep(settings.GC_INTERVAL_SECONDS)

    # Ensure agent code directory exists
    import os

    os.makedirs(settings.AGENT_CODE_PATH, exist_ok=True)
    logger.info("Agent code directory ready", path=settings.AGENT_CODE_PATH)
    os.makedirs(settings.AGENT_OUTPUT_PATH, exist_ok=True)
    logger.info("Agent output directory ready", path=settings.AGENT_OUTPUT_PATH)

    # Metrics monitoring available on-demand (no background task needed)
    if settings.METRICS_ENABLED:
        logger.info("Metrics monitoring available")

    gc_task = asyncio.create_task(container_gc_worker(), name="container-gc-worker")
    logger.info(
        "Container GC background task started",
        interval_seconds=settings.GC_INTERVAL_SECONDS,
        max_age_hours=settings.GC_MAX_AGE_HOURS,
    )

    yield

    # Shutdown - Graceful cleanup
    logger.info("Shutting down Docker Orchestrator")

    if gc_task is not None:
        gc_task.cancel()
        try:
            await gc_task
        except asyncio.CancelledError:
            logger.info("Container GC background task stopped")

    # Stop all active log streams
    try:
        from app.services.log_streamer import get_log_streamer

        streamer = get_log_streamer()
        active_count = len(streamer._active_streams)
        if active_count > 0:
            logger.info("Stopping active log streams", count=active_count)
            streamer._active_streams.clear()
    except Exception as e:
        logger.warning("Failed to stop log streams", error=str(e))

    # Close Docker service connections
    try:
        if hasattr(docker_service, "close"):
            await docker_service.close()
        logger.info("Docker service connections closed")
    except Exception as e:
        logger.warning("Failed to close Docker service", error=str(e))

    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION,
    description="Docker container lifecycle management for LAIAS agents",
    lifespan=lifespan,
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
)

# Rate limiting
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler

app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    cast(ExceptionHandler, rate_limit_exceeded_handler),
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SecurityHeadersMiddleware,
    hsts_enabled=getattr(settings, "SECURITY_HSTS_ENABLED", True),
    hsts_value=getattr(settings, "SECURITY_HSTS_VALUE", "max-age=31536000; includeSubDomains"),
    trust_proxy_headers=getattr(settings, "SECURITY_TRUST_PROXY_HEADERS", True),
)


# Exception handlers
@app.exception_handler(OrchestratorException)
async def orchestrator_exception_handler(request, exc: OrchestratorException):
    """Handle custom orchestrator exceptions."""
    http_exc = exception_to_http_response(exc)
    return JSONResponse(
        status_code=http_exc.status_code,
        content=http_exc.detail,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle unhandled exceptions."""
    logger.error("Unhandled exception", error=str(exc), type=type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "type": type(exc).__name__},
    )


# Include routers
app.include_router(
    deploy.router,
)

app.include_router(
    containers.router,
)

app.include_router(
    logs.router,
)

app.include_router(
    health.router,
)

app.include_router(
    analytics.router,
)

app.include_router(
    outputs.router,
)

app.include_router(
    filesystem.router,
)

app.include_router(
    convert.router,
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "status": "running",
        "docs": f"{settings.API_PREFIX}/docs",
    }
