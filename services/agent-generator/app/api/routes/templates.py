"""
Templates endpoint for Agent Generator API.

Agent template management and listing.
"""

import os
from pathlib import Path
from typing import Optional
import yaml

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel
import structlog

from app.models.requests import GenerateAgentRequest

logger = structlog.get_logger()

router = APIRouter(prefix="/api/templates", tags=["templates"])

# Templates directory path - use environment variable or default
TEMPLATES_DIR = Path(os.environ.get("TEMPLATES_DIR", "/app/templates/presets"))


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


def load_template(template_id: str) -> dict:
    """Load a template YAML file."""
    template_path = TEMPLATES_DIR / f"{template_id}.yaml"

    if not template_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found"
        )

    try:
        with open(template_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error("Failed to load template", template_id=template_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load template: {str(e)}"
        )


def load_all_templates() -> list[dict]:
    """Load all template YAML files."""
    templates = []

    if not TEMPLATES_DIR.exists():
        logger.warning("Templates directory not found", path=str(TEMPLATES_DIR))
        return templates

    for template_file in TEMPLATES_DIR.glob("*.yaml"):
        try:
            with open(template_file, "r") as f:
                template_data = yaml.safe_load(f)
                templates.append(template_data)
        except Exception as e:
            logger.error("Failed to load template file", file=str(template_file), error=str(e))

    return templates


@router.get("", response_model=TemplateListResponse, status_code=status.HTTP_200_OK)
async def list_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in name and description")
) -> TemplateListResponse:
    """
    List all available agent templates.

    Query parameters:
    - **category**: Filter by category
    - **search**: Search in name and description
    """
    templates = load_all_templates()

    # Apply filters
    if category:
        templates = [t for t in templates if t.get("category") == category]

    if search:
        search_lower = search.lower()
        templates = [
            t for t in templates
            if search_lower in t.get("name", "").lower() or
               search_lower in t.get("description", "").lower()
        ]

    # Extract unique categories
    all_templates = load_all_templates()
    categories = sorted(set(t.get("category", "general") for t in all_templates))

    return TemplateListResponse(
        templates=templates,
        total=len(templates),
        categories=categories
    )


@router.get("/categories", status_code=status.HTTP_200_OK)
async def list_categories() -> dict:
    """List all available template categories."""
    templates = load_all_templates()
    categories = sorted(set(t.get("category", "general") for t in templates))

    return {
        "categories": categories,
        "total": len(categories)
    }


@router.get("/{template_id}", response_model=Template, status_code=status.HTTP_200_OK)
async def get_template(template_id: str) -> Template:
    """
    Get a specific template by ID.

    Path parameters:
    - **template_id**: Template identifier (e.g., 'research_agent')
    """
    template_data = load_template(template_id)
    return Template(**template_data)


@router.post("/{template_id}/apply", status_code=status.HTTP_200_OK)
async def apply_template(
    template_id: str,
    request: TemplateApplyRequest
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
    template = load_template(template_id)

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
        max_agents=suggested_config.get("max_agents", 4)
    )

    # Apply customizations if provided
    if request.customizations:
        for key, value in request.customizations.items():
            if hasattr(generate_request, key):
                setattr(generate_request, key, value)

    logger.info(
        "Template applied",
        template_id=template_id,
        agent_name=request.agent_name
    )

    return generate_request
