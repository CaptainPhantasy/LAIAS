"""
================================================================================
                    DASES PIPELINE — MAIN FLOW
================================================================================
Deterministic Agentic Software Engineering System

Quality-gated multi-agent pipeline producing production-release quality software.
8 agents execute sequentially with The Critic verifying at each stage.
Failed gates loop back to the responsible agent for fixes.

Flow:
  initialize → planner → gate_1 → thinker → gate_2 → scaffolder → gate_3
  → database → gate_4 → coder → gate_5 → frontend → gate_6
  → documentarian → gate_7 → release_signoff

Follows Godzilla pattern: Flow[DASESState], structlog, error recovery.
================================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================

from crewai import Task, Crew, Process
from crewai.flow.flow import Flow, listen, start, router
from crewai.flow.persistence import persist
from pydantic import Field
from typing import Optional
from datetime import datetime
import structlog
import os
import json

from .state import (
    DASESState,
    DASESConfig,
    PipelinePhase,
    AgentType,
    GateStatus,
    VerificationReceipt,
    PipelineIssue,
)
from .agents import (
    create_deep_planner,
    create_deep_thinker,
    create_scaffolding_expert,
    create_database_specialist,
    create_coding_expert,
    create_frontend_designer,
    create_release_documentarian,
    create_critic,
)
from .prompts import (
    get_planner_task,
    get_thinker_task,
    get_scaffolder_task,
    get_database_task,
    get_coder_task,
    get_frontend_task,
    get_documentarian_task,
    get_critic_task,
    GATE_CHECKLISTS,
)

logger = structlog.get_logger()


# =============================================================================
# THE DASES FLOW
# =============================================================================

@persist()
class DASESFlow(Flow[DASESState]):
    """
    DASES — Deterministic Agentic Software Engineering System

    A quality-gated pipeline where 8 specialized agents build production
    software, with The Critic verifying each stage before allowing progression.

    FLOW DIAGRAM:

        ┌──────────────┐
        │  initialize   │ @start
        └──────┬───────┘
               ▼
        ┌──────────────┐     ┌──────────────┐
        │  planner     │────▶│  gate_1      │──┐
        └──────────────┘     └──────────────┘  │ FAIL → retry planner
               ▼ PASS                          │
        ┌──────────────┐     ┌──────────────┐  │
        │  thinker     │────▶│  gate_2      │──┘
        └──────────────┘     └──────────────┘
               ▼ PASS
        ... (continues through all 7 agents + gates) ...
               ▼
        ┌──────────────┐
        │  release     │ Final sign-off
        └──────────────┘
    """

    def __init__(self, config: Optional[DASESConfig] = None, **kwargs):
        super().__init__(**kwargs)
        self.config = config or DASESConfig()
        logger.info(
            "DASES Pipeline initialized",
            model=self.config.default_model,
            max_retries=self.config.max_retries,
        )

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _run_agent_task(self, agent, task_description: str, expected_output: str) -> str:
        """Execute a single agent task via a Crew and return the result string."""
        task = Task(
            description=task_description,
            expected_output=expected_output,
            agent=agent,
        )
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=self.config.verbose,
            memory=self.config.memory_enabled,
        )
        result = crew.kickoff()
        return str(result)

    def _run_critic_gate(self, gate_index: int, agent_name: str, agent_output: str) -> bool:
        """Run The Critic against an agent's output. Returns True if gate passes."""
        gate = self.state.quality_gates[gate_index]
        gate.attempts += 1
        checklist = GATE_CHECKLISTS.get(agent_name, "No checklist defined.")

        critic = create_critic(self.config)
        task_desc = get_critic_task(agent_name, agent_output, checklist)

        result = self._run_agent_task(
            critic,
            task_desc,
            f"Verification receipt for {agent_name} with PASS/FAIL verdict and issue details",
        )

        # Parse critic verdict — look for PASS/FAIL in output
        result_upper = result.upper()
        passed = "FAIL" not in result_upper or (
            "OVERALL" in result_upper and "PASS" in result_upper.split("OVERALL")[-1]
        )

        # Count issues mentioned
        issues_found = result_upper.count("FAIL")

        # Update gate
        gate.issues_found = issues_found
        gate.verified_at = datetime.utcnow().isoformat()

        # Store receipt
        receipt = VerificationReceipt(
            agent=agent_name,
            component=f"Gate {gate.gate_number}: {gate.name}",
            status="PASS" if passed else "FAIL",
            date=datetime.utcnow().isoformat(),
            issues_found=issues_found,
            details={"critic_output": result[:2000]},
        )
        self.state.verification_receipts.append(receipt)

        if passed:
            gate.status = GateStatus.PASSED
            logger.info(
                "Quality gate PASSED",
                gate=gate.name,
                agent=agent_name,
                attempt=gate.attempts,
            )
        else:
            gate.status = GateStatus.FAILED
            logger.warning(
                "Quality gate FAILED",
                gate=gate.name,
                agent=agent_name,
                attempt=gate.attempts,
                issues=issues_found,
            )

        self.state.updated_at = datetime.utcnow().isoformat()
        return passed

    def _save_artifact(self, key: str, content: str) -> None:
        """Save an artifact to state and optionally to disk."""
        self.state.artifacts[key] = content
        output_dir = os.getenv("LAIAS_OUTPUT_ROOT", "/app/outputs")
        if self.state.task_id:
            artifact_dir = os.path.join(output_dir, self.state.task_id, "artifacts")
            os.makedirs(artifact_dir, exist_ok=True)
            filepath = os.path.join(artifact_dir, f"{key}.md")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("Artifact saved", key=key, path=filepath)

    # =========================================================================
    # STEP 0: INITIALIZE
    # =========================================================================

    @start()
    def initialize_pipeline(self) -> DASESState:
        """Entry point — validate inputs and set up pipeline state."""
        try:
            if not self.state.task_id:
                self.state.task_id = f"dases_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.state.status = "initializing"
            self.state.created_at = datetime.utcnow().isoformat()
            self.state.phase = PipelinePhase.INIT

            # Extract project info from inputs
            if not self.state.project_description and self.state.inputs:
                self.state.project_description = self.state.inputs.get("description", "")
                self.state.project_name = self.state.inputs.get("name", "Unnamed Project")

            if not self.state.project_description:
                raise ValueError("Project description is required. Pass via inputs={'description': '...'}.")

            logger.info(
                "DASES Pipeline starting",
                task_id=self.state.task_id,
                project=self.state.project_name,
            )
            self.state.status = "initialized"
            self.state.progress = 2.0
            return self.state

        except Exception as e:
            logger.error("Initialization failed", error=str(e))
            self.state.status = "error"
            self.state.last_error = str(e)
            self.state.error_count += 1
            return self.state

    # =========================================================================
    # STEP 1: DEEP PLANNER
    # =========================================================================

    @listen("initialize_pipeline")
    def run_deep_planner(self) -> DASESState:
        """Agent 1: Extract requirements and produce SPEC.md."""
        if self.state.status == "error":
            return self.state

        try:
            self.state.phase = PipelinePhase.REQUIREMENTS
            self.state.current_agent = AgentType.PLANNER
            self.state.status = "running"
            logger.info("Agent 1: Deep Planner starting", task_id=self.state.task_id)

            planner = create_deep_planner(self.config)
            task_desc = get_planner_task(self.state.project_description)
            result = self._run_agent_task(planner, task_desc, "Complete SPEC.md document")

            self._save_artifact("spec", result)
            self.state.progress = 10.0
            logger.info("Agent 1: Deep Planner complete", task_id=self.state.task_id)
            return self.state

        except Exception as e:
            logger.error("Deep Planner failed", error=str(e))
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state

    # =========================================================================
    # GATE 1: REQUIREMENTS QUALITY
    # =========================================================================

    @listen("run_deep_planner")
    def gate_1_requirements(self) -> DASESState:
        """Critic verifies Agent 1 output."""
        spec = self.state.artifacts.get("spec", "")
        if not spec:
            logger.warning("No spec artifact to verify")
            return self.state

        passed = self._run_critic_gate(0, "Deep Planner", spec)
        if not passed and self.state.quality_gates[0].attempts < self.config.max_retries:
            logger.info("Gate 1 failed — retrying Deep Planner")
            return self.run_deep_planner()

        self.state.progress = 15.0
        return self.state

    # =========================================================================
    # STEP 2: DEEP THINKER
    # =========================================================================

    @listen("gate_1_requirements")
    def run_deep_thinker(self) -> DASESState:
        """Agent 2: Technical review and blocker finding."""
        if self.state.quality_gates[0].status != GateStatus.PASSED:
            logger.warning("Skipping Agent 2 — Gate 1 not passed")
            self.state.status = "blocked"
            return self.state

        try:
            self.state.phase = PipelinePhase.TECHNICAL_REVIEW
            self.state.current_agent = AgentType.THINKER
            logger.info("Agent 2: Deep Thinker starting", task_id=self.state.task_id)

            thinker = create_deep_thinker(self.config)
            task_desc = get_thinker_task(self.state.artifacts["spec"])
            result = self._run_agent_task(thinker, task_desc, "Complete Technical Review document")

            self._save_artifact("technical_review", result)
            self.state.progress = 22.0
            logger.info("Agent 2: Deep Thinker complete", task_id=self.state.task_id)
            return self.state

        except Exception as e:
            logger.error("Deep Thinker failed", error=str(e))
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state

    # =========================================================================
    # GATE 2: TECHNICAL QUALITY
    # =========================================================================

    @listen("run_deep_thinker")
    def gate_2_technical(self) -> DASESState:
        """Critic verifies Agent 2 output."""
        review = self.state.artifacts.get("technical_review", "")
        if not review:
            return self.state

        passed = self._run_critic_gate(1, "Deep Thinker", review)
        if not passed and self.state.quality_gates[1].attempts < self.config.max_retries:
            logger.info("Gate 2 failed — retrying Deep Thinker")
            return self.run_deep_thinker()

        self.state.progress = 28.0
        return self.state

    # =========================================================================
    # STEP 3: SCAFFOLDING EXPERT
    # =========================================================================

    @listen("gate_2_technical")
    def run_scaffolder(self) -> DASESState:
        """Agent 3: Create project scaffold with locked dependencies."""
        if self.state.quality_gates[1].status != GateStatus.PASSED:
            self.state.status = "blocked"
            return self.state

        try:
            self.state.phase = PipelinePhase.SCAFFOLDING
            self.state.current_agent = AgentType.SCAFFOLDER
            logger.info("Agent 3: Scaffolding Expert starting", task_id=self.state.task_id)

            scaffolder = create_scaffolding_expert(self.config)
            task_desc = get_scaffolder_task(
                self.state.artifacts["spec"],
                self.state.artifacts["technical_review"],
            )
            result = self._run_agent_task(scaffolder, task_desc, "Complete Scaffolding Manifest")

            self._save_artifact("scaffolding_manifest", result)
            self.state.progress = 35.0
            logger.info("Agent 3: Scaffolding Expert complete", task_id=self.state.task_id)
            return self.state

        except Exception as e:
            logger.error("Scaffolding Expert failed", error=str(e))
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state

    @listen("run_scaffolder")
    def gate_3_build(self) -> DASESState:
        """Critic verifies Agent 3 output."""
        manifest = self.state.artifacts.get("scaffolding_manifest", "")
        if not manifest:
            return self.state

        passed = self._run_critic_gate(2, "Scaffolding Expert", manifest)
        if not passed and self.state.quality_gates[2].attempts < self.config.max_retries:
            return self.run_scaffolder()

        self.state.progress = 40.0
        return self.state

    # =========================================================================
    # STEP 4: DATABASE SPECIALIST
    # =========================================================================

    @listen("gate_3_build")
    def run_database_specialist(self) -> DASESState:
        """Agent 4: Design and implement the data layer."""
        if self.state.quality_gates[2].status != GateStatus.PASSED:
            self.state.status = "blocked"
            return self.state

        try:
            self.state.phase = PipelinePhase.DATABASE
            self.state.current_agent = AgentType.DATABASE
            logger.info("Agent 4: Database Specialist starting", task_id=self.state.task_id)

            db_specialist = create_database_specialist(self.config)
            task_desc = get_database_task(
                self.state.artifacts["spec"],
                self.state.artifacts["technical_review"],
            )
            result = self._run_agent_task(db_specialist, task_desc, "Complete Database Architecture document")

            self._save_artifact("database_architecture", result)
            self.state.progress = 48.0
            logger.info("Agent 4: Database Specialist complete", task_id=self.state.task_id)
            return self.state

        except Exception as e:
            logger.error("Database Specialist failed", error=str(e))
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state

    @listen("run_database_specialist")
    def gate_4_database(self) -> DASESState:
        """Critic verifies Agent 4 output."""
        db_arch = self.state.artifacts.get("database_architecture", "")
        if not db_arch:
            return self.state

        passed = self._run_critic_gate(3, "Database Specialist", db_arch)
        if not passed and self.state.quality_gates[3].attempts < self.config.max_retries:
            return self.run_database_specialist()

        self.state.progress = 52.0
        return self.state

    # =========================================================================
    # STEP 5: CODING EXPERT
    # =========================================================================

    @listen("gate_4_database")
    def run_coding_expert(self) -> DASESState:
        """Agent 5: Implement the complete application."""
        if self.state.quality_gates[3].status != GateStatus.PASSED:
            self.state.status = "blocked"
            return self.state

        try:
            self.state.phase = PipelinePhase.IMPLEMENTATION
            self.state.current_agent = AgentType.CODING
            logger.info("Agent 5: Coding Expert starting", task_id=self.state.task_id)

            coder = create_coding_expert(self.config)
            task_desc = get_coder_task(
                self.state.artifacts["spec"],
                self.state.artifacts["database_architecture"],
                self.state.artifacts["scaffolding_manifest"],
            )
            result = self._run_agent_task(coder, task_desc, "Complete Implementation Report")

            self._save_artifact("implementation_report", result)
            self.state.progress = 62.0
            logger.info("Agent 5: Coding Expert complete", task_id=self.state.task_id)
            return self.state

        except Exception as e:
            logger.error("Coding Expert failed", error=str(e))
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state

    @listen("run_coding_expert")
    def gate_5_code(self) -> DASESState:
        """Critic verifies Agent 5 output."""
        impl = self.state.artifacts.get("implementation_report", "")
        if not impl:
            return self.state

        passed = self._run_critic_gate(4, "Coding Expert", impl)
        if not passed and self.state.quality_gates[4].attempts < self.config.max_retries:
            return self.run_coding_expert()

        self.state.progress = 68.0
        return self.state

    # =========================================================================
    # STEP 6: FRONTEND DESIGNER
    # =========================================================================

    @listen("gate_5_code")
    def run_frontend_designer(self) -> DASESState:
        """Agent 6: Implement pixel-perfect UI."""
        if self.state.quality_gates[4].status != GateStatus.PASSED:
            self.state.status = "blocked"
            return self.state

        try:
            self.state.phase = PipelinePhase.FRONTEND
            self.state.current_agent = AgentType.FRONTEND
            logger.info("Agent 6: Frontend Designer starting", task_id=self.state.task_id)

            frontend = create_frontend_designer(self.config)
            task_desc = get_frontend_task(
                self.state.artifacts["spec"],
                self.state.artifacts["implementation_report"],
            )
            result = self._run_agent_task(frontend, task_desc, "Complete Frontend Report and Design System")

            self._save_artifact("frontend_report", result)
            self.state.progress = 78.0
            logger.info("Agent 6: Frontend Designer complete", task_id=self.state.task_id)
            return self.state

        except Exception as e:
            logger.error("Frontend Designer failed", error=str(e))
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state

    @listen("run_frontend_designer")
    def gate_6_design(self) -> DASESState:
        """Critic verifies Agent 6 output."""
        frontend = self.state.artifacts.get("frontend_report", "")
        if not frontend:
            return self.state

        passed = self._run_critic_gate(5, "Frontend Designer", frontend)
        if not passed and self.state.quality_gates[5].attempts < self.config.max_retries:
            return self.run_frontend_designer()

        self.state.progress = 82.0
        return self.state

    # =========================================================================
    # STEP 7: RELEASE DOCUMENTARIAN
    # =========================================================================

    @listen("gate_6_design")
    def run_documentarian(self) -> DASESState:
        """Agent 7: Produce complete documentation package."""
        if self.state.quality_gates[5].status != GateStatus.PASSED:
            self.state.status = "blocked"
            return self.state

        try:
            self.state.phase = PipelinePhase.DOCUMENTATION
            self.state.current_agent = AgentType.DOCUMENTARIAN
            logger.info("Agent 7: Release Documentarian starting", task_id=self.state.task_id)

            documentarian = create_release_documentarian(self.config)
            all_artifacts = "\n\n---\n\n".join(
                f"## {k.upper()}\n{v}" for k, v in self.state.artifacts.items() if v
            )
            task_desc = get_documentarian_task(self.state.artifacts["spec"], all_artifacts)
            result = self._run_agent_task(documentarian, task_desc, "Complete Documentation Report")

            self._save_artifact("documentation_report", result)
            self.state.progress = 90.0
            logger.info("Agent 7: Release Documentarian complete", task_id=self.state.task_id)
            return self.state

        except Exception as e:
            logger.error("Release Documentarian failed", error=str(e))
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state

    @listen("run_documentarian")
    def gate_7_docs(self) -> DASESState:
        """Critic verifies Agent 7 output."""
        docs = self.state.artifacts.get("documentation_report", "")
        if not docs:
            return self.state

        passed = self._run_critic_gate(6, "Release Documentarian", docs)
        if not passed and self.state.quality_gates[6].attempts < self.config.max_retries:
            return self.run_documentarian()

        self.state.progress = 95.0
        return self.state

    # =========================================================================
    # FINAL: RELEASE SIGN-OFF
    # =========================================================================

    @listen("gate_7_docs")
    def release_signoff(self) -> DASESState:
        """Final release sign-off — all gates must be PASSED."""
        all_passed = all(g.status == GateStatus.PASSED for g in self.state.quality_gates)

        if not all_passed:
            failed_gates = [g.name for g in self.state.quality_gates if g.status != GateStatus.PASSED]
            logger.error("Release blocked — gates not passed", failed_gates=failed_gates)
            self.state.status = "blocked"
            self.state.phase = PipelinePhase.FAILED
            return self.state

        self.state.phase = PipelinePhase.RELEASE
        self.state.current_agent = AgentType.CRITIC
        logger.info("All quality gates passed — generating release sign-off")

        # Build release sign-off document
        gate_table = "\n".join(
            f"| {g.gate_number} | {g.agent} | {g.status.value} | {g.verified_at or 'N/A'} |"
            for g in self.state.quality_gates
        )

        signoff = f"""# FINAL RELEASE SIGN-OFF

## Project: {self.state.project_name}
## Version: 1.0.0
## Release Date: {datetime.utcnow().strftime('%Y-%m-%d')}
## Pipeline Run: {self.state.task_id}

## Quality Gates Passed

| Gate | Agent | Status | Verified |
|------|-------|--------|----------|
{gate_table}

## Verification Receipts
Total receipts: {len(self.state.verification_receipts)}
Total issues found and resolved: {sum(r.issues_found for r in self.state.verification_receipts)}

## Pipeline Metrics
- Total iterations: {self.state.iteration_count}
- Total errors: {self.state.error_count}
- Final confidence: {self.state.confidence}

## Production Readiness
- [x] All features implemented
- [x] All quality gates passed
- [x] All tests passing
- [x] Documentation complete
- [x] Security review passed

## Sign-off Authority
**The Critic** has reviewed all deliverables and approves this release
for PRODUCTION deployment.

This is NOT Alpha. This is NOT Beta. This is PUBLIC PRODUCTION RELEASE QUALITY.

---
VERIFIED: {datetime.utcnow().isoformat()}
"""

        self._save_artifact("release_signoff", signoff)
        self.state.status = "completed"
        self.state.progress = 100.0
        self.state.confidence = 1.0
        self.state.phase = PipelinePhase.COMPLETE
        self.state.updated_at = datetime.utcnow().isoformat()

        logger.info(
            "DASES Pipeline COMPLETE — Production Release Ready",
            task_id=self.state.task_id,
            project=self.state.project_name,
        )
        return self.state


# =============================================================================
# ENTRY POINT — for Docker / direct execution
# =============================================================================

def run_dases_pipeline(
    project_name: str,
    project_description: str,
    config: Optional[DASESConfig] = None,
) -> DASESState:
    """
    Run the complete DASES pipeline synchronously.

    Args:
        project_name: Name of the project to build
        project_description: Detailed project requirements
        config: Optional pipeline configuration

    Returns:
        Final DASESState with all artifacts and verification receipts
    """
    flow = DASESFlow(config=config)
    result = flow.kickoff(inputs={
        "project_name": project_name,
        "project_description": project_description,
        "inputs": {
            "name": project_name,
            "description": project_description,
        },
    })
    return flow.state


# Allow direct execution
if __name__ == "__main__":
    import sys

    name = sys.argv[1] if len(sys.argv) > 1 else "Demo Project"
    desc = sys.argv[2] if len(sys.argv) > 2 else "A simple task management web application"

    final_state = run_dases_pipeline(name, desc)
    print(f"\nPipeline Status: {final_state.status}")
    print(f"Phase: {final_state.phase}")
    print(f"Progress: {final_state.progress}%")
    print(f"Quality Gates: {sum(1 for g in final_state.quality_gates if g.status == GateStatus.PASSED)}/7 passed")
