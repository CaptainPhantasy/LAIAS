"""
Database models for Agent Generator Service.

SQLAlchemy 2.0 style models for persistent storage of agents and generations.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class Agent(Base):
    """
    Agent model for storing generated agents.

    Represents a generated CrewAI agent with its code,
    configuration, and metadata.
    """

    __tablename__ = "agents"

    # === Primary Key ===
    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=lambda: f"gen_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
    )

    # === Identity ===
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # === Generated Code (Godzilla pattern) ===
    flow_code: Mapped[str] = mapped_column(Text, nullable=False)
    agents_yaml: Mapped[str | None] = mapped_column(Text)
    state_class: Mapped[str | None] = mapped_column(Text)

    # === Configuration ===
    complexity: Mapped[str] = mapped_column(String(20), nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    tools: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    requirements: Mapped[list[Any] | dict[str, Any]] = mapped_column(JSONB, default=list)

    # === Metadata ===
    llm_provider: Mapped[str] = mapped_column(String(20), default="openai")
    model: Mapped[str] = mapped_column(String(50), default="gpt-4o")
    estimated_cost_per_run: Mapped[float | None] = mapped_column(Float)
    complexity_score: Mapped[int | None] = mapped_column(Integer)

    # === Validation ===
    validation_status: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    flow_diagram: Mapped[str | None] = mapped_column(Text)

    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    latest_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # === Status ===
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    deployed_count: Mapped[int] = mapped_column(Integer, default=0)
    last_deployed: Mapped[datetime | None] = mapped_column(DateTime)

    # === Team / Ownership ===
    owner_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    team_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True
    )

    # === Timestamps ===
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "agent_id": self.id,
            "agent_name": self.name,
            "description": self.description,
            "flow_code": self.flow_code,
            "agents_yaml": self.agents_yaml,
            "state_class": self.state_class,
            "complexity": self.complexity,
            "task_type": self.task_type,
            "requirements": self.requirements,
            "llm_provider": self.llm_provider,
            "model": self.model,
            "estimated_cost_per_run": self.estimated_cost_per_run,
            "complexity_score": self.complexity_score,
            "validation_status": self.validation_status,
            "flow_diagram": self.flow_diagram,
            "version": self.version,
            "latest_version": self.latest_version,
            "is_active": self.is_active,
            "deployed_count": self.deployed_count,
            "last_deployed": self.last_deployed.isoformat() if self.last_deployed else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "owner_id": str(self.owner_id) if self.owner_id else None,
            "team_id": str(self.team_id) if self.team_id else None,
        }


class AgentVersion(Base):
    __tablename__ = "agent_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)

    flow_code: Mapped[str | None] = mapped_column(Text)
    agents_yaml: Mapped[str | None] = mapped_column(Text)
    state_class: Mapped[str | None] = mapped_column(Text)
    requirements: Mapped[list[Any] | dict[str, Any]] = mapped_column(JSONB, default=list)
    validation_status: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    flow_diagram: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    change_summary: Mapped[str | None] = mapped_column(Text)

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "version": self.version,
            "flow_code": self.flow_code,
            "agents_yaml": self.agents_yaml,
            "state_class": self.state_class,
            "requirements": self.requirements,
            "validation_status": self.validation_status,
            "flow_diagram": self.flow_diagram,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "change_summary": self.change_summary,
        }


class Generation(Base):
    """
    Generation model for tracking generation requests.

    Logs each generation attempt for analytics and debugging.
    """

    __tablename__ = "generations"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    agent_id: Mapped[str] = mapped_column(String(50), nullable=False)  # Foreign key to Agent

    # === Request Details ===
    request_description: Mapped[str] = mapped_column(Text, nullable=False)
    request_complexity: Mapped[str | None] = mapped_column(String(20))
    request_task_type: Mapped[str | None] = mapped_column(String(50))
    request_llm_provider: Mapped[str | None] = mapped_column(String(20))
    request_model: Mapped[str | None] = mapped_column(String(50))

    # === Response Details ===
    response_code: Mapped[str | None] = mapped_column(Text)
    validation_passed: Mapped[bool | None] = mapped_column(Boolean)
    pattern_compliance: Mapped[float | None] = mapped_column(Float)

    # === Timing ===
    started_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    duration_ms: Mapped[int | None] = mapped_column(Integer)

    # === Status ===
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, completed, failed
    error_message: Mapped[str | None] = mapped_column(Text)

    # === Cost Tracking ===
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    estimated_cost: Mapped[float | None] = mapped_column(Float)

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "generation_id": self.id,
            "agent_id": self.agent_id,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "validation_passed": self.validation_passed,
            "pattern_compliance": self.pattern_compliance,
            "tokens_used": self.tokens_used,
            "estimated_cost": self.estimated_cost,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
