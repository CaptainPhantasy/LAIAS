"""
Custom exceptions for Docker Orchestrator.

Provides structured error handling with HTTP status codes.
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class OrchestratorException(Exception):
    """Base exception for all orchestrator errors."""

    def __init__(
        self,
        message: str,
        detail: Optional[str] = None,
        error_code: str = "ORCHESTRATOR_ERROR",
    ):
        self.message = message
        self.detail = detail
        self.error_code = error_code
        super().__init__(self.message)


class ContainerNotFoundError(OrchestratorException):
    """Raised when a container cannot be found."""

    def __init__(self, container_id: str, detail: Optional[str] = None):
        super().__init__(
            message=f"Container not found: {container_id}",
            detail=detail,
            error_code="CONTAINER_NOT_FOUND",
        )
        self.container_id = container_id


class DeploymentError(OrchestratorException):
    """Raised when agent deployment fails."""

    def __init__(
        self,
        agent_id: str,
        reason: str,
        detail: Optional[str] = None,
    ):
        super().__init__(
            message=f"Deployment failed for agent {agent_id}: {reason}",
            detail=detail,
            error_code="DEPLOYMENT_FAILED",
        )
        self.agent_id = agent_id
        self.reason = reason


class DockerConnectionError(OrchestratorException):
    """Raised when connection to Docker daemon fails."""

    def __init__(self, reason: str, detail: Optional[str] = None):
        super().__init__(
            message=f"Cannot connect to Docker daemon: {reason}",
            detail=detail,
            error_code="DOCKER_CONNECTION_ERROR",
        )
        self.reason = reason


class ResourceLimitError(OrchestratorException):
    """Raised when resource limits are exceeded."""

    def __init__(
        self,
        limit_type: str,
        current: int,
        maximum: int,
        detail: Optional[str] = None,
    ):
        super().__init__(
            message=f"{limit_type} limit exceeded: {current}/{maximum}",
            detail=detail,
            error_code="RESOURCE_LIMIT_EXCEEDED",
        )
        self.limit_type = limit_type
        self.current = current
        self.maximum = maximum


class InvalidConfigurationError(OrchestratorException):
    """Raised when configuration is invalid."""

    def __init__(self, field: str, reason: str, detail: Optional[str] = None):
        super().__init__(
            message=f"Invalid configuration for {field}: {reason}",
            detail=detail,
            error_code="INVALID_CONFIGURATION",
        )
        self.field = field
        self.reason = reason


class LogStreamingError(OrchestratorException):
    """Raised when log streaming fails."""

    def __init__(self, container_id: str, reason: str, detail: Optional[str] = None):
        super().__init__(
            message=f"Log streaming failed for container {container_id}: {reason}",
            detail=detail,
            error_code="LOG_STREAMING_ERROR",
        )
        self.container_id = container_id
        self.reason = reason


def exception_to_http_response(exc: OrchestratorException) -> HTTPException:
    """Convert an OrchestratorException to an HTTPException."""

    status_map: Dict[str, int] = {
        "CONTAINER_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "DEPLOYMENT_FAILED": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "DOCKER_CONNECTION_ERROR": status.HTTP_503_SERVICE_UNAVAILABLE,
        "RESOURCE_LIMIT_EXCEEDED": status.HTTP_429_TOO_MANY_REQUESTS,
        "INVALID_CONFIGURATION": status.HTTP_400_BAD_REQUEST,
        "LOG_STREAMING_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }

    http_status = status_map.get(
        exc.error_code,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )

    return HTTPException(
        status_code=http_status,
        detail={
            "error_code": exc.error_code,
            "message": exc.message,
            "detail": exc.detail,
        },
    )
