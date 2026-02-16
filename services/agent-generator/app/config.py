"""
Configuration management for Agent Generator Service.

Uses Pydantic Settings for type-safe environment variable loading.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env path relative to this config file's location
# This ensures .env is found regardless of where uvicorn is invoked from
CONFIG_DIR = Path(__file__).parent.parent  # app/config.py -> services/agent-generator
ENV_FILE_PATH = CONFIG_DIR / ".env"


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
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
    PORTKEY_API_KEY: str = Field(default="", description="Portkey API key for gateway access")
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    ANTHROPIC_API_KEY: str = Field(default="", description="Anthropic API key")
    OPENROUTER_API_KEY: str = Field(default="", description="OpenRouter API key")
    GOOGLE_API_KEY: str = Field(default="", description="Google API key")
    MISTRAL_API_KEY: str = Field(default="", description="Mistral API key")

    # === LLM Provider Override ===
    LLM_PROVIDER: str = Field(default="portkey", description="Default LLM provider")
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
    default_llm_provider: str = Field(default="zai", description="Default LLM provider")
    default_model: str = Field(default="glm-5", description="Default model")
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

    # === Tool Integration Settings ===
    # Web Scraping
    SERPER_API_KEY: str = Field(default="", description="Serper API key for Google search")
    FIRECRAWL_API_KEY: str = Field(default="", description="Firecrawl API key for web scraping")
    BROWSERBASE_API_KEY: str = Field(default="", description="Browserbase API key")
    EXA_API_KEY: str = Field(default="", description="Exa AI search API key")
    TAVILY_API_KEY: str = Field(default="", description="Tavily AI search API key")

    # Database Tools
    MYSQL_HOST: str = Field(default="", description="MySQL host")
    MYSQL_USER: str = Field(default="", description="MySQL user")
    MYSQL_PASSWORD: str = Field(default="", description="MySQL password")
    MYSQL_DATABASE: str = Field(default="", description="MySQL database")
    MONGODB_URI: str = Field(default="", description="MongoDB connection URI")
    QDRANT_URL: str = Field(default="", description="Qdrant vector DB URL")
    QDRANT_API_KEY: str = Field(default="", description="Qdrant API key")
    WEAVIATE_URL: str = Field(default="", description="Weaviate vector DB URL")
    WEAVIATE_API_KEY: str = Field(default="", description="Weaviate API key")
    PINECONE_API_KEY: str = Field(default="", description="Pinecone API key")
    PINECONE_ENVIRONMENT: str = Field(default="", description="Pinecone environment")

    # Cloud Services
    AWS_ACCESS_KEY_ID: str = Field(default="", description="AWS access key ID")
    AWS_SECRET_ACCESS_KEY: str = Field(default="", description="AWS secret access key")
    AWS_REGION: str = Field(default="us-east-1", description="AWS region")
    AZURE_STORAGE_CONNECTION_STRING: str = Field(default="", description="Azure storage connection string")
    GOOGLE_APPLICATION_CREDENTIALS: str = Field(default="", description="Google Cloud credentials path")

    # Automation Tools
    APIFY_API_KEY: str = Field(default="", description="Apify API key")
    COMPOSIO_API_KEY: str = Field(default="", description="Composio API key")
    MULTION_API_KEY: str = Field(default="", description="MultiOn API key")

    # Integration Tools
    GITHUB_TOKEN: str = Field(default="", description="GitHub personal access token")
    SLACK_BOT_TOKEN: str = Field(default="", description="Slack bot token")
    DISCORD_BOT_TOKEN: str = Field(default="", description="Discord bot token")
    NOTION_API_KEY: str = Field(default="", description="Notion integration token")
    JIRA_API_TOKEN: str = Field(default="", description="Jira API token")
    JIRA_EMAIL: str = Field(default="", description="Jira account email")
    JIRA_DOMAIN: str = Field(default="", description="Jira domain")
    HUBSPOT_API_KEY: str = Field(default="", description="HubSpot API key")
    STRIPE_API_KEY: str = Field(default="", description="Stripe API key")

    # Tool Configuration
    tools_enabled: bool = Field(default=True, description="Enable tool integration")
    mcp_servers_enabled: bool = Field(default=True, description="Enable MCP server connections")
    tool_timeout: int = Field(default=60, description="Default tool execution timeout")
    max_tools_per_agent: int = Field(default=20, description="Maximum tools per agent")

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
    def portkey_available(self) -> bool:
        """Check if Portkey API key is configured."""
        return bool(self.PORTKEY_API_KEY)

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

        # Fallback to ZAI if available (preferred for GLM-5), then Portkey, then OpenAI
        if self.zai_available:
            return "zai"
        if self.portkey_available:
            return "portkey"
        if self.openai_available:
            return "openai"
        return "zai"  # Default to ZAI for GLM-5


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
