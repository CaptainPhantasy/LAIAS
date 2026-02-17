"""
================================================================================
                    TEMPORAL_RISK_ASSESSOR AGENT
**Agent Type**: Code Archaeologist / Risk Analyst
================================================================================

Generated from Prompt Library
Date: 2026-02-16
Category: development
================================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================

from crewai import Agent, Task, Crew, Process, LLM
from crewai.flow.flow import Flow, listen, start, router, or_
from crewai.flow.persistence import persist
from crewai_tools import (
    SerperDevTool,
    ScrapeWebsiteTool,
    DirectoryReadTool,
    FileReadTool,
    CodeInterpreterTool
)
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog
import os

logger = structlog.get_logger()


# =============================================================================
# STATE CLASS
# =============================================================================

class TemporalRiskAssessorState(BaseModel):
    """Typed state for temporal_risk_assessor Agent."""

    task_id: str = Field(default="", description="Unique task identifier")
    status: str = Field(default="pending", description="Current execution status")
    error_count: int = Field(default=0, description="Number of errors encountered")
    last_error: Optional[str] = Field(default=None, description="Most recent error message")
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Completion percentage")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Result confidence score")

    inputs: Dict[str, Any] = Field(default_factory=dict, description="Original inputs")
    intermediate_results: Dict[str, Any] = Field(default_factory=dict, description="Work in progress")
    final_results: Dict[str, Any] = Field(default_factory=dict, description="Completed outputs")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


# =============================================================================
# FLOW CLASS
# =============================================================================

@persist
class TemporalRiskAssessorFlow(Flow[TemporalRiskAssessorState]):
    """
    temporal_risk_assessor Agent - **Agent Type**: Code Archaeologist / Risk Analyst

    Category: development
    Tags: analysis, code, security, testing
    """

    def __init__(self):
        super().__init__()
        self.tools = self._initialize_tools()
        logger.info("temporal_risk_assessor Agent initialized")

    def _initialize_tools(self) -> List:
        """Initialize tools for this agent."""
        tools = []
        tool_classes = {
            "SerperDevTool": SerperDevTool,
            "ScrapeWebsiteTool": ScrapeWebsiteTool,
            "DirectoryReadTool": DirectoryReadTool,
            "FileReadTool": FileReadTool,
            "CodeInterpreterTool": CodeInterpreterTool,
        }
        for tool_name in ['FileReadTool', 'CodeInterpreterTool', 'DirectoryReadTool']:
            if tool_name in tool_classes:
                try:
                    tools.append(tool_classes[tool_name]())
                except Exception as e:
                    logger.warning(f"Failed to initialize {tool_name}: {e}")
        return tools

    @start()
    async def initialize(self, inputs: Dict[str, Any]) -> TemporalRiskAssessorState:
        """Entry point - Initialize execution."""
        self.state.task_id = inputs.get('task_id', f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        self.state.status = "initializing"
        self.state.inputs = inputs
        logger.info("Starting execution", task_id=self.state.task_id)
        self.state.status = "initialized"
        self.state.progress = 10.0
        return self.state

    @listen("initialize")
    async def execute(self, state: TemporalRiskAssessorState) -> TemporalRiskAssessorState:
        """Main execution - Perform the agent's primary task."""
        if self.state.status == "error":
            return self.state

        try:
            self.state.status = "executing"
            logger.info("Executing main task", task_id=self.state.task_id)

            # Create the primary agent
            agent = Agent(
                role="temporal_risk_assessor Agent",
                goal="You exist to solve the "same file, same bug" problem: files that seem to attract problems like light",
                backstory="""You are the temporal_risk_assessor Agent, a specialized code archaeologist responsible for identifying and tracking risk across the temporal dimension of your codebase.

## Your Core Identity

You are the "Code Archaeologist" - part historian, part statistician, part risk manager. You've watched the same files cause problems again and again, and you know the patterns that signal "touch this and you'll regret it."

Your personality traits:
- Respectful of code that works (however ugly)
- Skeptica""",
                tools=self.tools,
                llm=LLM(model=os.getenv("DEFAULT_MODEL", "gpt-4o"), temperature=0.7),
                verbose=True,
                memory=True
            )

            # Create the task
            task = Task(
                description=f"""{self.state.inputs}

                When to invoke this agent:
                - You're about to touch a file you've never worked on before
- You want to know which files are "cursed" (high-risk)
- You're planning a refactor and need to know what's safe to change
- You've just fixed a bug and want to understand if it's a recurring problem
- You need to create a risk-based testing strategy
                """,
                expected_output="Complete the requested task with detailed results",
                agent=agent
            )

            # Execute
            crew = Crew(
                agents=[agent],
                tasks=[task],
                process=Process.sequential,
                verbose=True
            )

            result = await crew.kickoff_async()

            self.state.intermediate_results["execution"] = str(result)
            self.state.progress = 80.0
            self.state.confidence = 0.85

            return self.state

        except Exception as e:
            logger.error(f"Execution failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state

    @listen("execute")
    async def finalize(self, state: TemporalRiskAssessorState) -> TemporalRiskAssessorState:
        """Finalize and report results."""
        try:
            self.state.status = "finalizing"

            self.state.final_results = {
                "output": self.state.intermediate_results.get("execution", ""),
                "confidence": self.state.confidence,
                "completed_at": datetime.utcnow().isoformat()
            }

            self.state.status = "completed"
            self.state.progress = 100.0

            logger.info("Execution completed", task_id=self.state.task_id)
            return self.state

        except Exception as e:
            logger.error(f"Finalization failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            self.state.status = "error"
            return self.state


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

async def main():
    """Main entry point for running the flow."""
    import json

    inputs = {
        "task_description": os.getenv("TASK_DESCRIPTION", "Execute task"),
        "task_id": os.getenv("TASK_ID", None),
    }

    task_inputs_json = os.getenv("TASK_INPUTS")
    if task_inputs_json:
        try:
            inputs.update(json.loads(task_inputs_json))
        except json.JSONDecodeError:
            logger.warning("Failed to parse TASK_INPUTS JSON")

    flow = TemporalRiskAssessorFlow()

    try:
        result = await flow.kickoff_async(inputs=inputs)
        print(json.dumps({
            "status": flow.state.status,
            "results": flow.state.final_results
        }, indent=2, default=str))
    except Exception as e:
        logger.error(f"Flow execution failed: {e}")
        raise


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
