"""
Request models for Docker Orchestrator API.

Pydantic models for validating incoming API requests.
"""

from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime


class DeployAgentRequest(BaseModel):
    """Request to deploy an agent to a container."""

    agent_id: str = Field(
        ...,
        description="Unique agent ID from agent generator",
        min_length=1,
        max_length=100,
    )
    agent_name: str = Field(
        ...,
        description="Human-readable agent name",
        min_length=1,
        max_length=200,
    )
    flow_code: str = Field(
        ...,
        description="Generated Python flow code",
        min_length=1,
    )
    agents_yaml: str = Field(
        ...,
        description="Agent YAML configuration",
        min_length=1,
    )
    requirements: List[str] = Field(
        default_factory=list,
        description="Python package requirements (already in base image)",
    )
    environment_vars: Dict[str, str] = Field(
        default_factory=dict,
        description="Environment variables for the container",
    )
    cpu_limit: float = Field(
        default=1.0,
        ge=0.1,
        le=4.0,
        description="CPU limit in cores",
    )
    memory_limit: str = Field(
        default="512m",
        description="Memory limit (e.g., '512m', '1g')",
    )
    auto_start: bool = Field(
        default=True,
        description="Automatically start container after creation",
    )

    @validator("memory_limit")
    def validate_memory_limit(cls, v: str) -> str:
        """Validate memory limit format."""
        import re
        if not re.match(r"^\d+[mgMG]$", v):
            raise ValueError(
                "Memory limit must be in format: <number><unit> where unit is m or g"
            )
        return v.lower()

    @validator("environment_vars")
    def validate_environment_vars(cls, v: Dict[str, str]) -> Dict[str, str]:
        """Validate environment variable names."""
        import re
        valid_key = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
        for key in v.keys():
            if not valid_key.match(key):
                raise ValueError(f"Invalid environment variable name: {key}")
        return v


class ContainerActionRequest(BaseModel):
    """Request to perform an action on a container."""

    action: Literal["start", "stop", "restart"] = Field(
        ...,
        description="Action to perform",
    )
    timeout: int = Field(
        default=10,
        ge=1,
        le=60,
        description="Timeout in seconds for stop operation",
    )
    force: bool = Field(
        default=False,
        description="Force operation (for remove)",
    )


class LogsRequest(BaseModel):
    """Request for container logs."""

    tail: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Number of lines to retrieve from the end",
    )
    since: Optional[datetime] = Field(
        default=None,
        description="Only return logs since this timestamp",
    )
    level: Optional[Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]] = Field(
        default=None,
        description="Filter by log level",
    )
    follow: bool = Field(
        default=False,
        description="Follow log output (for streaming)",
    )
