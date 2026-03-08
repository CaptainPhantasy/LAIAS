"""
Request models for Docker Orchestrator API.

Pydantic models for validating incoming API requests.
"""

import os
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


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
    requirements: list[str] = Field(
        default_factory=list,
        description="Python package requirements (already in base image)",
    )
    environment_vars: dict[str, str] = Field(
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
    output_config: dict[str, bool] = Field(
        default_factory=lambda: {"postgres": True, "files": True},
        description="Per-deployment output routing destinations",
    )
    output_path: str | None = Field(
        default=None,
        description="User-chosen output directory path",
    )
    output_format: str = Field(
        default="markdown",
        description="Output format: markdown or html",
    )
    input_volumes: list[dict[str, str]] = Field(
        default_factory=list,
        description="Read-only host directories to mount into the agent container. "
        "Each entry: {host_path: '/path/on/host', container_path: '/data/input'}",
    )

    @field_validator("input_volumes")
    @classmethod
    def validate_input_volumes(cls, v: list[dict[str, str]]) -> list[dict[str, str]]:
        for vol in v:
            if "host_path" not in vol or "container_path" not in vol:
                raise ValueError("Each input_volume must have 'host_path' and 'container_path'")
            if not os.path.isabs(vol["host_path"]):
                raise ValueError(f"host_path must be absolute: {vol['host_path']}")
            if not os.path.isabs(vol["container_path"]):
                raise ValueError(f"container_path must be absolute: {vol['container_path']}")
            if ".." in vol["host_path"].split(os.sep) or ".." in vol["container_path"].split(
                os.sep
            ):
                raise ValueError("Paths must not contain '..' components")
        return v

    @field_validator("memory_limit")
    @classmethod
    def validate_memory_limit(cls, v: str) -> str:
        """Validate memory limit format."""
        import re

        if not re.match(r"^\d+[mgMG]$", v):
            raise ValueError("Memory limit must be in format: <number><unit> where unit is m or g")
        return v.lower()

    @field_validator("environment_vars")
    @classmethod
    def validate_environment_vars(cls, v: dict[str, str]) -> dict[str, str]:
        """Validate environment variable names."""
        import re

        valid_key = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
        for key in v.keys():
            if not valid_key.match(key):
                raise ValueError(f"Invalid environment variable name: {key}")
        return v

    @field_validator("output_config")
    @classmethod
    def validate_output_config(cls, v: dict[str, bool]) -> dict[str, bool]:
        allowed_destinations = {"postgres", "files"}
        unknown_destinations = set(v.keys()) - allowed_destinations
        if unknown_destinations:
            unknown_list = ", ".join(sorted(unknown_destinations))
            raise ValueError(f"Unknown output destinations: {unknown_list}")

        normalized = {"postgres": False, "files": False}
        normalized.update(v)
        if not any(normalized.values()):
            raise ValueError("At least one output destination must be enabled")
        return normalized

    @field_validator("output_format")
    @classmethod
    def validate_output_format(cls, v: str) -> str:
        """Validate output format is markdown or html."""
        if v not in {"markdown", "html"}:
            raise ValueError(f"output_format must be 'markdown' or 'html', got '{v}'")
        return v

    @field_validator("output_path")
    @classmethod
    def validate_output_path(cls, v: str | None) -> str | None:
        """Validate output path is absolute and safe."""
        if v is not None:
            if not os.path.isabs(v):
                raise ValueError("output_path must be an absolute path")
            if ".." in v.split(os.sep):
                raise ValueError("output_path must not contain '..' components")
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
    since: datetime | None = Field(
        default=None,
        description="Only return logs since this timestamp",
    )
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] | None = Field(
        default=None,
        description="Filter by log level",
    )
    follow: bool = Field(
        default=False,
        description="Follow log output (for streaming)",
    )


class OutputEventIngestRequest(BaseModel):
    run_id: str = Field(..., min_length=1, max_length=120)
    event_type: str = Field(..., min_length=1, max_length=120)
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")
    message: str = Field(..., min_length=1)
    source: str = Field(default="agent", min_length=1, max_length=120)
    payload: dict[str, object] = Field(default_factory=dict)
    destinations: dict[str, bool] | None = Field(default=None)
    timestamp: datetime | None = Field(default=None)
