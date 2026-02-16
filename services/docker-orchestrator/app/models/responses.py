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


# ============================================================================
# Analytics Response Models
# ============================================================================

class UsageDataPoint(BaseModel):
    """Single data point for usage over time."""
    date: str = Field(..., description="Date in ISO format")
    api_calls: int = Field(..., description="Number of API calls")
    tokens_used: int = Field(..., description="Number of tokens used")
    cost_usd: float = Field(..., description="Cost in USD")


class UsageStatsResponse(BaseModel):
    """Usage statistics response."""
    period_days: int = Field(..., description="Period covered in days")
    total_api_calls: int = Field(..., description="Total API calls in period")
    total_tokens_used: int = Field(..., description="Total tokens used")
    total_cost_usd: float = Field(..., description="Total estimated cost in USD")
    cost_by_provider: Dict[str, float] = Field(..., description="Cost breakdown by provider")
    tokens_by_provider: Dict[str, Dict[str, int]] = Field(
        ..., description="Token breakdown by provider (input/output)"
    )
    api_calls_by_endpoint: Dict[str, int] = Field(
        ..., description="API call count by endpoint"
    )
    daily_timeseries: List[UsageDataPoint] = Field(
        ..., description="Daily usage data"
    )


class DeploymentDataPoint(BaseModel):
    """Single data point for deployments over time."""
    date: str = Field(..., description="Date in ISO format")
    total: int = Field(..., description="Total deployments")
    successful: int = Field(..., description="Successful deployments")
    failed: int = Field(..., description="Failed deployments")
    success_rate: float = Field(..., description="Success rate percentage")


class DeploymentEvent(BaseModel):
    """A deployment event record."""
    deployment_id: Optional[str] = None
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    status: str = Field(..., description="Deployment status")
    created_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class DeploymentStatsResponse(BaseModel):
    """Deployment statistics response."""
    period_days: int = Field(..., description="Period covered in days")
    total_deployments: int = Field(..., description="Total deployments")
    successful_deployments: int = Field(..., description="Successful deployments")
    failed_deployments: int = Field(..., description="Failed deployments")
    success_rate: float = Field(..., description="Success rate percentage")
    deployments_by_status: Dict[str, int] = Field(
        ..., description="Deployment count by status"
    )
    daily_timeseries: List[DeploymentDataPoint] = Field(
        ..., description="Daily deployment data"
    )
    recent_deployments: List[DeploymentEvent] = Field(
        ..., description="Recent deployment events"
    )


class PerformanceDataPoint(BaseModel):
    """Single data point for performance over time."""
    date: str = Field(..., description="Date in ISO format")
    avg_response_time_ms: float = Field(..., description="Average response time")
    request_count: int = Field(..., description="Number of requests")


class PerformanceMetricsResponse(BaseModel):
    """Performance metrics response."""
    period_days: int = Field(..., description="Period covered in days")
    avg_response_time_ms: float = Field(..., description="Average response time")
    p50_response_time_ms: float = Field(..., description="50th percentile response time")
    p95_response_time_ms: float = Field(..., description="95th percentile response time")
    p99_response_time_ms: float = Field(..., description="99th percentile response time")
    total_requests: int = Field(..., description="Total requests measured")
    daily_timeseries: List[PerformanceDataPoint] = Field(
        ..., description="Daily performance data"
    )


class AnalyticsResponse(BaseModel):
    """Comprehensive analytics response."""
    usage: UsageStatsResponse = Field(..., description="Usage statistics")
    deployments: DeploymentStatsResponse = Field(..., description="Deployment statistics")
    performance: PerformanceMetricsResponse = Field(..., description="Performance metrics")
