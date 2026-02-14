"""
Response models for Docker Orchestrator API.

Pydantic models for API response serialization.
"""

from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class DeploymentResponse(BaseModel):
    """Response after deploying an agent."""

    deployment_id: str = Field(..., description="Unique deployment ID")
    agent_id: str = Field(..., description="Agent ID")
    container_id: str = Field(..., description="Docker container ID")
    container_name: str = Field(..., description="Docker container name")
    status: Literal["created", "starting", "running", "stopped", "error"] = Field(
        ..., description="Container status"
    )
    ports: Dict[str, int] = Field(default_factory=dict, description="Exposed ports")
    created_at: datetime = Field(..., description="Creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    logs_endpoint: str = Field(..., description="WebSocket URL for logs")
    metrics_endpoint: str = Field(..., description="REST URL for metrics")

    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class ContainerInfo(BaseModel):
    """Information about a container."""

    container_id: str = Field(..., description="Docker container ID", alias="id")
    deployment_id: str = Field(..., description="Deployment ID")
    agent_id: str = Field(..., description="Agent ID")
    agent_name: str = Field(..., description="Human-readable agent name")
    status: str = Field(..., description="Container status")
    cpu_usage: float = Field(..., description="Current CPU usage percent")
    memory_usage: str = Field(..., description="Current memory usage")
    uptime_seconds: Optional[int] = Field(None, description="Uptime in seconds")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")

    class Config:
        """Pydantic config."""
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class ContainerListResponse(BaseModel):
    """Response listing all containers."""

    containers: List[ContainerInfo] = Field(..., description="List of containers")
    total: int = Field(..., description="Total number of containers")
    running: int = Field(..., description="Number of running containers")
    stopped: int = Field(..., description="Number of stopped containers")


class LogEntry(BaseModel):
    """A single log entry."""

    timestamp: datetime = Field(..., description="Log timestamp")
    level: str = Field(..., description="Log level")
    message: str = Field(..., description="Log message")
    source: str = Field(..., description="Log source (container, agent, etc.)")

    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class LogsResponse(BaseModel):
    """Response containing container logs."""

    container_id: str = Field(..., description="Container ID")
    logs: List[LogEntry] = Field(..., description="Log entries")
    has_more: bool = Field(..., description="Whether more logs exist")


class MetricsResponse(BaseModel):
    """Container resource metrics."""

    container_id: str = Field(..., description="Container ID")
    cpu_percent: float = Field(..., description="CPU usage percentage")
    memory_usage_mb: float = Field(..., description="Memory usage in MB")
    memory_limit_mb: float = Field(..., description="Memory limit in MB")
    network_rx_bytes: int = Field(..., description="Network bytes received")
    network_tx_bytes: int = Field(..., description="Network bytes transmitted")
    uptime_seconds: int = Field(..., description="Container uptime in seconds")
    timestamp: datetime = Field(..., description="Metrics timestamp")

    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class HealthResponse(BaseModel):
    """Health check response."""

    status: Literal["healthy", "degraded", "unhealthy"] = Field(
        ..., description="Health status"
    )
    version: str = Field(..., description="Service version")
    docker_connected: bool = Field(..., description="Docker daemon connection status")
    database_connected: bool = Field(..., description="Database connection status")
    redis_connected: bool = Field(..., description="Redis connection status")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    container_count: int = Field(..., description="Current number of containers")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class ErrorResponse(BaseModel):
    """Error response model."""

    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
