"""
Indiana SMB Business Development Agent API Endpoint

NOTE: This route requires the business development agent to be deployed
via the Docker Orchestrator. Direct execution from the API is not supported.
Use POST /api/deploy with the indiana_smb_business_development agent instead.
"""


import structlog
from fastapi import APIRouter, HTTPException, status
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


@router.post("/business-dev-campaign", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def start_business_dev_campaign(request: BusinessDevCampaignRequest) -> dict:
    """
    Start a business development campaign for Indiana SMBs.

    This endpoint is not yet implemented. Business development agents should
    be deployed as containers via the Docker Orchestrator (POST /api/deploy).
    """
    logger.info(
        "Business development campaign requested (not implemented)",
        target_industries=request.target_industries,
        target_geography=request.target_geography,
    )
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=(
            "Direct campaign execution is not implemented. "
            "Deploy the indiana_smb_business_development agent via "
            "POST http://localhost:4522/api/deploy instead."
        ),
    )


@router.get(
    "/business-dev-campaign/{agent_id}",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
)
async def get_business_dev_campaign_status(agent_id: str) -> dict:
    """
    Get campaign status. Not yet implemented — use the Docker Orchestrator
    container endpoints to monitor deployed agent status.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=(
            "Campaign status tracking is not implemented. "
            "Use GET http://localhost:4522/api/containers/{container_id} "
            "to check deployed agent status."
        ),
    )


@router.post(
    "/business-dev-campaign/{agent_id}/stop",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
)
async def stop_business_dev_campaign(agent_id: str) -> dict:
    """
    Stop a campaign. Not yet implemented — use the Docker Orchestrator
    container endpoints to stop deployed agent containers.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=(
            "Direct campaign control is not implemented. "
            "Use POST http://localhost:4522/api/containers/{container_id}/stop "
            "to stop a deployed agent."
        ),
    )
