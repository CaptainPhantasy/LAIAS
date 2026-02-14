"""
FastAPI application for Docker Orchestrator Service.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.config import settings
from app.api.routes import deploy, containers, logs, health
from app.services.docker_service import get_docker_service
from app.services.resource_monitor import get_resource_monitor
from app.utils.exceptions import (
    OrchestratorException,
    ContainerNotFoundError,
    DeploymentError,
    ResourceLimitError,
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
async def lifespan(app: FastAPI) -> AsyncGenerator:
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
    try:
        await get_docker_service().ping()
        logger.info("Docker connection verified")
    except Exception as e:
        logger.error("Docker connection failed", error=str(e))
        raise

    # Ensure agent code directory exists
    import os
    os.makedirs(settings.AGENT_CODE_PATH, exist_ok=True)
    logger.info("Agent code directory ready", path=settings.AGENT_CODE_PATH)

    # Metrics monitoring available on-demand (no background task needed)
    if settings.METRICS_ENABLED:
        logger.info("Metrics monitoring available")

    yield

    # Shutdown
    logger.info("Shutting down Docker Orchestrator")
    if monitor_task:
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass
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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
