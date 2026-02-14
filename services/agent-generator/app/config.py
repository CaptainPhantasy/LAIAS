"""
Configuration management for Agent Generator Service.

Uses Pydantic Settings for type-safe environment variable loading.
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # === Application ===
    app_name: str = Field(default="Agent Generator Service", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="development", description="Environment name")

    # === Server ===
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8001, description="Server port")
    reload: bool = Field(default=False, description="Enable auto-reload")

    # === API Keys ===
    ZAI_API_KEY: str = Field(default="", description="ZAI API key (default provider)")
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    ANTHROPIC_API_KEY: str = Field(default="", description="Anthropic API key")
    OPENROUTER_API_KEY: str = Field(default="", description="OpenRouter API key")
    GOOGLE_API_KEY: str = Field(default="", description="Google API key")
    MISTRAL_API_KEY: str = Field(default="", description="Mistral API key")

    # === LLM Provider Override ===
    LLM_PROVIDER: str = Field(default="zai", description="Default LLM provider")
    LLM_MODEL: str = Field(default="", description="Override default model")

    # === Database ===
    database_url: str = Field(
        default="postgresql+asyncpg://laias:laias@localhost:5432/laias",
        description="Database connection URL"
    )
    database_pool_size: int = Field(default=10, description="Database pool size")
    database_max_overflow: int = Field(default=20, description="Database max overflow")

    # === Redis ===
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis URL")
    redis_cache_ttl: int = Field(default=3600, description="Redis cache TTL in seconds")
    redis_max_connections: int = Field(default=50, description="Redis max connections")

    # === LLM Settings ===
    default_llm_provider: str = Field(default="openai", description="Default LLM provider")
    default_model: str = Field(default="gpt-4o", description="Default model")
    max_tokens: int = Field(default=8000, description="Max tokens for generation")
    temperature: float = Field(default=0.7, description="Default temperature")
    timeout_seconds: int = Field(default=120, description="LLM timeout in seconds")

    # === Generation Settings ===
    max_agents: int = Field(default=10, ge=1, le=20, description="Max agents per flow")
    default_complexity: str = Field(default="moderate", description="Default complexity level")
    enable_code_validation: bool = Field(default=True, description="Enable code validation")
    cache_enabled: bool = Field(default=True, description="Enable response caching")

    # === Security ===
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="CORS allowed origins"
    )
    api_key_header: str = Field(default="X-API-Key", description="API key header name")
    require_api_key: bool = Field(default=False, description="Require API key for all endpoints")

    # === Logging ===
    log_level: str = Field(default="INFO", description="Log level")
    log_format: str = Field(default="json", description="Log format (json or text)")
    log_file: Optional[str] = Field(default=None, description="Log file path")

    # === Monitoring ===
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_path: str = Field(default="/metrics", description="Metrics endpoint path")
    enable_tracing: bool = Field(default=False, description="Enable distributed tracing")

    # === Feature Flags ===
    enable_few_shot: bool = Field(default=True, description="Enable few-shot examples")
    enable_analytics: bool = Field(default=True, description="Enable usage analytics")
    enable_rate_limiting: bool = Field(default=False, description="Enable rate limiting")
    rate_limit_requests: int = Field(default=100, description="Rate limit per minute")

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment.lower() in ("production", "prod")

    @property
    def openai_available(self) -> bool:
        """Check if OpenAI API key is configured."""
        return bool(self.OPENAI_API_KEY and self.OPENAI_API_KEY != "sk-")

    @property
    def anthropic_available(self) -> bool:
        """Check if Anthropic API key is configured."""
        return bool(self.ANTHROPIC_API_KEY)

    @property
    def zai_available(self) -> bool:
        """Check if ZAI API key is configured."""
        return bool(self.ZAI_API_KEY)

    @property
    def openrouter_available(self) -> bool:
        """Check if OpenRouter API key is configured."""
        return bool(self.OPENROUTER_API_KEY)

    @property
    def google_available(self) -> bool:
        """Check if Google API key is configured."""
        return bool(self.GOOGLE_API_KEY)

    @property
    def mistral_available(self) -> bool:
        """Check if Mistral API key is configured."""
        return bool(self.MISTRAL_API_KEY)

    @property
    def effective_llm_provider(self) -> str:
        """Get the effective LLM provider from env or fallback to available."""
        provider_override = os.getenv("LLM_PROVIDER", "").lower()
        if provider_override:
            return provider_override

        # Fallback to ZAI if available, then OpenAI
        if self.zai_available:
            return "zai"
        if self.openai_available:
            return "openai"
        return "zai"  # Default to zai for config consistency


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
