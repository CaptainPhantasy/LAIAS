"""
Health check endpoints.

Provides service health status and connection checks.
"""

from fastapi import APIRouter, status
from datetime import datetime
import time
import logging

from app.models.responses import HealthResponse
from app.config import settings

router = APIRouter(tags=["health"])

# Service start time for uptime calculation
_start_time = time.time()

# Logger for health check failures
logger = logging.getLogger(__name__)


async def _check_postgresql() -> bool:
    """
    Check PostgreSQL database connectivity.

    Uses SQLAlchemy with asyncpg to execute a simple ping query.
    Returns True if connection succeeds, False otherwise.
    """
    try:
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import text

        # Create async engine from DATABASE_URL
        # DATABASE_URL already uses postgresql+asyncpg:// scheme
        engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=1,
            max_overflow=0,
            pool_pre_ping=True,
        )

        # Create session and execute ping
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            # Simple SELECT 1 to verify connection
            result = await session.execute(text("SELECT 1"))
            result.scalar_one()

        await engine.dispose()
        return True

    except Exception as e:
        logger.warning(f"PostgreSQL health check failed: {e}")
        return False


async def _check_redis() -> bool:
    """
    Check Redis connectivity.

    Uses redis.asyncio client to ping the Redis server.
    Returns True if connection succeeds, False otherwise.
    """
    try:
        import redis.asyncio as redis

        # Create async Redis client from REDIS_URL
        client = redis.from_url(
            settings.REDIS_URL,
            socket_timeout=1,  # 1 second timeout for health check
            socket_connect_timeout=1,
            decode_responses=False,
        )

        # Ping Redis
        await client.ping()
        await client.close()
        return True

    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        return False


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check service health and dependencies",
)
async def get_health() -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        HealthResponse: Service health status including:
        - Overall status
        - Docker connection status
        - Database connection status
        - Redis connection status
        - Service uptime
        - Current container count
    """
    from app.services.docker_service import get_docker_service
    from app.services.resource_monitor import get_resource_monitor

    # Check connections
    docker_ok = await get_docker_service().ping()
    database_ok = await _check_postgresql()
    redis_ok = await _check_redis()
    uptime = time.time() - _start_time

    # Determine overall health (degraded if any dependency is down)
    if docker_ok and database_ok and redis_ok:
        overall_status = "healthy"
    elif docker_ok:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    # Get current container count
    container_count = 0
    if docker_ok:
        try:
            containers = await get_docker_service().list_containers(all=True)
            container_count = len(containers)
        except Exception:
            pass

    return HealthResponse(
        status=overall_status,
        version=settings.SERVICE_VERSION,
        docker_connected=docker_ok,
        database_connected=database_ok,
        redis_connected=redis_ok,
        uptime_seconds=round(uptime, 2),
        container_count=container_count,
    )


@router.get(
    "/health/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
    description="Kubernetes liveness probe - returns 200 if service is running",
)
async def liveness() -> dict:
    """Liveness probe for Kubernetes."""
    return {"status": "alive"}


@router.get(
    "/health/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
    description="Kubernetes readiness probe - returns 200 if service is ready",
)
async def readiness() -> dict:
    """Readiness probe for Kubernetes."""
    from app.services.docker_service import docker_service

    docker_ready = await docker_service.check_connection()

    if docker_ready:
        return {"status": "ready"}
    else:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Docker daemon not connected"
        )
