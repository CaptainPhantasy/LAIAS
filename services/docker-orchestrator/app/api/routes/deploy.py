"""
Agent deployment endpoints.

Handles deployment of generated agents to Docker containers.
"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from typing import Dict
import uuid
from datetime import datetime

from app.models.requests import DeployAgentRequest
from app.models.responses import DeploymentResponse
from app.services.docker_service import get_docker_service
from app.services.container_manager import get_container_manager
from app.utils.exceptions import (
    DeploymentError,
    ResourceLimitError,
    exception_to_http_response,
)

router = APIRouter(prefix="/api", tags=["deploy"])


@router.post(
    "/deploy",
    response_model=DeploymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Deploy agent",
    description="Deploy a generated agent to a new Docker container",
)
async def deploy_agent(
    request: DeployAgentRequest,
    background_tasks: BackgroundTasks,
) -> DeploymentResponse:
    """
    Deploy an agent to a container.

    Process:
    1. Generate unique deployment ID
    2. Write agent code to filesystem
    3. Create container with code mounted
    4. Start container if auto_start is True
    5. Return deployment info

    Args:
        request: Deployment request with agent code and config

    Returns:
        DeploymentResponse: Deployment details including endpoints

    Raises:
        HTTPException: If deployment fails
    """
    from app.config import settings

    # Check container limit
    try:
        container_count = len(await get_docker_service().list_containers(all=True))
        if container_count >= settings.MAX_CONTAINERS:
            raise ResourceLimitError(
                limit_type="Container",
                current=container_count,
                maximum=settings.MAX_CONTAINERS,
            )
    except Exception as e:
        if isinstance(e, ResourceLimitError):
            raise exception_to_http_response(e)
        # Continue on other errors

    # Generate deployment ID
    deployment_id = str(uuid.uuid4())

    try:
        # Deploy the agent
        container = await get_docker_service().deploy_agent(
            deployment_id=deployment_id,
            agent_id=request.agent_id,
            agent_name=request.agent_name,
            flow_code=request.flow_code,
            agents_yaml=request.agents_yaml,
            environment_vars=request.environment_vars,
            cpu_limit=request.cpu_limit,
            memory_limit=request.memory_limit,
        )

        # Start container if requested
        started_at = None
        container_status = "created"

        if request.auto_start:
            await get_docker_service().start_container(container.id)
            started_at = datetime.utcnow()
            container_status = "running"

        # Build response
        base_url = "ws://localhost:8002" if settings.DEBUG else "wss://api.laias.platform"

        return DeploymentResponse(
            deployment_id=deployment_id,
            agent_id=request.agent_id,
            container_id=container.id,
            container_name=container.name,
            status=container_status,  # type: ignore
            created_at=datetime.utcnow(),
            started_at=started_at,
            logs_endpoint=f"{base_url}/api/containers/{container.id}/logs/stream",
            metrics_endpoint=f"/api/containers/{container.id}/metrics",
        )

    except Exception as e:
        # Clean up on failure
        background_tasks.add_task(get_container_manager().cleanup_deployment, deployment_id)

        if isinstance(e, (DeploymentError, ResourceLimitError)):
            raise exception_to_http_response(e)
        else:
            # Log unexpected errors
            import structlog
            logger = structlog.get_logger()
            logger.error(
                "Unexpected deployment error",
                deployment_id=deployment_id,
                agent_id=request.agent_id,
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error_code": "DEPLOYMENT_ERROR",
                    "message": "Failed to deploy agent",
                    "detail": str(e),
                },
            )


@router.delete(
    "/deploy/{deployment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove deployment",
    description="Remove a deployment and its container",
)
async def remove_deployment(deployment_id: str) -> None:
    """
    Remove a deployment.

    Args:
        deployment_id: Deployment ID to remove

    Raises:
        HTTPException: If deployment not found or removal fails
    """
    try:
        await get_container_manager().remove_deployment(deployment_id)
    except Exception as e:
        from app.utils.exceptions import ContainerNotFoundError
        if isinstance(e, ContainerNotFoundError):
            raise exception_to_http_response(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "REMOVAL_FAILED",
                "message": f"Failed to remove deployment {deployment_id}",
                "detail": str(e),
            },
        )
