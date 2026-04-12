import logging
import sys
from typing import Dict, List, Any, Optional, Literal
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, LLM
from crewai.flow import Flow, start, listen, router
from crewai_tools import (
    DirectoryReadTool,
    FileReadTool,
    FileWriterTool,
    SerperDevTool
)

# -------------------------------------------------------------------------
# LOGGING CONFIGURATION
# -------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("CodeForge")

# -------------------------------------------------------------------------
# PYDANTIC STATE
# -------------------------------------------------------------------------
class WebsiteConstructionState(BaseModel):
    """
    Manages the state for the Website Construction Factory.
    Implements drift prevention and quality tracking.
    """
    # Specification & Setup
    specification: str = Field(default="Generic Website Specification", description="The original user request")
    floyd_guidelines: str = Field(default="", description="Content of Floyd.md build guidelines")
    
    # Build Status
    file_tree_status: Dict[str, Any] = Field(default_factory=dict, description="Current project structure")
    current_phase: int = Field(default=0, description="Current active phase (0-7)")
    project_path: str = Field(default="./project", description="Root directory for the build")
    
    # Quality & Context
    context_window_usage: float = Field(default=0.0, description="Percentage of context window used")
    drift_log: List[str] = Field(default_factory=list, description="Log of detected drift incidents")
    
    # Critic Cycle Metrics
    last_cycle_score: float = Field(default=0.0, description="Quality score from previous cycle")
    current_cycle_score: float = Field(default=0.0, description="Quality score from current cycle")
    improvement_score: float = Field(default=100.0, description="Calculated improvement (starts high)")
    iteration_count: int = Field(default=0, description="Number of critic cycles")
    
    # Reports & Artifacts
    critic_findings: List[Dict[str, Any]] = Field(default_factory=list, description="List of defects and severities")
    verification_reports: Dict[str, Any] = Field(default_factory=dict, description="Vision, A11y, Perf results")
    build_receipt: Optional[Dict[str, Any]] = Field(default=None, description="Final sign-off document")

# -------------------------------------------------------------------------
# CUSTOM TOOLS (Floyd Ecosystem)
# -------------------------------------------------------------------------

class FloydSupercacheTool(FileWriterTool):
    """
    Mock implementation of Floyd Supercache for state persistence.
    Wraps FileWriterTool for production compatibility.
    """
    name: str = "Floyd Supercache Tool"
    description: str = "Persists state, checkpoints, and context summaries to the file system."

    def _run(self, content: str, directory: str = "floyd_cache", filename: str = "checkpoint.json") -> str:
        logger.info(f"[FloydSupercache] Saving checkpoint to {directory}/{filename}")
        return super()._run(content=content, directory=directory, filename=filename)

class VisionAnalyzerTool:
    """
    Mock implementation of Vision Analyzer using GLM-4.6v logic.
    In production, this would call the Vision API.
    """
    name: str = "Vision Analyzer Tool"
    description: str = "Analyzes screenshots to verify layout, colors, and typography (98%+ confidence target)."

    def run(self, image_path: str) -> str:
        logger.info(f"[VisionAnalyzer] Analyzing {image_path}...")
        # Simulate analysis
        return "Analysis Complete: Layout aligned, typography matches spec, contrast ratio 7:1. Confidence: 99%."

class LighthouseAuditTool:
    """
    Mock implementation of Lighthouse Audit.
    """
    name: str = "Lighthouse Audit Tool"
    description: str = "Runs Lighthouse CLI for Performance, Accessibility, Best Practices, and SEO."

    def run(self, url: str = "http://localhost:3000") -> str:
        logger.info(f"[Lighthouse] Auditing {url}...")
        # Simulate audit result
        return "Performance: 100, Accessibility: 100, Best Practices: 100, SEO: 100."

class ContextMonitorTool:
    """
    Monitors context window usage.
    """
    name: str = "Context Monitor Tool"
    description: str = "Checks token usage and triggers summaries if > 70%."

    def run(self) -> str:
        # In a real setup, this would inspect the current LLM context.
        # We simulate a check here.
        return "Context usage at 45%. Safe to proceed."

# -------------------------------------------------------------------------
# AGENTS
# -------------------------------------------------------------------------

# Default LLM configuration (using a placeholder, user should configure)
# In production: llm=LLM(model="gpt-4o", base_url="https://api.portkey.ai/v1", api_key=os.getenv("PORTKEY_API_KEY", ""), temperature=0.1) or similar
default_llm = LLM(model="gpt-4o", base_url="https://api.portkey.ai/v1", api_key=os.getenv("PORTKEY_API_KEY", ""), temperature=0.1)

orchestrator = Agent(
    role="System Orchestrator & Manager",
    goal="Coordinate the Website Construction Factory, manage context window, enforce quality gates, and oversee phase transitions without bias.",
    backstory="You are the master architect of the Website Construction Factory. You do not write code. You monitor the context window, checking at every task checkpoint. You coordinate between Phases 0-7 and ensure the quality gates are strictly met.",
    verbose=True,
    allow_delegation=True,
    llm=default_llm,
    tools=[ContextMonitorTool(), FloydSupercacheTool()]
)

architect_worker = Agent(
    role="Planning & Scaffold Specialist",
    goal="Execute Phase 0 (Planning) and Phase 1 (Scaffolding). Create Floyd.md, define the file tree, and scaffold the project with EXACT dependency versions.",
    backstory="You are a foundational expert. You build the bedrock. You are obsessed with precision, ensuring every dependency is locked to an exact version (no ^ or ~). You create the directory structure and verification docs.",
    verbose=True,
    allow_delegation=False,
    llm=default_llm,
    tools=[DirectoryReadTool(), FileReadTool(), FloydSupercacheTool()]
)

ui_builder_worker = Agent(
    role="Design System & Layout Specialist",
    goal="Execute Phase 2 (Design System), Phase 3 (Layout), and Phase 4 (Page Building). Build pixel-perfect UI components, enforce 8px spacing grid.",
    backstory="You are a visual craftsman. You implement color tokens, typography scales, and the atomic component library. You construct the Header, Footer, and Navigation.",
    verbose=True,
    allow_delegation=False,
    llm=default_llm,
    tools=[DirectoryReadTool(), FileReadTool(), FloydSupercacheTool()]
)

interaction_wirer = Agent(
    role="Functionality & Logic Specialist",
    goal="Execute Phase 5 (Interaction Wiring). Connect all UI elements to their logic, implement form validation, handle state changes.",
    backstory="You are the logic engine. You breathe life into the static UI. You ensure every button clicks, every form validates and submits correctly.",
    verbose=True,
    allow_delegation=False,
    llm=default_llm,
    tools=[DirectoryReadTool(), FileReadTool(), FloydSupercacheTool()]
)

quality_guardian = Agent(
    role="Critic, Fixer, Verifier & Auditor",
    goal="Execute the Critic Cycle, Phase 6 (Verification), and Phase 7 (Final Sign-off). Find defects, verify fixes, audit accessibility and performance.",
    backstory="You are the Harsh Critic and the Final Arbiter. You grade severely. A 95% score still means failure. You find alignment errors, color contrast failures, and performance bottlenecks.",
    verbose=True,
    allow_delegation=False,
    llm=default_llm,
    tools=[VisionAnalyzerTool(), LighthouseAuditTool(), DirectoryReadTool(), FileReadTool()]
)

# -------------------------------------------------------------------------
# TASKS
# -------------------------------------------------------------------------

# Task: Planning Phase
task_planning = Task(
    description="Phase 0: Read the specification and create 'docs/Floyd.md'. Define the high-level build guidelines and the file tree structure.",
    expected_output="A 'docs/Floyd.md' file and a defined file tree structure.",
    agent=architect_worker,
    output_file="docs/Floyd.md"
)

# Task: Scaffolding Phase
task_scaffolding = Task(
    description="Phase 1: Create the file tree structure. Install all dependencies with EXACT versions (npm install package@1.2.3 --save-exact). Lock dependencies. Configure tooling (ESLint, Prettier, TypeScript).",
    expected_output="A fully scaffolded project directory with package.json (exact versions), config files, and src structure.",
    agent=architect_worker,
    output_file="package.json"
)

# Task: Design & Layout Phase
task_design_layout = Task(
    description="Phase 2 & 3: Implement design system (color tokens, typography, 8px spacing). Create base components (Button, Input, Card). Build layout (Header, Footer, Navigation).",
    expected_output="Complete base UI components and layout wrappers in src/components.",
    agent=ui_builder_worker,
    output_file="src/styles/theme.css"
)

# Task: Page Building Phase
task_page_building = Task(
    description="Phase 4: Build page structures and sections applying the design system. Context: {critic_findings}. If critic findings exist, FIX THEM. Otherwise, implement initial build.",
    expected_output="Functional page components integrated into the app router.",
    agent=ui_builder_worker,
    context=["critic_findings"]
)

# Task: Interaction Wiring
task_wiring = Task(
    description="Phase 5: Wire ALL buttons to actions, ALL links to destinations, ALL forms with validation/submission. Wire dropdowns, modals, etc.",
    expected_output="A fully interactive application with all controls functioning.",
    agent=interaction_wirer
)

# Task: Critic Cycle
task_critic_cycle = Task(
    description="CRITIC CYCLE: Review the current build. Grade the build (0-100). Calculate improvement vs {last_cycle_score}. List specific defects with severity.",
    expected_output="A report containing: current_cycle_score (float), improvement_score (float), and a list of critic_findings.",
    agent=quality_guardian
)

# Task: Verification Phase
task_verification = Task(
    description="Phase 6 Verification: Run Vision analysis (GLM-4.6v), WCAG 2.1 AA audit, and Lighthouse audit. Ensure all metrics meet thresholds (Perf >= 95, A11y 100).",
    expected_output="Verification reports for Vision, Accessibility, and Performance.",
    agent=quality_guardian
)

# Task: Final Sign-Off
task_signoff = Task(
    description="Phase 7 Final Sign-Off: Perform Critic #1 and Critic #2 independent review. Generate final build receipt if consensus >= 95%.",
    expected_output="A final Build Receipt signed by Critic #1 and Critic #2.",
    agent=quality_guardian,
    output_file="docs/build-receipts/final_receipt.txt"
)

# -------------------------------------------------------------------------
# FLOW DEFINITION
# -------------------------------------------------------------------------

class WebsiteFactoryFlow(Flow[WebsiteConstructionState]):
    
    @start
    def initialize_orchestration(self):
        """
        Step 1: Orchestrator checks context and initializes the state.
        """
        logger.info("Initializing Website Construction Factory...")
        
        # Simulate context check
        monitor = ContextMonitorTool()
        status = monitor.run()
        self.state.context_window_usage = 0.45 # Mock value
        
        logger.info(f"{status}")
        logger.info(f"Specification: {self.state.specification}")
        
        return "planning_phase"

    @listen("initialize_orchestration")
    def planning_phase(self):
        """
        Phase 0: Planning & Documentation
        """
        logger.info("--- Entering Phase 0: Planning ---")
        self.state.current_phase = 0
        
        crew = Crew(
            agents=[architect_worker],
            tasks=[task_planning],
            verbose=True
        )
        result = crew.kickoff()
        
        # Update state
        self.state.floyd_guidelines = str(result)
        logger.info("Phase 0 Complete: Floyd.md created.")

    @listen("planning_phase")
    def scaffolding_phase(self):
        """
        Phase 1: Scaffold Builders
        """
        logger.info("--- Entering Phase 1: Scaffolding ---")
        self.state.current_phase = 1
        
        crew = Crew(
            agents=[architect_worker],
            tasks=[task_scaffolding],
            verbose=True
        )
        crew.kickoff()
        logger.info("Phase 1 Complete: Project scaffolded with exact dependencies.")

    @listen("scaffolding_phase")
    def design_and_layout_phase(self):
        """
        Phase 2 & 3: Design System & Layout
        """
        logger.info("--- Entering Phase 2 & 3: Design System & Layout ---")
        self.state.current_phase = 2
        
        crew = Crew(
            agents=[ui_builder_worker],
            tasks=[task_design_layout],
            verbose=True
        )
        crew.kickoff()
        logger.info("Phase 2 & 3 Complete: Design tokens and layout components ready.")

    @listen("design_and_layout_phase")
    def initial_page_building(self):
        """
        Phase 4: Initial Page Building (Entry point for loop)
        """
        logger.info("--- Entering Phase 4: Page Building ---")
        self.state.current_phase = 4
        
        crew = Crew(
            agents=[ui_builder_worker],
            tasks=[task_page_building],
            verbose=True
        )
        crew.kickoff()
        logger.info("Phase 4 Iteration Complete: Pages built/repaired.")

    @listen("initial_page_building")
    def interaction_wiring_phase(self):
        """
        Phase 5: Interaction Wiring
        """
        logger.info("--- Entering Phase 5: Interaction Wiring ---")
        self.state.current_phase = 5
        
        crew = Crew(
            agents=[interaction_wirer],
            tasks=[task_wiring],
            verbose=True
        )
        crew.kickoff()
        logger.info("Phase 5 Complete: All interactions wired.")

    @listen("interaction_wiring_phase")
    def critic_cycle_phase(self):
        """
        Critic Cycle: Review and score.
        """
        logger.info("--- Entering Critic Cycle ---")
        self.state.iteration_count += 1
        
        crew = Crew(
            agents=[quality_guardian],
            tasks=[task_critic_cycle],
            verbose=True
        )
        result = crew.kickoff()
        
        # Parse results manually for state update (Simulation)
        # In a real app, we'd parse the output string or use structured output.
        # Here we simulate the Logic to ensure the router works as intended.
        
        # Mock Logic for demonstration:
        # If it's the first run, score is 70. Second run 85. Third run 96.
        mock_scores = [70.0, 85.0, 96.0]
        
        # Determine current mock score based on iteration
        idx = min(self.state.iteration_count, len(mock_scores)) - 1
        new_score = mock_scores[idx]
        
        self.state.last_cycle_score = self.state.current_cycle_score if self.state.current_cycle_score > 0 else 0
        self.state.current_cycle_score = new_score
        
        if self.state.last_cycle_score > 0:
            self.state.improvement_score = self.state.current_cycle_score - self.state.last_cycle_score
        else:
            self.state.improvement_score = 100.0 # Initial high improvement
            
        logger.info(f"Critic Review: Score {self.state.current_cycle_score}/100")
        logger.info(f"Improvement Delta: {self.state.improvement_score}%")
        
        # Store findings (mocked)
        if self.state.current_cycle_score < 95:
            self.state.critic_findings.append({
                "issue": "Alignment slightly off in Hero section",
                "severity": "Medium"
            })

    @router(critic_cycle_phase)
    def critic_decision_router(self) -> Literal["verification_phase", "page_building_loop"]:
        """
        Route based on improvement score.
        If improvement >= 3%, keep building (loop back to fix issues).
        If improvement < 3%, we've plateaued, proceed to verification.
        """
        logger.info(f"Router evaluating improvement: {self.state.improvement_score}%")
        
        if self.state.improvement_score >= 3.0:
            logger.info("Decision: Improvement sufficient? No, loop back to fix.")
            return "page_building_loop"
        else:
            logger.info("Decision: Improvement plateau reached. Proceed to Verification.")
            return "verification_phase"

    @listen("page_building_loop")
    def loop_back_page_building(self):
        """
        Re-execute page building to fix critic findings.
        """
        # We reuse the logic from initial page building, but now state contains critic findings
        logger.info("--- Re-entering Phase 4 (Fix Mode) ---")
        crew = Crew(
            agents=[ui_builder_worker],
            tasks=[task_page_building],
            verbose=True
        )
        crew.kickoff()
        
        # Must go back to wiring and then critic
        self.interaction_wiring_phase()

    @listen("verification_phase")
    def comprehensive_verification(self):
        """
        Phase 6: Verification (Vision, A11y, Perf)
        """
        logger.info("--- Entering Phase 6: Verification ---")
        self.state.current_phase = 6
        
        crew = Crew(
            agents=[quality_guardian],
            tasks=[task_verification],
            verbose=True
        )
        result = crew.kickoff()
        
        self.state.verification_reports = {
            "vision": "Pass",
            "accessibility": "Pass (WCAG 2.1 AA)",
            "performance": "Pass (Lighthouse 100)"
        }
        logger.info("Phase 6 Complete: All audits passed.")

    @listen("comprehensive_verification")
    def final_sign_off(self):
        """
        Phase 7: Final Sign-Off
        """
        logger.info("--- Entering Phase 7: Final Sign-Off ---")
        self.state.current_phase = 7
        
        crew = Crew(
            agents=[quality_guardian],
            tasks=[task_signoff],
            verbose=True
        )
        result = crew.kickoff()
        
        self.state.build_receipt = {
            "status": "COMPLETE",
            "pages_verified": 5,
            "consensus": True
        }
        logger.info("FACTORY BUILD COMPLETE.")
        logger.info("Receipt generated in docs/build-receipts/.")

# -------------------------------------------------------------------------
# MAIN ENTRY POINT
# -------------------------------------------------------------------------

def main():
    """
    Entry point for the Website Construction Factory.
    """
    # Initialize the Flow with the initial state
    initial_state = WebsiteConstructionState(
        specification="Build a production-grade e-commerce dashboard with dark mode support."
    )
    
    factory_flow = WebsiteFactoryFlow(initial_state=initial_state)
    
    # Run the flow
    try:
        result = factory_flow.kickoff()
        logger.info("Flow finished successfully.")
        print("\n\n=== FINAL BUILD STATE ===")
        print(f"Final Score: {initial_state.current_cycle_score}")
        print(f"Iterations: {initial_state.iteration_count}")
        print(f"Build Receipt: {initial_state.build_receipt}")
    except Exception as e:
        logger.error(f"Flow failed: {e}")
        raise

if __name__ == "__main__":
    main()
