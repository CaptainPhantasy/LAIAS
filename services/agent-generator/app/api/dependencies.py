"""
Shared dependencies for API routes.

Common dependencies for dependency injection in FastAPI routes.
"""

from fastapi import Header, HTTPException, status
from typing import Optional

from app.config import settings


async def get_api_key(x_api_key: Optional[str] = Header(None)) -> Optional[str]:
    """
    Optionally validate API key from header.

    Used for protected endpoints when API key authentication is enabled.
    """
    if settings.require_api_key and not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    return x_api_key


async def validate_content_length(content_length: Optional[int] = Header(None)) -> None:
    """
    Validate content length is within acceptable limits.

    Prevents excessively large requests that could cause issues.
    """
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB

    if content_length and content_length > MAX_CONTENT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Request body too large. Maximum size: {MAX_CONTENT_LENGTH} bytes"
        )
