"""
Rate limiting configuration for LAIAS Agent Generator.

Uses slowapi (FastAPI-Limiter) to limit requests on expensive endpoints.
"""

import structlog
from fastapi import HTTPException, Request, status
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

logger = structlog.get_logger()


def get_client_identifier(request: Request) -> str:
    """
    Get client identifier for rate limiting.

    Priority:
    1. Authenticated user ID (from X-User-Id header or JWT)
    2. X-Forwarded-For header (behind proxy)
    3. Client IP address
    """
    # Try to get user ID from auth header or dev mode header
    user_id = request.headers.get("X-User-Id")
    if user_id:
        return f"user:{user_id}"

    # Try forwarded header (for reverse proxies)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take first IP (original client)
        return f"ip:{forwarded.split(',')[0].strip()}"

    # Fall back to direct client address
    return f"ip:{get_remote_address(request)}"


# Create limiter instance
limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=["200/minute"],  # Default: 200 requests per minute
    storage_uri="redis://redis:6379/0",  # Use Redis for distributed rate limiting
    enabled=True,
)


# Rate limit configurations for different endpoint types
RATE_LIMITS = {
    # LLM generation endpoints - expensive API calls
    "generation": "10/minute",  # 10 generations per minute per user

    # Docker deployment endpoints - resource intensive
    "deployment": "20/minute",  # 20 deployments per minute

    # Standard API operations
    "standard": "100/minute",  # 100 requests per minute

    # Auth endpoints - prevent brute force
    "auth": "20/minute",  # 20 auth attempts per minute
}


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded errors.

    Returns a JSON response with retry information.
    """
    logger.warning(
        "Rate limit exceeded",
        client=get_client_identifier(request),
        path=request.url.path,
        limit=str(exc.detail),
    )

    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "Rate limit exceeded",
            "message": "Too many requests. Please wait before trying again.",
            "retry_after": "60s",
        },
    )
