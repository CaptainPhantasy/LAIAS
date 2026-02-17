"""
Request schemas for Agent Generator API.

Pydantic v2 models for validating incoming API requests.
"""

from datetime import datetime
from typing import Literal, Optional, Any

from pydantic import BaseModel, Field, field_validator


class GenerateAgentRequest(BaseModel):
    """
    Request to generate a CrewAI agent from natural language.

    Attributes:
        description: Natural language description of agent
        agent_name: Valid Python class name for the flow
        complexity: Complexity level affecting agent count and structure
        task_type: Primary task category for optimized generation
        tools_requested: Specific tools to include
        llm_provider: LLM provider to use
        model: Specific model override
        include_memory: Enable agent memory
        include_analytics: Include analytics service
        max_agents: Maximum number of specialized agents
    """

    description: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Natural language description of agent's purpose and behavior",
        examples=[
            "Create an agent that researches competitor pricing and generates a weekly report",
            "Build an agent that monitors API health and sends alerts to Slack"
        ]
    )

    agent_name: str = Field(
        ...,
        pattern=r"^[A-Za-z][A-Za-z0-9_]*$",
        description="Valid Python class name for the generated flow",
        examples=["CompetitorAnalysisFlow", "ApiMonitorFlow"]
    )

    complexity: Literal["simple", "moderate", "complex"] = Field(
        default="moderate",
        description="Complexity level affecting agent count and flow structure"
    )

    task_type: Literal["research", "development", "analysis", "automation", "general"] = Field(
        default="general",
        description="Primary task category for optimized generation"
    )

    tools_requested: Optional[list[str]] = Field(
        default=None,
        description="Specific tools to include (SerperDevTool, ScrapeWebsiteTool, etc.)",
        examples=[["SerperDevTool", "ScrapeWebsiteTool"]]
    )

    llm_provider: Literal["zai", "openai", "anthropic", "openrouter", "google", "mistral"] = Field(
        default="zai",
        description="LLM provider for code generation"
    )

    model: Optional[str] = Field(
        default=None,
        description="Specific model override (gpt-4o, claude-3-5-sonnet, etc.)",
        examples=["gpt-4o", "claude-3-5-sonnet-20241022"]
    )

    include_memory: bool = Field(
        default=True,
        description="Enable agent memory for context retention"
    )

    include_analytics: bool = Field(
        default=True,
        description="Include AnalyticsService for monitoring"
    )

    max_agents: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Maximum number of specialized agents to create"
    )

    @field_validator("agent_name")
    @classmethod
    def validate_agent_name(cls, v: str) -> str:
        """Ensure agent name is a valid Python identifier."""
        if not v:
            raise ValueError("Agent name cannot be empty")
        if v[0].isdigit():
            raise ValueError("Agent name must start with a letter")
        if v in ("Flow", "AgentState", "BaseModel"):
            raise ValueError(f"Agent name cannot be a reserved name: {v}")
        return v

    @field_validator("tools_requested")
    @classmethod
    def validate_tools(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """Validate tool names against known CrewAI tools."""
        if v is None:
            return v

        # Complete list of CrewAI-compatible tools supported by the frontend
        known_tools = {
            # Web & Search Tools
            "SerperDevTool",
            "DuckDuckGoSearchRun",
            "ScrapeWebsiteTool",
            "WebsiteSearchTool",
            "SeleniumScrapingTool",
            "FirecrawlScrapeWebsiteTool",
            "EXASearchTool",
            # File & Document Tools
            "FileReadTool",
            "DirectoryReadTool",
            "DirectorySearchTool",
            "CSVSearchTool",
            "JSONSearchTool",
            "XMLSearchTool",
            "PDFSearchTool",
            "DOCXSearchTool",
            "GithubSearchTool",
            # Code & Development Tools
            "CodeInterpreterTool",
            "CodeDocsSearchTool",
            "CodeSearchTool",
            "VBCodeInterpreterTool",
            # Database Tools
            "PostgreSQLTool",
            "MySQLTool",
            "SQLiteTool",
            "SnowflakeTool",
            # Communication Tools
            "EmailTool",
            "SlackTool",
            "DiscordTool",
            "TelegramTool",
            "WhatsAppTool",
            # AI & LLM Tools
            "AzureAiSearchTool",
            "ChatOllama",
            "LlamaIndexTool",
            # Cloud & Infrastructure Tools
            "AWSTool",
            "GCSTool",
            "AzureStorageTool",
            "S3Tool",
            "CloudTool",
            # Data & Analytics Tools
            "PandasTool",
            "NL2SQLTool",
            "DatabricksTool",
            # Browser Automation Tools
            "BrowserbaseLoadTool",
            "PlaywrightTool",
            "ScrapflyScrapeWebsiteTool",
            # Content & Media Tools
            "YoutubeVideoSearchTool",
            "YoutubeChannelSearchTool",
            # Utility Tools
            "BaseTool",
        }

        unknown = set(v) - known_tools
        if unknown:
            raise ValueError(f"Unknown tools requested: {unknown}")

        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "description": "Create an agent that researches market trends",
                    "agent_name": "MarketResearchFlow",
                    "complexity": "moderate",
                    "task_type": "research",
                    "include_memory": True,
                    "max_agents": 3
                }
            ]
        }
    }


class ValidateCodeRequest(BaseModel):
    """
    Request to validate Python code against Godzilla pattern.

    Attributes:
        code: Python code to validate
        check_pattern_compliance: Enable pattern compliance checking
        check_syntax: Enable syntax validation
    """

    code: str = Field(
        ...,
        min_length=10,
        description="Python code to validate"
    )

    check_pattern_compliance: bool = Field(
        default=True,
        description="Check compliance with Godzilla architectural pattern"
    )

    check_syntax: bool = Field(
        default=True,
        description="Perform Python syntax validation"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "code": "class MyFlow(Flow[AgentState]):\n    @start()\n    async def begin(self):\n        pass",
                    "check_pattern_compliance": True
                }
            ]
        }
    }


class AgentListRequest(BaseModel):
    """Request to list saved agents with filtering."""

    limit: int = Field(default=50, ge=1, le=200, description="Maximum results to return")
    offset: int = Field(default=0, ge=0, description="Results offset for pagination")
    task_type: Optional[Literal["research", "development", "analysis", "automation", "general"]] = Field(
        default=None,
        description="Filter by task type"
    )
    complexity: Optional[Literal["simple", "moderate", "complex"]] = Field(
        default=None,
        description="Filter by complexity"
    )
    search: Optional[str] = Field(
        default=None,
        min_length=2,
        description="Search in description and name"
    )


class AgentUpdateRequest(BaseModel):
    """Request to update a saved agent."""

    description: Optional[str] = Field(
        default=None,
        min_length=10,
        max_length=5000,
        description="Updated description"
    )

    is_active: Optional[bool] = Field(
        default=None,
        description="Whether agent is active"
    )

    tags: Optional[list[str]] = Field(
        default=None,
        description="Updated tags"
    )

    version_notes: Optional[str] = Field(
        default=None,
        description="Notes about this version"
    )
