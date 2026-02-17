"""
================================================================================
                    CONTEXT_ANCHOR AGENT
**Agent Type**: Mental State Librarian / Context Manager
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

class ContextAnchorState(BaseModel):
    """Typed state for context_anchor Agent."""

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
class ContextAnchorFlow(Flow[ContextAnchorState]):
    """
    context_anchor Agent - **Agent Type**: Mental State Librarian / Context Manager

    Category: development
    Tags: code, development, architecture
    """

    def __init__(self):
        super().__init__()
        self.tools = self._initialize_tools()
        logger.info("context_anchor Agent initialized")

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
    async def initialize(self, inputs: Dict[str, Any]) -> ContextAnchorState:
        """Entry point - Initialize execution."""
        self.state.task_id = inputs.get('task_id', f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        self.state.status = "initializing"
        self.state.inputs = inputs
        logger.info("Starting execution", task_id=self.state.task_id)
        self.state.status = "initialized"
        self.state.progress = 10.0
        return self.state

    @listen("initialize")
    async def execute(self, state: ContextAnchorState) -> ContextAnchorState:
        """Main execution - Perform the agent's primary task."""
        if self.state.status == "error":
            return self.state

        try:
            self.state.status = "executing"
            logger.info("Executing main task", task_id=self.state.task_id)

            # Create the primary agent
            agent = Agent(
                role="context_anchor Agent",
                goal="You exist to solve the context loss problem. Without preservation:
- Returning from a break means 20",
                backstory="""You are the context_anchor Agent, a specialized mental state manager responsible for capturing, compressing, and restoring developer context across sessions.

## Your Core Identity

You are the "Mental State Librarian" - part archivist, part compression expert, part memory palace architect. You understand that developer context is expensive to build and fragile to lose. You preserve the mental state that takes 20 minutes to rebuild.

Your personality traits:
- Attentive to what matters - you ign""",
                tools=self.tools,
                llm=LLM(model=os.getenv("DEFAULT_MODEL", "gpt-4o"), temperature=0.7),
                verbose=True,
                memory=True
            )

            # Create the task
            task = Task(
                description=f"""{self.state.inputs}

                When to invoke this agent:
                - You're starting a work session and need to restore context
- You're pausing work and need to save your mental state
- You're context-switching between projects
- You've been away from the codebase for a while
- You need to remember where you left off
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
    async def finalize(self, state: ContextAnchorState) -> ContextAnchorState:
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

    flow = ContextAnchorFlow()

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
