"""
Database models for persistent storage.

These models would be used if orchestrator needs to persist
deployment records. For now, Docker labels provide the source of truth.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Integer, Float, Text, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class DeploymentRecord(Base):
    """
    Persistent record of an agent deployment.

    This table stores deployment metadata for auditing and
    tracking container lifecycle beyond Docker's own records.
    """

    __tablename__ = "deployments"

    id = Column(String, primary_key=True)  # UUID
    agent_id = Column(String, index=True, nullable=False)
    agent_name = Column(String, nullable=False)
    container_id = Column(String, index=True)
    container_name = Column(String)

    # Configuration
    cpu_limit = Column(Float, default=1.0)
    memory_limit = Column(String, default="512m")
    environment_vars = Column(JSON)

    # Status tracking
    status = Column(String, default="created")  # created, running, stopped, error
    auto_start = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime)
    stopped_at = Column(DateTime)

    # Code storage path
    code_path = Column(String)

    # Relationships
    logs = relationship("DeploymentLog", back_populates="deployment", cascade="all, delete-orphan")


class DeploymentLog(Base):
    """
    Individual log entries for deployments.

    Allows querying logs without accessing container logs.
    Useful for audit trails and offline analysis.
    """

    __tablename__ = "deployment_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    deployment_id = Column(String, ForeignKey("deployments.id"), index=True)

    # Log entry
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(String, index=True)  # DEBUG, INFO, WARNING, ERROR
    message = Column(Text)
    source = Column(String)  # flow, agent, system

    deployment = relationship("DeploymentRecord", back_populates="logs")
