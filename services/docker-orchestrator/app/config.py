"""
Configuration management for Docker Orchestrator.

Uses pydantic-settings for type-safe configuration with environment variables.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # -----------------------------------------------------------------------------
    # Service Configuration
    # -----------------------------------------------------------------------------
    APP_NAME: str = Field(default="LAIAS Docker Orchestrator", description="Application name")
    APP_VERSION: str = Field(default="0.1.0", description="Application version")
    SERVICE_NAME: str = Field(default="docker-orchestrator", description="Service name")
    SERVICE_VERSION: str = Field(default="1.0.0", description="Service version")
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Log format (json or console)")

    # -----------------------------------------------------------------------------
    # API Configuration
    # -----------------------------------------------------------------------------
    API_HOST: str = Field(default="0.0.0.0", description="API bind host")
    API_PORT: int = Field(default=8002, description="API bind port")
    API_PREFIX: str = Field(default="/api", description="API route prefix")
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="CORS allowed origins"
    )

    # -----------------------------------------------------------------------------
    # Docker Configuration
    # -----------------------------------------------------------------------------
    DOCKER_HOST: Optional[str] = Field(
        default=None,
        description="Docker daemon socket URL (None for default)"
    )
    DOCKER_NETWORK: str = Field(
        default="laias-network",
        description="Docker network for agent containers"
    )
    AGENT_IMAGE_BASE: str = Field(
        default="laias/agent-runner:latest",
        description="Base image for agent containers"
    )
    AGENT_CODE_PATH: str = Field(
        default="/var/laias/agents",
        description="Path to store generated agent code"
    )
    CONTAINER_PREFIX: str = Field(
        default="laias-agent-",
        description="Prefix for container names"
    )

    # -----------------------------------------------------------------------------
    # Container Configuration
    # -----------------------------------------------------------------------------
    DEFAULT_CPU_LIMIT: float = Field(
        default=1.0,
        ge=0.1,
        le=4.0,
        description="Default CPU limit per container"
    )
    DEFAULT_MEMORY_LIMIT: str = Field(
        default="512m",
        description="Default memory limit per container"
    )
    CONTAINER_STOP_TIMEOUT: int = Field(
        default=10,
        ge=1,
        le=60,
        description="Seconds to wait before force stopping container"
    )
    MAX_CONTAINERS: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of concurrent agent containers"
    )

    # -----------------------------------------------------------------------------
    # Database Configuration
    # -----------------------------------------------------------------------------
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://laias:laias_secure_password@localhost:5432/laias",
        description="Database connection URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=10, ge=1, description="Database pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, ge=0, description="Database max overflow")

    # -----------------------------------------------------------------------------
    # Redis Configuration
    # -----------------------------------------------------------------------------
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    REDIS_STREAM_CHANNEL: str = Field(
        default="laias:logs",
        description="Redis pub/sub channel for log streaming"
    )

    # -----------------------------------------------------------------------------
    # Monitoring Configuration
    # -----------------------------------------------------------------------------
    METRICS_ENABLED: bool = Field(
        default=True,
        description="Enable Prometheus metrics endpoint"
    )
    METRICS_PATH: str = Field(
        default="/metrics",
        description="Prometheus metrics endpoint path"
    )
    HEALTH_CHECK_INTERVAL: int = Field(
        default=30,
        ge=5,
        description="Health check interval in seconds"
    )

    # -----------------------------------------------------------------------------
    # Security Configuration
    # -----------------------------------------------------------------------------
    SECRET_KEY: str = Field(
        default="change-this-in-production",
        description="Secret key for signing tokens"
    )
    API_KEY_HEADER: str = Field(
        default="X-API-Key",
        description="Header name for API key authentication"
    )
    API_KEYS: List[str] = Field(
        default=[],
        description="Valid API keys (empty = disabled)"
    )

    @validator("AGENT_CODE_PATH")
    def validate_agent_code_path(cls, v: str) -> str:
        """Ensure agent code path is absolute."""
        import os
        if not os.path.isabs(v):
            raise ValueError(f"AGENT_CODE_PATH must be absolute: {v}")
        return v

    @validator("DEFAULT_MEMORY_LIMIT")
    def validate_memory_limit(cls, v: str) -> str:
        """Validate memory limit format."""
        import re
        if not re.match(r"^\d+[mg]$", v.lower()):
            raise ValueError(f"Invalid memory limit format: {v}")
        return v.lower()


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Dependency injection helper for settings."""
    return settings
