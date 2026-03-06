"""
Agent deployment endpoints.

Handles deployment of generated agents to Docker containers.
"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Request, Depends
from typing import Dict
import uuid
import json
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.requests import DeployAgentRequest
from app.models.responses import DeploymentResponse
from app.services.docker_service import get_docker_service
from app.services.container_manager import get_container_manager
from app.database.session import get_db
from app.utils.exceptions import (
    DeploymentError,
    ResourceLimitError,
    exception_to_http_response,
)
from app.middleware.rate_limit import limiter, RATE_LIMITS

router = APIRouter(prefix="/api", tags=["deploy"])


@limiter.limit(RATE_LIMITS["deployment"])
@router.post(
    "/deploy",
    response_model=DeploymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Deploy agent",
    description="Deploy a generated agent to a new Docker container",
)
async def deploy_agent(
    request: Request,
    body: DeployAgentRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
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
        body: Deployment request with agent code and config

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
            agent_id=body.agent_id,
            agent_name=body.agent_name,
            flow_code=body.flow_code,
            agents_yaml=body.agents_yaml,
            environment_vars=body.environment_vars,
            output_config=body.output_config,
            cpu_limit=body.cpu_limit,
            memory_limit=body.memory_limit,
        )

        # Start container if requested
        started_at = None
        container_status = "created"

        if body.auto_start:
            await get_docker_service().start_container(container.id)
            started_at = datetime.utcnow()
            container_status = "running"

        try:
            await db.execute(
                text(
                    """
                    INSERT INTO deployments (
                        id,
                        agent_id,
                        container_id,
                        container_name,
                        status,
                        cpu_limit,
                        memory_limit,
                        environment_vars,
                        created_at,
                        started_at
                    ) VALUES (
                        :id,
                        :agent_id,
                        :container_id,
                        :container_name,
                        :status,
                        :cpu_limit,
                        :memory_limit,
                        CAST(:environment_vars AS jsonb),
                        :created_at,
                        :started_at
                    )
                    ON CONFLICT (id)
                    DO UPDATE SET
                        container_id = EXCLUDED.container_id,
                        container_name = EXCLUDED.container_name,
                        status = EXCLUDED.status,
                        cpu_limit = EXCLUDED.cpu_limit,
                        memory_limit = EXCLUDED.memory_limit,
                        environment_vars = EXCLUDED.environment_vars,
                        started_at = EXCLUDED.started_at
                    """
                ),
                {
                    "id": deployment_id,
                    "agent_id": body.agent_id,
                    "container_id": container.id,
                    "container_name": container.name,
                    "status": container_status,
                    "cpu_limit": body.cpu_limit,
                    "memory_limit": body.memory_limit,
                    "environment_vars": json.dumps(body.environment_vars),
                    "created_at": datetime.utcnow(),
                    "started_at": started_at,
                },
            )
            await db.commit()
        except Exception as db_error:
            await db.rollback()
            import structlog

            structlog.get_logger().warning(
                "Failed to persist deployment row",
                deployment_id=deployment_id,
                agent_id=body.agent_id,
                error=str(db_error),
            )

        # Build response
        base_url = "ws://localhost:8002" if settings.DEBUG else "wss://api.laias.platform"

        # Record analytics event
        from app.services.analytics_store import analytics_store

        await analytics_store.add_event(
            "deployment",
            {
                "deployment_id": deployment_id,
                "agent_id": body.agent_id,
                "agent_name": body.agent_name,
                "status": container_status,
            },
        )

        return DeploymentResponse(
            deployment_id=deployment_id,
            agent_id=body.agent_id,
            container_id=container.id,
            container_name=container.name,
            status=container_status,  # type: ignore
            created_at=datetime.utcnow(),
            started_at=started_at,
            logs_endpoint=f"{base_url}/api/containers/{container.id}/logs/stream",
            metrics_endpoint=f"/api/containers/{container.id}/metrics",
            output_config=body.output_config,
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
                agent_id=body.agent_id,
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

        # Record failed deployment analytics
        from app.services.analytics_store import analytics_store

        await analytics_store.add_event(
            "deployment",
            {
                "deployment_id": deployment_id,
                "agent_id": body.agent_id,
                "agent_name": body.agent_name,
                "status": "error",
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
