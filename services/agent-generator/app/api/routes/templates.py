"""
Templates endpoint for Agent Generator API.

Agent template management and listing.
Uses TemplateService as the single source of truth for YAML-based templates.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
import structlog

from app.models.requests import GenerateAgentRequest
from app.services.template_service import get_template_service

logger = structlog.get_logger()

router = APIRouter(prefix="/api/templates", tags=["templates"])


# =============================================================================
# Response Models
# =============================================================================


class Template(BaseModel):
    """Agent template model."""

    id: str
    name: str
    description: str
    category: str
    tags: list[str]
    default_complexity: str
    default_tools: list[str]
    sample_prompts: list[str]
    suggested_config: dict
    agent_structure: dict
    expected_outputs: list[str]


class TemplateListResponse(BaseModel):
    """Response model for template list."""

    templates: list[Template]
    total: int
    categories: list[str]


class TemplateApplyRequest(BaseModel):
    """Request to apply a template."""

    template_id: str
    agent_name: str
    customizations: Optional[dict] = None


# =============================================================================
# Endpoints
# =============================================================================


@router.get("", response_model=TemplateListResponse, status_code=status.HTTP_200_OK)
async def list_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in name and description"),
) -> TemplateListResponse:
    """
    List all available agent templates.

    Query parameters:
    - **category**: Filter by category
    - **search**: Search in name and description
    """
    service = get_template_service()
    raw_templates = service.list_templates(category=category, search=search)
    categories = service.list_categories()

    templates = [Template(**t) for t in raw_templates]

    return TemplateListResponse(
        templates=templates,
        total=len(templates),
        categories=categories,
    )


@router.get("/categories", status_code=status.HTTP_200_OK)
async def list_categories() -> dict:
    """List all available template categories."""
    service = get_template_service()
    categories = service.list_categories()

    return {
        "categories": categories,
        "total": len(categories),
    }


@router.get("/{template_id}", response_model=Template, status_code=status.HTTP_200_OK)
async def get_template(template_id: str) -> Template:
    """
    Get a specific template by ID.

    Path parameters:
    - **template_id**: Template identifier (e.g., 'revenue_lead_scoring_qualifier')
    """
    service = get_template_service()
    template_data = service.get_template(template_id)

    if template_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found",
        )

    return Template(**template_data)


@router.post("/{template_id}/apply", status_code=status.HTTP_200_OK)
async def apply_template(
    template_id: str,
    request: TemplateApplyRequest,
) -> GenerateAgentRequest:
    """
    Apply a template to create a new agent generation request.

    This endpoint pre-fills a GenerateAgentRequest with template defaults,
    which can then be customized before submission to /api/generate.

    Path parameters:
    - **template_id**: Template identifier

    Request body:
    - **agent_name**: Name for the new agent
    - **customizations**: Optional overrides for template defaults
    """
    service = get_template_service()
    template = service.get_template(template_id)

    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found",
        )

    suggested_config = template.get("suggested_config", {})

    # Build the generation request from template
    generate_request = GenerateAgentRequest(
        description=template.get("sample_prompts", [""])[0] or template.get("description", ""),
        agent_name=request.agent_name,
        complexity=template.get("default_complexity", "moderate"),
        task_type=template.get("category", "general"),
        tools_requested=template.get("default_tools", []),
        llm_provider=suggested_config.get("llm_provider", "zai"),
        model=suggested_config.get("model"),
        include_memory=suggested_config.get("include_memory", True),
        include_analytics=suggested_config.get("include_analytics", True),
        max_agents=suggested_config.get("max_agents", 4),
    )

    # Apply customizations if provided
    if request.customizations:
        for key, value in request.customizations.items():
            if hasattr(generate_request, key):
                setattr(generate_request, key, value)

    logger.info(
        "Template applied",
        template_id=template_id,
        agent_name=request.agent_name,
    )

    return generate_request
