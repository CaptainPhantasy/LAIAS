"""
Godzilla template reference for code generation.

This module provides the authoritative Godzilla pattern reference
that all generated agents should follow.
"""

GODZILLA_TEMPLATE_REFERENCE = """
# GODZILLA ARCHITECTURAL PATTERN - REFERENCE

## Overview
The Godzilla pattern is a production-ready architecture for CrewAI Flows
that ensures reliability, observability, and maintainability.

## Core Components

### 1. Typed State (REQUIRED)
```python
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class AgentState(BaseModel):
    # Identity
    task_id: str = Field(default="")

    # Status tracking
    status: str = Field(default="pending")
    error_count: int = Field(default=0)
    last_error: Optional[str] = Field(default=None)

    # Progress tracking
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    # Data storage
    inputs: Dict[str, Any] = Field(default_factory=dict)
    intermediate_results: Dict[str, Any] = Field(default_factory=dict)
    final_results: Dict[str, Any] = Field(default_factory=dict)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### 2. Flow Structure (REQUIRED)
```python
from crewai.flow.flow import Flow, listen, start, router, or_
from crewai.flow.persistence import persist

@persist
class GeneratedFlow(Flow[AgentState]):
    \"\"\"Flow following Godzilla pattern.\"\"\"

    def __init__(self):
        super().__init__()
        self.tools = self._initialize_tools()
        self.config = self._get_config()

    @start()
    async def initialize(self, inputs: Dict[str, Any]) -> AgentState:
        \"\"\"Entry point - setup and validation.\"\"\"
        try:
            self.state.task_id = inputs.get("task_id", "auto_" + str(uuid.uuid4())[:8])
            self.state.inputs = inputs
            self.state.status = "initializing"

            logger.info("Flow initialized", task_id=self.state.task_id)
            return self.state

        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state

    @listen("initialize")
    async def execute(self, state: AgentState) -> AgentState:
        \"\"\"Main execution - do the work.\"\"\"
        try:
            self.state.status = "executing"
            # ... main logic ...
            return self.state
        except Exception as e:
            self.state.error_count += 1
            return self.state

    @router(execute)
    def route(self) -> str:
        \"\"\"Conditional routing based on state.\"\"\"
        if self.state.error_count > 3:
            return "error_recovery"
        if self.state.confidence < 0.5:
            return "retry"
        return "finalize"

    @listen("finalize")
    async def complete(self, state: AgentState) -> AgentState:
        \"\"\"Finalize - generate output.\"\"\"
        self.state.status = "completed"
        self.state.progress = 100.0
        return self.state

    @listen(or_("error_recovery", "retry"))
    async def recover(self, state: AgentState) -> AgentState:
        \"\"\"Error recovery handler.\"\"\"
        self.state.status = "recovering"
        return self.state
```

### 3. Agent Factory Pattern (REQUIRED)
```python
def _create_specialist_agent(self) -> Agent:
    \"\"\"Create a specialist agent with proper configuration.\"\"\"
    return Agent(
        role="Specialist Role",
        goal="Clear, specific goal",
        backstory="Detailed backstory motivating behavior",
        tools=self.tools,
        llm=LLM(
            model=self.config.model,
            temperature=self.config.temperature
        ),
        verbose=True,
        memory=True,
        max_iter=15
    )
```

## Required Patterns

| Pattern | Required | Description |
|---------|-----------|-------------|
| @start() | Yes | Entry point decorator |
| @listen() | Yes | Event listener decorator |
| @router() | Yes | Conditional routing |
| @persist | Yes | State persistence |
| try/except | Yes | Error handling |
| logger.info() | Yes | Structured logging |
| Typed State | Yes | Pydantic BaseModel |

## Flow State Transitions

```mermaid
graph TD
    A[start] --> B[initialize]
    B --> C[execute]
    C --> D{router}
    D -->|success| E[finalize]
    D -->|recoverable| F[recover]
    D -->|failed| G[error]
    F --> C
    E --> H[complete]
    G --> I[end]
```

## Error Handling Pattern

```python
try:
    # Operation
    result = await operation()
    self.state.confidence = 0.8
except SpecificException as e:
    logger.warning(f"Expected error: {e}")
    self.state.error_count += 1
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    self.state.error_count += 1
    self.state.last_error = str(e)
```

## Logging Pattern

```python
import structlog

logger = structlog.get_logger()

# Structured logging with context
logger.info(
    "Processing started",
    task_id=self.state.task_id,
    step="initialize",
    inputs=self.state.inputs
)

logger.error(
    "Processing failed",
    task_id=self.state.task_id,
    error=str(e),
    error_count=self.state.error_count
)
```
"""

GODZILLA_VALIDATION_RULES = {
    "required_patterns": [
        (r"class \\w+\\(Flow\\[", "Must use Flow[State] base class"),
        (r"@start\\(\\)", "Must have @start() entry point"),
        (r"@listen\\(", "Must have @listen() event handlers"),
        (r"class \\w+State\\(BaseModel\\)", "Must define typed state with BaseModel"),
        (r"def _create_\\w+_agent\\(self\\)", "Must have agent factory methods"),
        (r"try:", "Must include error handling (try/except)"),
        (r"logger\\.", "Must use structlog logging"),
    ],
    "recommended_patterns": [
        (r"@router\\(", "Consider adding @router() for conditional branching"),
        (r"AnalyticsService", "Consider adding analytics for monitoring"),
        (r"async def", "Consider using async methods for better performance"),
    ]
}
