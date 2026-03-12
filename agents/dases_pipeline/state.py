"""
================================================================================
                    DASES PIPELINE — TYPED STATE MODEL
================================================================================
Pydantic state for the DASES quality-gated multi-agent pipeline.
Follows the Godzilla pattern: typed fields, defaults, validation.
================================================================================
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class PipelinePhase(str, Enum):
    INIT = "INIT"
    REQUIREMENTS = "REQUIREMENTS"
    TECHNICAL_REVIEW = "TECHNICAL_REVIEW"
    SCAFFOLDING = "SCAFFOLDING"
    DATABASE = "DATABASE"
    IMPLEMENTATION = "IMPLEMENTATION"
    FRONTEND = "FRONTEND"
    DOCUMENTATION = "DOCUMENTATION"
    RELEASE = "RELEASE"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class AgentType(str, Enum):
    PLANNER = "PLANNER"
    THINKER = "THINKER"
    SCAFFOLDER = "SCAFFOLDER"
    DATABASE = "DATABASE"
    CODING = "CODING"
    FRONTEND = "FRONTEND"
    DOCUMENTARIAN = "DOCUMENTARIAN"
    CRITIC = "CRITIC"


class GateStatus(str, Enum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


# =============================================================================
# SUB-MODELS
# =============================================================================

class QualityGate(BaseModel):
    gate_number: int = 0
    name: str = ""
    agent: str = ""
    status: GateStatus = GateStatus.PENDING
    issues_found: int = 0
    issues_resolved: int = 0
    attempts: int = 0
    max_attempts: int = 3
    verified_at: Optional[str] = None


class VerificationReceipt(BaseModel):
    agent: str = ""
    component: str = ""
    status: str = "PENDING"
    date: str = ""
    issues_found: int = 0
    checks_passed: int = 0
    checks_total: int = 0
    details: Dict[str, Any] = Field(default_factory=dict)


class PipelineIssue(BaseModel):
    issue_id: str = ""
    severity: str = "MEDIUM"  # CRITICAL, HIGH, MEDIUM
    agent: str = ""
    description: str = ""
    location: str = ""
    fix_required: str = ""
    resolved: bool = False


# =============================================================================
# MAIN STATE CLASS
# =============================================================================

class DASESState(BaseModel):
    """
    Complete state for the DASES pipeline.

    Standard fields (Godzilla pattern):
    - task_id, status, error_count, progress, confidence

    DASES-specific fields:
    - project_name, project_description, current_agent, phase
    - artifacts (output from each agent)
    - quality_gates, verification_receipts, issues
    """

    # === Execution Identity ===
    task_id: str = Field(default="", description="Unique pipeline run identifier")

    # === Status Tracking ===
    status: str = Field(default="pending", description="Current execution status")
    error_count: int = Field(default=0, description="Total errors encountered")
    last_error: Optional[str] = Field(default=None, description="Most recent error")
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Completion %")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Result confidence")

    # === Project Identity ===
    project_name: str = Field(default="", description="Name of the project being built")
    project_description: str = Field(default="", description="User's project requirements")

    # === Pipeline Position ===
    current_agent: AgentType = Field(default=AgentType.PLANNER, description="Active agent")
    phase: PipelinePhase = Field(default=PipelinePhase.INIT, description="Current phase")

    # === Agent Artifacts ===
    # Each agent's output is stored here as it completes
    artifacts: Dict[str, str] = Field(default_factory=lambda: {
        "spec": "",
        "technical_review": "",
        "scaffolding_manifest": "",
        "database_architecture": "",
        "implementation_report": "",
        "frontend_report": "",
        "design_system": "",
        "documentation_report": "",
        "release_signoff": "",
    })

    # === Quality Gates ===
    quality_gates: List[QualityGate] = Field(default_factory=lambda: [
        QualityGate(gate_number=1, name="Requirements Quality", agent="Deep Planner"),
        QualityGate(gate_number=2, name="Technical Quality", agent="Deep Thinker"),
        QualityGate(gate_number=3, name="Build Quality", agent="Scaffolding Expert"),
        QualityGate(gate_number=4, name="Database Quality", agent="Database Specialist"),
        QualityGate(gate_number=5, name="Code Quality", agent="Coding Expert"),
        QualityGate(gate_number=6, name="Design Quality", agent="Frontend Designer"),
        QualityGate(gate_number=7, name="Documentation Quality", agent="Release Documentarian"),
    ])

    # === Verification ===
    verification_receipts: List[VerificationReceipt] = Field(default_factory=list)
    issues: List[PipelineIssue] = Field(default_factory=list)

    # === Iteration Tracking ===
    iteration_count: int = Field(default=0, description="Total critic iterations")
    max_iterations: int = Field(default=3, description="Max retries per gate")

    # === Metadata ===
    inputs: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = Field(default=None)
    updated_at: Optional[str] = Field(default=None)


# =============================================================================
# CONFIGURATION
# =============================================================================

class DASESConfig(BaseModel):
    """Configuration for the DASES pipeline."""

    # LLM Settings — defaults to GLM via ZAI
    default_model: str = Field(
        default="openai/glm-4-flash",
        description="LLM model identifier for CrewAI"
    )
    temperature: float = 0.7
    max_tokens: int = 8000

    # Execution Settings
    max_retries: int = 3
    timeout_seconds: int = 600
    memory_enabled: bool = True
    verbose: bool = True

    # Quality Thresholds
    min_test_coverage: float = 90.0
    min_lighthouse_score: int = 90
    max_critical_issues: int = 0
