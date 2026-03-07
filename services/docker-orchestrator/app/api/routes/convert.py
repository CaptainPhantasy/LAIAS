"""
Format conversion API route.

Provides a stateless endpoint for converting content between formats
(e.g., Markdown to HTML).
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.auth import verify_api_key
from app.services.format_converter import get_format_converter

router = APIRouter(prefix="/api", tags=["convert"], dependencies=[Depends(verify_api_key)])


# =============================================================================
# Request / Response Models
# =============================================================================


class ConvertRequest(BaseModel):
    """Request body for content conversion."""

    content: str = Field(..., description="Content to convert")
    format: Literal["html", "markdown"] = Field(..., description="Target format: html or markdown")


class ConvertResponse(BaseModel):
    """Response body with converted content."""

    converted: str = Field(..., description="Converted content")
    format: Literal["html", "markdown"] = Field(..., description="Target format used")
    content_length: int = Field(..., description="Length of converted content")


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/convert", response_model=ConvertResponse)
async def convert_content(request: ConvertRequest):
    """Convert content to the requested format."""
    converter = get_format_converter()
    try:
        converted = converter.convert(request.content, request.format)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return ConvertResponse(
        converted=converted,
        format=request.format,
        content_length=len(converted),
    )
