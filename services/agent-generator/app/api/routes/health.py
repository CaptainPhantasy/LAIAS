"""
Health endpoint for Agent Generator API.

GET /health
Service health check and status reporting.
"""

from datetime import datetime
import time
import structlog

from fastapi import APIRouter
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.session import AsyncSessionLocal
from app.models.responses import HealthResponse
from app.services.llm_service import get_llm_service

logger = structlog.get_logger()

router = APIRouter(tags=["health"])

# Track service start time
_start_time = time.time()

# Simple in-memory cache metrics tracking
_cache_hits = 0
_cache_misses = 0


@router.get("/health", response_model=HealthResponse, status_code=200)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns service status including:
    - Overall health status
    - Component status (LLM providers, database, Redis)
    - Service metrics
    - Version information
    """
    global _cache_hits, _cache_misses

    uptime = time.time() - _start_time

    # Check LLM provider status
    llm_service = get_llm_service()
    llm_status = await llm_service.check_health()

    # Check database connectivity
    database_status = await _check_database()

    # Check Redis connectivity
    redis_status = await _check_redis()

    # Get total generated agents count from database
    total_generated = await _get_total_agents()

    # Calculate cache hit rate
    total_cache_requests = _cache_hits + _cache_misses
    cache_hit_rate = (
        _cache_hits / total_cache_requests
        if total_cache_requests > 0
        else 0.0
    )

    # Determine overall status
    components_healthy = (
        (llm_status.get("openai") == "ok" or llm_status.get("anthropic") == "ok")
        and database_status == "ok"
    )
    components_degraded = (
        redis_status != "ok"
        or (llm_status.get("openai") != "not_configured" and llm_status.get("openai") != "ok")
        or (llm_status.get("anthropic") != "not_configured" and llm_status.get("anthropic") != "ok")
    )

    if components_healthy:
        overall_status = "healthy"
    elif components_degraded:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    return HealthResponse(
        status=overall_status,
        version=settings.app_version,
        uptime_seconds=round(uptime, 2),
        llm_status=llm_status,
        database_status=database_status,
        redis_status=redis_status,
        total_generated=total_generated,
        cache_hit_rate=round(cache_hit_rate, 4),
        checked_at=datetime.utcnow()
    )


@router.get("/readiness", status_code=200)
async def readiness_check():
    """
    Readiness check for Kubernetes/liveness probes.

    Returns 200 if service is ready to accept requests.
    """
    llm_service = get_llm_service()
    llm_status = await llm_service.check_health()

    # Check if at least one LLM provider is available
    openai_ok = llm_status.get("openai") == "ok"
    anthropic_ok = llm_status.get("anthropic") == "ok"

    if not (openai_ok or anthropic_ok):
        raise Exception("No LLM provider available")

    return {"status": "ready"}


@router.get("/liveness", status_code=200)
async def liveness_check():
    """
    Liveness check for Kubernetes/liveness probes.

    Returns 200 if service is alive.
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


# =============================================================================
# Health Check Helper Functions
# =============================================================================

async def _check_database() -> str:
    """
    Check PostgreSQL database connectivity.

    Returns:
        "ok" if database is reachable, "error" otherwise.
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return "ok"
    except Exception as e:
        logger.warning("Database health check failed", error=str(e))
        return "error"


async def _check_redis() -> str:
    """
    Check Redis connectivity.

    Returns:
        "ok" if Redis is reachable, "error" otherwise.
    """
    try:
        redis = Redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=False,
            socket_connect_timeout=2,
            socket_timeout=2
        )
        await redis.ping()
        await redis.close()
        return "ok"
    except Exception as e:
        logger.warning("Redis health check failed", error=str(e))
        return "error"


async def _get_total_agents() -> int:
    """
    Get total count of generated agents from database.

    Returns:
        Total number of agents in the database.
    """
    try:
        from sqlalchemy import func
        from app.models.database import Agent

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(func.count()).select_from(Agent)
            )
            return result.scalar() or 0
    except Exception as e:
        logger.warning("Failed to get agent count", error=str(e))
        return 0


def record_cache_hit() -> None:
    """Record a cache hit for metrics tracking."""
    global _cache_hits
    _cache_hits += 1


def record_cache_miss() -> None:
    """Record a cache miss for metrics tracking."""
    global _cache_misses
    _cache_misses += 1


def get_cache_metrics() -> tuple[int, int, float]:
    """
    Get current cache metrics.

    Returns:
        Tuple of (hits, misses, hit_rate)
    """
    global _cache_hits, _cache_misses
    total = _cache_hits + _cache_misses
    hit_rate = _cache_hits / total if total > 0 else 0.0
    return _cache_hits, _cache_misses, hit_rate
