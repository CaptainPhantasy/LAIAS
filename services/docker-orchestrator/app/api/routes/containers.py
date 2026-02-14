"""
Container management endpoints.

Provides CRUD operations for agent containers.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Optional, List
from datetime import datetime

from app.models.requests import ContainerActionRequest
from app.models.responses import ContainerInfo, ContainerListResponse
from app.services.docker_service import docker_service
from app.services.resource_monitor import resource_monitor
from app.utils.exceptions import (
    ContainerNotFoundError,
    exception_to_http_response,
)

router = APIRouter(prefix="/api", tags=["containers"])


@router.get(
    "/containers",
    response_model=ContainerListResponse,
    summary="List containers",
    description="List all LAIAS agent containers",
)
async def list_containers(
    status_filter: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> ContainerListResponse:
    """
    List all agent containers.

    Args:
        status_filter: Optional status filter (running, stopped, etc.)
        limit: Maximum number of containers to return
        offset: Number of containers to skip

    Returns:
        ContainerListResponse: List of containers with summary
    """
    try:
        containers = await docker_service.list_containers(all=True)

        # Apply status filter if provided
        if status_filter:
            containers = [c for c in containers if c.get("status") == status_filter]

        # Apply pagination
        total = len(containers)
        containers = containers[offset:offset + limit]

        # Enrich with metrics
        enriched_containers = []
        running_count = 0
        stopped_count = 0

        for container in containers:
            container_status = container.get("status", "unknown")

            # Count by status
            if "running" in container_status.lower():
                running_count += 1
            else:
                stopped_count += 1

            # Get metrics if running
            cpu_usage = 0.0
            memory_usage = "0m"
            uptime = None

            if "running" in container_status.lower():
                try:
                    metrics = await resource_monitor.get_metrics(container["container_id"])
                    cpu_usage = metrics.cpu_percent
                    memory_usage = f"{int(metrics.memory_usage_mb)}m"
                    uptime = metrics.uptime_seconds
                except Exception:
                    pass

            enriched_containers.append(
                ContainerInfo(
                    container_id=container["container_id"],
                    deployment_id=container.get("deployment_id", "unknown"),
                    agent_id=container.get("agent_id", "unknown"),
                    agent_name=container.get("name", "unknown"),
                    status=container_status,
                    cpu_usage=cpu_usage,
                    memory_usage=memory_usage,
                    uptime_seconds=uptime,
                    created_at=datetime.fromisoformat(container["created"].replace("Z", "+00:00")),
                    last_activity=None,
                )
            )

        return ContainerListResponse(
            containers=enriched_containers,
            total=total,
            running=running_count,
            stopped=stopped_count,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "LIST_CONTAINERS_FAILED",
                "message": "Failed to list containers",
                "detail": str(e),
            },
        )


@router.get(
    "/containers/{container_id}",
    response_model=ContainerInfo,
    summary="Get container details",
    description="Get detailed information about a specific container",
)
async def get_container(container_id: str) -> ContainerInfo:
    """
    Get container details.

    Args:
        container_id: Container ID (short or long)

    Returns:
        ContainerInfo: Container details

    Raises:
        HTTPException: If container not found
    """
    try:
        container = await docker_service.get_container(container_id)

        # Get metrics
        metrics = await resource_monitor.get_metrics(container_id)

        return ContainerInfo(
            container_id=container.id,
            deployment_id=container.labels.get("deployment_id", "unknown"),
            agent_id=container.labels.get("agent_id", "unknown"),
            agent_name=container.labels.get("agent_name", "unknown"),
            status=container.status,
            cpu_usage=metrics.cpu_percent,
            memory_usage=f"{int(metrics.memory_usage_mb)}m",
            uptime_seconds=metrics.uptime_seconds,
            created_at=datetime.fromisoformat(
                container.attrs["Created"].replace("Z", "+00:00")
            ),
            last_activity=None,
        )

    except Exception as e:
        if "not found" in str(e).lower():
            raise exception_to_http_response(
                ContainerNotFoundError(container_id, detail=str(e))
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "GET_CONTAINER_FAILED",
                "message": f"Failed to get container {container_id}",
                "detail": str(e),
            },
        )


@router.post(
    "/containers/{container_id}/start",
    summary="Start container",
    description="Start a stopped container",
)
async def start_container(container_id: str) -> dict:
    """
    Start a container.

    Args:
        container_id: Container ID

    Returns:
        dict: Operation result
    """
    try:
        await docker_service.start_container(container_id)
        return {
            "container_id": container_id,
            "status": "started",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        if "not found" in str(e).lower():
            raise exception_to_http_response(
                ContainerNotFoundError(container_id, detail=str(e))
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "START_FAILED",
                "message": f"Failed to start container {container_id}",
                "detail": str(e),
            },
        )


@router.post(
    "/containers/{container_id}/stop",
    summary="Stop container",
    description="Stop a running container",
)
async def stop_container(
    container_id: str,
    timeout: int = 10,
) -> dict:
    """
    Stop a container.

    Args:
        container_id: Container ID
        timeout: Seconds to wait before force stopping

    Returns:
        dict: Operation result
    """
    try:
        await docker_service.stop_container(container_id, timeout=timeout)
        return {
            "container_id": container_id,
            "status": "stopped",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        if "not found" in str(e).lower():
            raise exception_to_http_response(
                ContainerNotFoundError(container_id, detail=str(e))
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "STOP_FAILED",
                "message": f"Failed to stop container {container_id}",
                "detail": str(e),
            },
        )


@router.post(
    "/containers/{container_id}/restart",
    summary="Restart container",
    description="Restart a container",
)
async def restart_container(
    container_id: str,
    timeout: int = 10,
) -> dict:
    """
    Restart a container.

    Args:
        container_id: Container ID
        timeout: Seconds to wait during stop

    Returns:
        dict: Operation result
    """
    try:
        await docker_service.restart_container(container_id, timeout=timeout)
        return {
            "container_id": container_id,
            "status": "restarted",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        if "not found" in str(e).lower():
            raise exception_to_http_response(
                ContainerNotFoundError(container_id, detail=str(e))
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "RESTART_FAILED",
                "message": f"Failed to restart container {container_id}",
                "detail": str(e),
            },
        )


@router.delete(
    "/containers/{container_id}",
    summary="Remove container",
    description="Remove a container and clean up its resources",
)
async def remove_container(
    container_id: str,
    force: bool = False,
) -> dict:
    """
    Remove a container.

    Args:
        container_id: Container ID
        force: Force removal even if running

    Returns:
        dict: Operation result
    """
    try:
        await docker_service.remove_container(container_id, force=force)
        return {
            "container_id": container_id,
            "status": "removed",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        if "not found" in str(e).lower():
            raise exception_to_http_response(
                ContainerNotFoundError(container_id, detail=str(e))
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "REMOVE_FAILED",
                "message": f"Failed to remove container {container_id}",
                "detail": str(e),
            },
        )


@router.get(
    "/containers/{container_id}/metrics",
    summary="Get container metrics",
    description="Get resource usage metrics for a container",
)
async def get_container_metrics(container_id: str):
    """
    Get container metrics.

    Args:
        container_id: Container ID

    Returns:
        MetricsResponse: Container metrics
    """
    from app.models.responses import MetricsResponse

    try:
        metrics = await resource_monitor.get_metrics(container_id)
        return metrics
    except Exception as e:
        if "not found" in str(e).lower():
            raise exception_to_http_response(
                ContainerNotFoundError(container_id, detail=str(e))
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "METRICS_FAILED",
                "message": f"Failed to get metrics for container {container_id}",
                "detail": str(e),
            },
        )
