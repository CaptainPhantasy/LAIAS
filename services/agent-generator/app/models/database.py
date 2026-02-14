"""
Database models for Agent Generator Service.

SQLAlchemy models for persistent storage of agents and generations.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Agent(Base):
    """
    Agent model for storing generated agents.

    Represents a generated CrewAI agent with its code,
    configuration, and metadata.
    """

    __tablename__ = "agents"

    # === Primary Key ===
    id = Column(String(50), primary_key=True, default=lambda: f"gen_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")

    # === Identity ===
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)

    # === Generated Code (Godzilla pattern) ===
    flow_code = Column(Text, nullable=False)
    agents_yaml = Column(Text)
    state_class = Column(Text)

    # === Configuration ===
    complexity = Column(String(20), nullable=False)
    task_type = Column(String(50), nullable=False)
    tools = Column(JSONB, default=list)
    requirements = Column(JSONB, default=list)

    # === Metadata ===
    llm_provider = Column(String(20), default="openai")
    model = Column(String(50), default="gpt-4o")
    estimated_cost_per_run = Column(Float)
    complexity_score = Column(Integer)

    # === Validation ===
    validation_status = Column(JSONB, default=dict)
    flow_diagram = Column(Text)

    # === Status ===
    is_active = Column(Boolean, default=True)
    deployed_count = Column(Integer, default=0)
    last_deployed = Column(DateTime)

    # === Timestamps ===
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "agent_id": self.id,
            "agent_name": self.name,
            "description": self.description,
            "flow_code": self.flow_code,
            "agents_yaml": self.agents_yaml,
            "complexity": self.complexity,
            "task_type": self.task_type,
            "llm_provider": self.llm_provider,
            "model": self.model,
            "estimated_cost_per_run": self.estimated_cost_per_run,
            "complexity_score": self.complexity_score,
            "validation_status": self.validation_status,
            "flow_diagram": self.flow_diagram,
            "is_active": self.is_active,
            "deployed_count": self.deployed_count,
            "last_deployed": self.last_deployed.isoformat() if self.last_deployed else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Generation(Base):
    """
    Generation model for tracking generation requests.

    Logs each generation attempt for analytics and debugging.
    """

    __tablename__ = "generations"

    id = Column(String(50), primary_key=True)
    agent_id = Column(String(50), nullable=False)  # Foreign key to Agent

    # === Request Details ===
    request_description = Column(Text, nullable=False)
    request_complexity = Column(String(20))
    request_task_type = Column(String(50))
    request_llm_provider = Column(String(20))
    request_model = Column(String(50))

    # === Response Details ===
    response_code = Column(Text)
    validation_passed = Column(Boolean)
    pattern_compliance = Column(Float)

    # === Timing ===
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_ms = Column(Integer)

    # === Status ===
    status = Column(String(20), default="pending")  # pending, completed, failed
    error_message = Column(Text)

    # === Cost Tracking ===
    tokens_used = Column(Integer)
    estimated_cost = Column(Float)

    def to_dict(self) -> dict:
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
