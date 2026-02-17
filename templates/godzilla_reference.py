"""
================================================================================
                        G O D Z I L L A   P R I M A L
                     "From the Depths, I Rise to Command"
================================================================================

                              ███████╗ ██████╗ ██╗
                              ╚══███╔╝██╔═══██╗██║
                                ███╔╝ ██║   ██║██║
                               ███╔╝  ██║   ██║██║
                              ███████╗╚██████╔╝███████╗
                              ╚══════╝ ╚═════╝ ╚══════╝

                          HERO IMAGE: /godzilla-hero.jpg
                     The Supreme Operator of the LAIAS Platform

================================================================================
GODZILLA TEMPLATE - GOLD STANDARD REFERENCE FOR LAIAS CODE GENERATION
================================================================================

This is the AUTHORITATIVE architectural pattern that ALL generated agents MUST follow.
The LAIAS Agent Generator API uses this template as the basis for code generation.

HERO IMAGE: Display /godzilla-hero.jpg on all pages referencing Godzilla agents.

ARCHITECTURE OVERVIEW:
---------------------
- Flow-based architecture using CrewAI Flow[AgentState]
- Typed state management with Pydantic BaseModel
- Event-driven transitions using decorators (@start, @listen, @router)
- Agent factory pattern for specialized agent creation
- Comprehensive error handling with recovery paths
- Built-in analytics and monitoring

DEPLOYMENT NOTE (CRITICAL):
--------------------------
This code is designed for the "No-Build" deployment strategy:
- Runs inside the pre-built `laias/agent-runner:latest` Docker image
- Code is mounted as a volume (NOT baked into image)
- All dependencies are pre-installed in the base image

Author: Jim (Architecture Correction)
Date: February 11, 2026
Version: 1.0
================================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# All these packages are pre-installed in laias/agent-runner:latest

from crewai import Agent, Task, Crew, Process, LLM
from crewai.flow.flow import Flow, listen, start, router, or_
from crewai.flow.persistence import persist
from crewai_tools import (
    SerperDevTool,      # Web search
    ScrapeWebsiteTool,  # Web scraping
    DirectoryReadTool,  # Read directories
    FileReadTool,       # Read files
    CodeInterpreterTool # Execute code
)
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog
import os

# =============================================================================
# LOGGING SETUP
# =============================================================================
# Always use structlog for consistent, structured logging

logger = structlog.get_logger()

# =============================================================================
# FEATURE FLAGS - Check tool availability
# =============================================================================
# Some tools may not be available in all environments

try:
    from crewai_tools import SerperDevTool
    CREWAI_TOOLS_AVAILABLE = True
except ImportError:
    CREWAI_TOOLS_AVAILABLE = False
    logger.warning("crewai_tools not available - using fallback tools")


# =============================================================================
# SECTION 1: TYPED STATE CLASS
# =============================================================================
# The state class MUST:
# - Extend Pydantic BaseModel
# - Define all fields with types and defaults
# - Include standard fields: task_id, status, error_count, progress
#
# Why Pydantic?
# - Type validation at runtime
# - Automatic serialization/deserialization
# - Clear schema documentation

class AgentState(BaseModel):
    """
    Typed state for the agent flow.
    
    This state object is:
    - Passed between flow methods
    - Persisted across restarts (with @persist decorator)
    - Validated by Pydantic on every mutation
    
    Standard fields every state should have:
    - task_id: Unique identifier for this execution
    - status: Current state (pending, running, completed, failed)
    - error_count: Number of errors encountered (for retry logic)
    - progress: Percentage complete (0.0 to 100.0)
    - confidence: Confidence in results (0.0 to 1.0)
    """
    
    # === Execution Identity ===
    task_id: str = Field(default="", description="Unique task identifier")
    
    # === Status Tracking ===
    status: str = Field(default="pending", description="Current execution status")
    # Valid statuses: pending, initializing, running, completed, failed, paused
    
    # === Error Handling ===
    error_count: int = Field(default=0, description="Number of errors encountered")
    last_error: Optional[str] = Field(default=None, description="Most recent error message")
    
    # === Progress Tracking ===
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Completion percentage")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Result confidence score")
    
    # === Task-Specific Data ===
    # Add fields specific to your agent's domain
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Original inputs")
    intermediate_results: Dict[str, Any] = Field(default_factory=dict, description="Work in progress")
    final_results: Dict[str, Any] = Field(default_factory=dict, description="Completed outputs")
    
    # === Metadata ===
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    created_at: Optional[str] = Field(default=None, description="ISO timestamp of creation")
    updated_at: Optional[str] = Field(default=None, description="ISO timestamp of last update")


# =============================================================================
# SECTION 2: CONFIGURATION CLASS (Optional but Recommended)
# =============================================================================
# Centralize configuration for easy customization

class AgentConfig(BaseModel):
    """Configuration for the agent flow."""
    
    # LLM Settings
    default_model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 4000
    
    # Execution Settings
    max_retries: int = 3
    timeout_seconds: int = 300
    memory_enabled: bool = True
    verbose: bool = True
    
    # Resource Limits
    max_concurrent_tasks: int = 5
    cost_limit_usd: float = 10.0


# =============================================================================
# SECTION 3: ANALYTICS SERVICE
# =============================================================================
# Track execution metrics for monitoring and billing

class AnalyticsService:
    """
    Simple analytics tracking for agent execution.
    
    In production, this would integrate with:
    - Prometheus/Grafana for metrics
    - DataDog/New Relic for APM
    - Custom billing systems
    """
    
    def __init__(self):
        self.session_id: Optional[str] = None
        self.metrics: Dict[str, Any] = {
            "total_cost": 0.0,
            "api_calls": 0,
            "tokens_used": 0,
            "start_time": None,
            "end_time": None
        }
    
    def start_session(self, task_id: str) -> None:
        """Start tracking a new execution session."""
        self.session_id = task_id
        self.metrics["start_time"] = datetime.utcnow().isoformat()
        logger.info("Analytics session started", task_id=task_id)
    
    def record_api_call(self, cost: float = 0.0, tokens: int = 0) -> None:
        """Record an API call with associated costs."""
        self.metrics["api_calls"] += 1
        self.metrics["total_cost"] += cost
        self.metrics["tokens_used"] += tokens
    
    def end_session(self) -> Dict[str, Any]:
        """End the session and return final metrics."""
        self.metrics["end_time"] = datetime.utcnow().isoformat()
        logger.info("Analytics session ended", 
                   task_id=self.session_id,
                   total_cost=self.metrics["total_cost"],
                   api_calls=self.metrics["api_calls"])
        return self.metrics


# =============================================================================
# SECTION 4: CUSTOM TOOLS (Optional)
# =============================================================================
# Define custom tools if needed beyond crewai_tools

class EnterpriseSearchTool:
    """Example custom tool for enterprise search."""
    name = "enterprise_search"
    description = "Search internal enterprise knowledge bases"
    
    def _run(self, query: str) -> str:
        # Implementation would connect to internal systems
        return f"Enterprise search results for: {query}"


# =============================================================================
# SECTION 5: THE FLOW CLASS - MAIN ORCHESTRATION
# =============================================================================
# This is where the magic happens!

@persist  # Enable state persistence across restarts
class LegacyAIPrimeFlow(Flow[AgentState]):
    """
    LegacyAI Prime - Production-Ready CrewAI Agent Flow
    
    This is the GOLD STANDARD implementation demonstrating:
    - Event-driven architecture with precise control
    - Comprehensive error handling and recovery
    - Full observability and monitoring
    - Enterprise-grade tool integration
    - Cost-aware execution with limits
    - Human-in-the-loop support
    
    FLOW DIAGRAM:
    
        ┌─────────────────┐
        │   initialize    │ (@start)
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────┐
        │analyze_requirements│ (@listen)
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────┐
        │ execute_main_task │ (@listen)
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────┐
        │  @router        │ (conditional)
        └───┬────┬────┬───┘
            │    │    │
     errors>3  conf<0.5  conf>=0.5
            │    │    │
            ▼    ▼    ▼
        ┌──────┐ ┌──────┐ ┌──────┐
        │human │ │retry │ │final │
        │escal │ │diff  │ │ize   │
        └──────┘ └──────┘ └──────┘
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize the flow with configuration.
        
        Args:
            config: Optional configuration. Uses defaults if not provided.
        """
        super().__init__()
        self.config = config or AgentConfig()
        self.analytics = AnalyticsService()
        self.tools = self._initialize_tools()
        
        logger.info("LegacyAI Prime Flow initialized",
                   model=self.config.default_model,
                   memory_enabled=self.config.memory_enabled)
    
    # =========================================================================
    # TOOL INITIALIZATION
    # =========================================================================
    
    def _initialize_tools(self) -> List:
        """
        Initialize all production tools with error handling.
        
        Returns:
            List of initialized tool instances
        """
        tools = []
        
        # Add custom tools (always available)
        tools.append(EnterpriseSearchTool())
        
        # Add crewai_tools if available
        if CREWAI_TOOLS_AVAILABLE:
            try:
                tools.extend([
                    SerperDevTool(),
                    ScrapeWebsiteTool(),
                    DirectoryReadTool(),
                    FileReadTool(),
                ])
                # Only add CodeInterpreter if explicitly enabled
                if os.getenv("ENABLE_CODE_INTERPRETER", "false").lower() == "true":
                    tools.append(CodeInterpreterTool())
            except Exception as e:
                logger.warning(f"Failed to initialize some tools: {e}")
        
        logger.info(f"Initialized {len(tools)} tools")
        return tools
    
    # =========================================================================
    # FLOW METHODS - The Event-Driven Pipeline
    # =========================================================================
    
    @start()
    async def initialize_execution(self, inputs: Dict[str, Any]) -> AgentState:
        """
        ENTRY POINT - Initialize execution with state validation.
        
        The @start() decorator marks this as the flow's entry point.
        It's called first when the flow begins execution.
        
        Args:
            inputs: Dictionary of input parameters from the user
            
        Returns:
            Initialized AgentState
        """
        try:
            # Generate task ID if not provided
            self.state.task_id = inputs.get(
                'task_id', 
                f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            self.state.status = "initializing"
            self.state.inputs = inputs
            self.state.created_at = datetime.utcnow().isoformat()
            
            logger.info("Starting execution",
                       task_id=self.state.task_id,
                       inputs=inputs)
            
            # Validate inputs
            if not self._validate_inputs(inputs):
                raise ValueError("Invalid inputs provided")
            
            # Start analytics tracking
            self.analytics.start_session(self.state.task_id)
            
            self.state.status = "initialized"
            self.state.progress = 5.0
            return self.state
            
        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")
            self.state.status = "error"
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state
    
    @listen("initialize_execution")
    async def analyze_requirements(self, state: AgentState) -> AgentState:
        """
        STEP 2 - Analyze task requirements and plan execution.
        
        The @listen("event") decorator creates an event-driven transition.
        This method runs after initialize_execution completes.
        
        Args:
            state: Current state from previous step
            
        Returns:
            Updated AgentState with analysis results
        """
        if self.state.status == "error":
            logger.warning("Skipping analyze_requirements due to error state")
            return self.state
        
        try:
            self.state.status = "analyzing"
            logger.info("Analyzing requirements", task_id=self.state.task_id)
            
            # Create analysis agent
            analyst = self._create_analyst_agent()
            
            # Define analysis task
            analysis_task = Task(
                description=f"""
                Analyze the following request and create an execution plan:
                
                {self.state.inputs}
                
                Provide:
                1. Key objectives
                2. Required resources
                3. Potential challenges
                4. Recommended approach
                """,
                expected_output="Detailed analysis and execution plan",
                agent=analyst
            )
            
            # Execute analysis
            crew = Crew(
                agents=[analyst],
                tasks=[analysis_task],
                process=Process.sequential,
                verbose=self.config.verbose
            )
            
            result = await crew.kickoff_async()
            
            self.state.intermediate_results["analysis"] = str(result)
            self.state.progress = 25.0
            self.state.confidence = 0.6
            
            logger.info("Requirements analysis complete",
                       task_id=self.state.task_id)
            
            return self.state
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state
    
    @listen("analyze_requirements")
    async def execute_main_task(self, state: AgentState) -> AgentState:
        """
        STEP 3 - Execute the main task with specialized agents.
        
        This is where the primary work happens, using a crew of
        specialized agents working together.
        
        Args:
            state: Current state with analysis results
            
        Returns:
            Updated AgentState with execution results
        """
        if self.state.error_count > self.config.max_retries:
            logger.warning("Max errors exceeded, skipping execution")
            return self.state
        
        try:
            self.state.status = "executing"
            logger.info("Executing main task", task_id=self.state.task_id)
            
            # Create specialized agents
            researcher = self._create_researcher_agent()
            implementer = self._create_implementer_agent()
            
            # Define tasks for the crew
            research_task = Task(
                description=f"""
                Research the following based on our analysis:
                
                Analysis: {self.state.intermediate_results.get('analysis', 'N/A')}
                Original Request: {self.state.inputs}
                
                Gather comprehensive information needed for implementation.
                """,
                expected_output="Detailed research findings",
                agent=researcher
            )
            
            implementation_task = Task(
                description="""
                Based on the research findings, create the deliverable:
                
                1. Synthesize the research
                2. Create the requested output
                3. Validate quality and completeness
                """,
                expected_output="Complete deliverable with documentation",
                agent=implementer,
                context=[research_task]  # Depends on research task
            )
            
            # Create and run the crew
            crew = Crew(
                agents=[researcher, implementer],
                tasks=[research_task, implementation_task],
                process=Process.sequential,
                verbose=self.config.verbose,
                memory=self.config.memory_enabled
            )
            
            result = await crew.kickoff_async()
            
            self.state.intermediate_results["execution"] = str(result)
            self.state.progress = 75.0
            self.state.confidence = 0.8
            
            # Track API usage
            self.analytics.record_api_call(cost=0.05, tokens=2000)
            
            logger.info("Main task execution complete",
                       task_id=self.state.task_id,
                       confidence=self.state.confidence)
            
            return self.state
            
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state
    
    # =========================================================================
    # ROUTER - Conditional Flow Control
    # =========================================================================
    
    @router(execute_main_task)
    def determine_next_steps(self) -> str:
        """
        ROUTER - Determine next steps based on execution results.
        
        The @router decorator enables conditional branching.
        Returns a string that matches a @listen decorator.
        
        Returns:
            String identifying the next step:
            - "escalate_to_human": Too many errors
            - "retry_with_different_approach": Low confidence
            - "finalize_results": Success
        """
        logger.info("Determining next steps",
                   error_count=self.state.error_count,
                   confidence=self.state.confidence,
                   progress=self.state.progress)
        
        # Too many errors - need human intervention
        if self.state.error_count > self.config.max_retries:
            logger.warning("Escalating to human due to errors")
            return "escalate_to_human"
        
        # Low confidence - try different approach
        if self.state.confidence < 0.5:
            logger.info("Retrying with different approach due to low confidence")
            return "retry_with_different_approach"
        
        # Good progress - finalize
        if self.state.progress >= 75.0:
            logger.info("Proceeding to finalization")
            return "finalize_results"
        
        # Default - continue execution
        return "continue_execution"
    
    # =========================================================================
    # SUCCESS PATH
    # =========================================================================
    
    @listen("finalize_results")
    async def finalize_and_report(self, state: AgentState) -> AgentState:
        """
        SUCCESS - Finalize results and generate comprehensive report.
        
        Args:
            state: State with completed execution results
            
        Returns:
            Final AgentState with complete results
        """
        try:
            self.state.status = "finalizing"
            logger.info("Finalizing results", task_id=self.state.task_id)
            
            # Create reporter agent
            reporter = self._create_reporter_agent()
            
            # Generate final report
            report_task = Task(
                description=f"""
                Create a comprehensive final report including:
                
                1. Executive Summary
                2. Analysis Results: {self.state.intermediate_results.get('analysis', 'N/A')}
                3. Execution Results: {self.state.intermediate_results.get('execution', 'N/A')}
                4. Key Findings
                5. Recommendations
                6. Next Steps
                
                Format professionally with clear sections.
                """,
                expected_output="Professional report in markdown format",
                agent=reporter
            )
            
            crew = Crew(
                agents=[reporter],
                tasks=[report_task],
                verbose=self.config.verbose
            )
            
            result = await crew.kickoff_async()
            
            # Update final state
            self.state.final_results = {
                "report": str(result),
                "confidence": self.state.confidence,
                "execution_time": self.analytics.metrics.get("start_time")
            }
            self.state.status = "completed"
            self.state.progress = 100.0
            self.state.updated_at = datetime.utcnow().isoformat()
            
            # End analytics session
            self.analytics.end_session()
            
            logger.info("Flow completed successfully",
                       task_id=self.state.task_id,
                       total_cost=self.analytics.metrics["total_cost"])
            
            return self.state
            
        except Exception as e:
            logger.error(f"Finalization failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            self.state.status = "error"
            return self.state
    
    # =========================================================================
    # ERROR RECOVERY PATHS
    # =========================================================================
    
    @listen(or_("escalate_to_human", "retry_with_different_approach"))
    async def handle_error_recovery(self, state: AgentState) -> AgentState:
        """
        ERROR RECOVERY - Handle error recovery and human escalation.
        
        The or_() function allows listening to multiple events.
        This method handles both escalation and retry scenarios.
        
        Args:
            state: State requiring error recovery
            
        Returns:
            Updated state after recovery attempt
        """
        logger.warning("Error recovery triggered",
                      task_id=self.state.task_id,
                      error_count=self.state.error_count,
                      status=self.state.status)
        
        if self.state.error_count > self.config.max_retries:
            # Human escalation required
            self.state.status = "escalated"
            self.state.metadata["escalation_reason"] = self.state.last_error
            self.state.metadata["escalated_at"] = datetime.utcnow().isoformat()
            
            logger.error("Task escalated to human",
                        task_id=self.state.task_id,
                        reason=self.state.last_error)
            
            # In production, this would trigger:
            # - Email notification
            # - Slack alert
            # - Ticketing system
            
            return self.state
        
        # Retry with different approach
        self.state.metadata["retry_count"] = self.state.metadata.get("retry_count", 0) + 1
        self.state.status = "retrying"
        
        logger.info("Retrying with modified approach",
                   retry_count=self.state.metadata["retry_count"])
        
        # Reset progress for retry
        self.state.progress = 25.0
        
        # The flow will continue from analyze_requirements
        return self.state
    
    @listen("continue_execution")
    async def continue_execution(self, state: AgentState) -> AgentState:
        """
        CONTINUE - Continue execution if not ready to finalize.
        
        This is a fallback path for when we need more work.
        """
        logger.info("Continuing execution", progress=self.state.progress)
        self.state.progress += 10.0
        
        # Route back to main execution
        if self.state.progress < 75.0:
            return await self.execute_main_task(state)
        
        return self.state
    
    # =========================================================================
    # AGENT FACTORY METHODS
    # =========================================================================
    # Each agent type has its own factory method for:
    # - Clear separation of concerns
    # - Easy customization per agent type
    # - Consistent configuration
    
    def _create_researcher_agent(self) -> Agent:
        """
        Create a researcher agent specialized in information gathering.
        
        Returns:
            Configured Agent instance
        """
        return Agent(
            role="Senior Research Analyst",
            goal="Gather comprehensive, accurate information from multiple sources",
            backstory="""You are an expert research analyst with 15+ years of 
            experience. You excel at finding relevant information, verifying 
            sources, and synthesizing findings into actionable insights. You 
            approach every research task with thoroughness and skepticism.""",
            tools=self.tools,
            llm=LLM(
                model=self.config.default_model,
                temperature=0.7  # Slightly creative for research
            ),
            verbose=self.config.verbose,
            memory=self.config.memory_enabled,
            max_iter=15,
            allow_delegation=True
        )
    
    def _create_analyst_agent(self) -> Agent:
        """
        Create an analyst agent for requirements analysis.
        
        Returns:
            Configured Agent instance
        """
        return Agent(
            role="Requirements Analyst",
            goal="Analyze requirements and create detailed execution plans",
            backstory="""You are a meticulous requirements analyst who excels 
            at breaking down complex requests into actionable components. You 
            identify dependencies, risks, and optimal execution strategies.""",
            tools=[],  # Analysis doesn't need external tools
            llm=LLM(
                model=self.config.default_model,
                temperature=0.3  # More deterministic for analysis
            ),
            verbose=self.config.verbose,
            memory=self.config.memory_enabled
        )
    
    def _create_implementer_agent(self) -> Agent:
        """
        Create an implementer agent for task execution.
        
        Returns:
            Configured Agent instance
        """
        return Agent(
            role="Senior Implementation Specialist",
            goal="Execute tasks with precision and deliver high-quality outputs",
            backstory="""You are a skilled implementer who transforms plans 
            into reality. You pay attention to detail, follow best practices, 
            and ensure deliverables meet or exceed expectations.""",
            tools=self.tools,
            llm=LLM(
                model=self.config.default_model,
                temperature=0.5
            ),
            verbose=self.config.verbose,
            memory=self.config.memory_enabled,
            max_iter=20
        )
    
    def _create_reporter_agent(self) -> Agent:
        """
        Create a reporter agent for generating final reports.
        
        Returns:
            Configured Agent instance
        """
        return Agent(
            role="Executive Report Writer",
            goal="Create clear, comprehensive, and actionable reports",
            backstory="""You are an expert technical writer who creates 
            executive-level reports. You excel at summarizing complex 
            information, highlighting key findings, and providing clear 
            recommendations.""",
            tools=[],  # Reporting doesn't need external tools
            llm=LLM(
                model=self.config.default_model,
                temperature=0.2  # Very deterministic for reports
            ),
            verbose=self.config.verbose
        )
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """
        Validate input parameters.
        
        Args:
            inputs: Dictionary of input parameters
            
        Returns:
            True if valid, False otherwise
        """
        # Basic validation - extend as needed
        if not inputs:
            logger.warning("Empty inputs provided")
            return False
        
        # Check for required fields (customize per use case)
        # required_fields = ["task_description"]
        # for field in required_fields:
        #     if field not in inputs:
        #         logger.error(f"Missing required field: {field}")
        #         return False
        
        return True


# =============================================================================
# SECTION 6: MAIN ENTRY POINT
# =============================================================================
# This is how the flow is executed when the container starts

async def main():
    """
    Main entry point for running the flow.
    
    This function:
    1. Reads inputs from environment or stdin
    2. Creates the flow instance
    3. Kicks off execution
    4. Handles results/errors
    """
    import json
    
    logger.info("Starting LegacyAI Prime Flow")
    
    # Get inputs from environment (set by orchestrator)
    inputs = {
        "task_description": os.getenv("TASK_DESCRIPTION", "Default task"),
        "task_id": os.getenv("TASK_ID", None),
    }
    
    # Parse additional inputs from TASK_INPUTS env var if present
    task_inputs_json = os.getenv("TASK_INPUTS")
    if task_inputs_json:
        try:
            additional_inputs = json.loads(task_inputs_json)
            inputs.update(additional_inputs)
        except json.JSONDecodeError:
            logger.warning("Failed to parse TASK_INPUTS JSON")
    
    # Create and run the flow
    config = AgentConfig(
        verbose=os.getenv("VERBOSE", "true").lower() == "true",
        memory_enabled=os.getenv("MEMORY_ENABLED", "true").lower() == "true"
    )
    
    flow = LegacyAIPrimeFlow(config=config)
    
    try:
        result = await flow.kickoff_async(inputs=inputs)
        
        logger.info("Flow execution completed",
                   status=flow.state.status,
                   progress=flow.state.progress)
        
        # Output final results
        print(json.dumps({
            "status": flow.state.status,
            "results": flow.state.final_results,
            "metrics": flow.analytics.metrics
        }, indent=2, default=str))
        
    except Exception as e:
        logger.error(f"Flow execution failed: {e}")
        raise


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())


# =============================================================================
# USAGE EXAMPLES
# =============================================================================
"""
EXAMPLE 1: Running locally

    from flow import LegacyAIPrimeFlow
    
    flow = LegacyAIPrimeFlow()
    result = await flow.kickoff_async(inputs={
        "task_description": "Research the latest AI agent frameworks"
    })
    print(flow.state.final_results)

EXAMPLE 2: Running in Docker (via LAIAS)

    # Environment variables set by orchestrator:
    # TASK_ID=task_20260211_143022
    # TASK_DESCRIPTION=Analyze market trends
    # TASK_INPUTS={"competitors": ["Company A", "Company B"]}
    
    # Container runs:
    # python flow.py

EXAMPLE 3: Customizing configuration

    config = AgentConfig(
        default_model="gpt-4-turbo",
        temperature=0.5,
        max_retries=5,
        verbose=False
    )
    flow = LegacyAIPrimeFlow(config=config)
"""
