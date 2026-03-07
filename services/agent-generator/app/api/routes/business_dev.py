"""
Indiana SMB Business Development Agent API Endpoint

NOTE: This route requires the business development agent to be deployed
via the Docker Orchestrator. Direct execution from the API is not supported.
Use POST /api/deploy with the indiana_smb_business_development agent instead.
"""

import structlog
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

logger = structlog.get_logger()

router = APIRouter(prefix="/api", tags=["business-dev"])


class BusinessDevCampaignRequest(BaseModel):
    target_industries: list[str] = Field(
        default=["Healthcare", "Manufacturing", "Professional Services"]
    )
    target_geography: str = Field(
        default="Indiana (Brown County, Columbus, Bloomington, Indianapolis, 100-mile radius)"
    )
    campaign_duration: int = Field(default=30)
    daily_outreach_limit: int = Field(default=10)
    budget_per_lead: int = Field(default=50)
    service_focus: list[str] = Field(default=["software", "website"])
    outreach_channels: list[str] = Field(default=["email", "linkedin"])


@router.post("/business-dev-campaign", status_code=status.HTTP_303_SEE_OTHER)
async def start_business_dev_campaign(request: BusinessDevCampaignRequest) -> dict:
    """
    Start a business development campaign for Indiana SMBs.

    Business development agents must be deployed as containers via the
    Docker Orchestrator. This endpoint returns a redirect hint with the
    correct deployment URL and a pre-filled payload.
    """
    logger.info(
        "Business development campaign requested — redirecting to deploy",
        target_industries=request.target_industries,
        target_geography=request.target_geography,
    )
    return {
        "status": "redirect",
        "message": (
            "Business development campaigns run as deployed agents. "
            "Use the deploy endpoint to start one."
        ),
        "deploy_url": "/api/deploy",
        "suggested_payload": {
            "agent_name": "indiana_smb_business_development",
            "description": (
                f"SMB outreach campaign targeting {', '.join(request.target_industries)} "
                f"in {request.target_geography}"
            ),
            "auto_start": True,
        },
    }


@router.get(
    "/business-dev-campaign/{agent_id}",
    status_code=status.HTTP_303_SEE_OTHER,
)
async def get_business_dev_campaign_status(agent_id: str) -> dict:
    """
    Get campaign status.

    Campaign status is tracked via the Docker Orchestrator container
    endpoints. This endpoint returns a redirect hint.
    """
    return {
        "status": "redirect",
        "message": "Campaign status is available via the container endpoint.",
        "container_url": f"/api/containers/{agent_id}",
    }


@router.post(
    "/business-dev-campaign/{agent_id}/stop",
    status_code=status.HTTP_303_SEE_OTHER,
)
async def stop_business_dev_campaign(agent_id: str) -> dict:
    """
    Stop a campaign.

    Campaign lifecycle is managed via the Docker Orchestrator container
    endpoints. This endpoint returns a redirect hint.
    """
    return {
        "status": "redirect",
        "message": "Use the container stop endpoint to halt the campaign agent.",
        "stop_url": f"/api/containers/{agent_id}/stop",
    }
