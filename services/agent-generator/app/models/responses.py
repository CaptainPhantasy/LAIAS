"""
Response schemas for Agent Generator API.

Pydantic v2 models for API responses.
"""

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

# =============================================================================
# Common Components
# =============================================================================


class AgentInfo(BaseModel):
    """Information about a generated agent."""

    role: str = Field(..., description="Agent role (e.g., 'Senior Research Analyst')")
    goal: str = Field(..., description="Agent's primary goal")
    tools: list[str] = Field(default_factory=list, description="Tools assigned to this agent")
    llm_config: dict[str, Any] = Field(default_factory=dict, description="LLM configuration")
    backstory: str | None = Field(default=None, description="Agent backstory")


class ValidationResult(BaseModel):
    """Validation result for generated code."""

    is_valid: bool = Field(..., description="Whether code passes validation")
    syntax_errors: list[str] = Field(default_factory=list, description="Syntax errors found")
    pattern_compliance: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        validation_alias="pattern_compliance_score",
        description="Pattern compliance score (0.0 to 1.0)",
    )
    warnings: list[str] = Field(default_factory=list, description="Non-critical warnings")
    suggestions: list[str] = Field(default_factory=list, description="Improvement suggestions")
    missing_patterns: list[str] = Field(
        default_factory=list, description="Required patterns not found"
    )


# =============================================================================
# Main Responses
# =============================================================================


class GenerateAgentResponse(BaseModel):
    """
    Response from agent generation endpoint.

    Contains complete generated code, configuration, and metadata.
    """

    # === Identity ===
    agent_id: str = Field(..., description="Unique identifier for this generation")
    agent_name: str = Field(..., description="Name of generated flow class")
    version: str = Field(default="1.0.0", description="Generated code version")

    # === Generated Code (Godzilla pattern) ===
    flow_code: str = Field(..., description="Complete flow.py content")
    agents_yaml: str = Field(..., description="agents.yaml configuration")
    state_class: str = Field(..., description="AgentState class definition")

    # === Dependencies ===
    requirements: list[str] = Field(
        default_factory=lambda: ["crewai[tools]>=0.80.0", "pydantic>=2.5.0", "structlog>=24.1.0"],
        description="Python packages needed",
    )

    # === Metadata ===
    estimated_cost_per_run: float = Field(
        ..., ge=0.0, description="Estimated LLM cost in USD per run"
    )
    complexity_score: int = Field(..., ge=1, le=10, description="Complexity score (1-10)")

    # === Agent Details ===
    agents_created: list[AgentInfo] = Field(
        default_factory=list, description="Details of created agents"
    )
    tools_included: list[str] = Field(
        default_factory=list, description="Tools included in the flow"
    )

    # === Visualization ===
    flow_diagram: str | None = Field(default=None, description="Mermaid diagram showing the flow")

    # === Validation ===
    validation_status: ValidationResult = Field(
        default_factory=lambda: ValidationResult(is_valid=False),
        description="Code validation results",
    )

    # === Timestamps ===
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Generation timestamp"
    )
    expires_at: datetime | None = Field(default=None, description="Cache expiration")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "agent_id": "gen_20260214_042255_abc123",
                    "agent_name": "MarketResearchFlow",
                    "flow_code": "# Complete Python code here...",
                    "estimated_cost_per_run": 0.15,
                    "complexity_score": 5,
                }
            ]
        }
    }


class ValidateCodeResponse(BaseModel):
    """Response from code validation endpoint."""

    is_valid: bool = Field(..., description="Whether code passes validation")
    syntax_errors: list[str] = Field(default_factory=list, description="Syntax errors found")
    pattern_compliance_score: float = Field(
        ..., ge=0.0, le=1.0, description="Pattern compliance score"
    )
    missing_patterns: list[str] = Field(
        default_factory=list, description="Required patterns not found"
    )
    suggestions: list[str] = Field(default_factory=list, description="Improvement suggestions")
    warnings: list[str] = Field(default_factory=list, description="Non-critical warnings")
    validated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class HealthResponse(BaseModel):
    """Health check response."""

    status: Literal["healthy", "degraded", "unhealthy"] = Field(
        ..., description="Overall service health status"
    )
    version: str = Field(..., description="Service version")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")

    # === Component Status ===
    llm_status: dict[str, str] = Field(
        default_factory=dict, description="LLM provider status (openai, anthropic)"
    )
    database_status: str = Field(..., description="Database connection status")
    redis_status: str = Field(..., description="Redis connection status")

    # === Metrics ===
    total_generated: int = Field(default=0, description="Total agents generated")
    cache_hit_rate: float = Field(default=0.0, description="Cache hit rate")

    # === Timestamp ===
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AgentListResponse(BaseModel):
    """Response listing saved agents."""

    agents: list[dict[str, Any]] = Field(default_factory=list, description="List of agents")
    total: int = Field(..., description="Total count")
    limit: int = Field(..., description="Results limit")
    offset: int = Field(..., description="Results offset")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "agents": [
                        {
                            "agent_id": "gen_20260214_042255_abc123",
                            "agent_name": "MarketResearchFlow",
                            "description": "Research competitor pricing",
                            "created_at": "2026-02-14T04:22:55Z",
                        }
                    ],
                    "total": 1,
                    "limit": 50,
                    "offset": 0,
                }
            ]
        }
    }


class AgentDetailResponse(BaseModel):
    """Detailed response for a single agent."""

    agent_id: str = Field(..., description="Unique identifier")
    agent_name: str = Field(..., description="Flow class name")
    description: str = Field(..., description="Original description")

    # === Code ===
    flow_code: str = Field(..., description="Generated flow code")
    agents_yaml: str = Field(..., description="Agents configuration")

    # === Metadata ===
    complexity: str = Field(..., description="Complexity level")
    task_type: str = Field(..., description="Task category")
    llm_provider: str = Field(..., description="LLM used for generation")
    model: str = Field(..., description="Model used")

    # === Status ===
    is_active: bool = Field(default=True, description="Whether agent is active")
    deployed_count: int = Field(default=0, description="Times deployed")
    last_deployed: datetime | None = Field(default=None, description="Last deployment time")

    # === Timestamps ===
    created_at: datetime = Field(..., description="Creation time")
    updated_at: datetime | None = Field(default=None, description="Last update time")


class AgentVersionResponse(BaseModel):
    id: int | None = Field(default=None, description="Version row ID")
    agent_id: str = Field(..., description="Agent identifier")
    version: int = Field(..., description="Version number")
    flow_code: str = Field(..., description="Generated flow code for this version")
    agents_yaml: str | None = Field(default=None, description="Agents YAML for this version")
    state_class: str | None = Field(default=None, description="State class code for this version")
    requirements: list[Any] | dict[str, Any] = Field(
        default_factory=list, description="Requirements for this version"
    )
    validation_status: dict[str, Any] = Field(
        default_factory=dict, description="Validation status for this version"
    )
    flow_diagram: str | None = Field(default=None, description="Flow diagram for this version")
    created_at: datetime | None = Field(default=None, description="Version creation timestamp")
    change_summary: str | None = Field(default=None, description="Summary of changes")
    is_current: bool = Field(default=False, description="Whether this is current agent version")


class AgentVersionListResponse(BaseModel):
    agent_id: str = Field(..., description="Agent identifier")
    current_version: int = Field(..., description="Current version number")
    latest_version: int = Field(..., description="Latest version number")
    versions: list[AgentVersionResponse] = Field(
        default_factory=list, description="Version history"
    )


class AgentRollbackResponse(BaseModel):
    agent_id: str = Field(..., description="Agent identifier")
    from_version: int = Field(..., description="Version before rollback")
    rolled_back_to_version: int = Field(..., description="Historical version used for rollback")
    new_version: int = Field(..., description="New current version after rollback")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: str | None = Field(default=None, description="Detailed error information")
    request_id: str | None = Field(default=None, description="Request ID for tracing")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


# =============================================================================
# Utility Models
# =============================================================================


class CostEstimate(BaseModel):
    """Cost estimation for agent execution."""

    estimated_cost_usd: float = Field(..., description="Estimated cost in USD")
    token_estimate: int = Field(..., description="Estimated token usage")
    api_call_estimate: int = Field(..., description="Estimated API calls")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Estimation confidence")


class TemplateInfo(BaseModel):
    """Information about available templates."""

    template_name: str = Field(..., description="Template identifier")
    description: str = Field(..., description="Template description")
    task_types: list[str] = Field(..., description="Compatible task types")
    complexity: str = Field(..., description="Best suited complexity")
    agent_count_range: tuple[int, int] = Field(..., description="Min/max agents")
