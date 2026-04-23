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

@persist()  # NOTE: Must be @persist() with parentheses, NOT @persist
class GeneratedFlow(Flow[AgentState]):
    \"\"\"Flow following Godzilla pattern.\"\"\"

    def __init__(self, **kwargs):
        # **kwargs is REQUIRED — @persist() injects a 'persistence' kwarg
        super().__init__(**kwargs)
        # CRITICAL — DO NOT write `self.state = AgentState()` here.
        # `Flow[AgentState]` declares a managed property `self.state` that
        # CrewAI populates automatically from the generic type + the
        # kickoff_async(inputs=...) dict. Assigning to it raises
        # `AttributeError: property 'state' has no setter`. Inside flow
        # methods, mutate fields on self.state (e.g. `self.state.task_id = ...`)
        # — never rebind `self.state` as a whole.
        self.tools = self._initialize_tools()
        self.config = self._get_config()

    @start()
    async def initialize(self) -> AgentState:
        \"\"\"Entry point - setup and validation.

        IMPORTANT: Do NOT add 'inputs: Dict[str, Any]' as a positional arg.
        @persist() wraps this method and will break if it receives unexpected args.
        Instead call kickoff_async(inputs={...}) and access data via self.state,
        which CrewAI pre-populates from the inputs dict before calling this.
        \"\"\"
        try:
            if not self.state.task_id:
                self.state.task_id = "auto_" + str(uuid.uuid4())[:8]
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

**CRITICAL — LLM routing**: Every `Agent` MUST use a Portkey-routed LLM.
CrewAI's default LLM tries to hit OpenAI directly, which will 401 inside
the deployed container (no raw provider keys live there). LAIAS ships
every container with `PORTKEY_API_KEY` + `PORTKEY_VIRTUAL_KEY` env vars;
use them in a `_make_llm()` factory and pass its result to every Agent.

```python
def _make_llm(self) -> LLM:
    \"\"\"Portkey-routed LLM for every Agent in this flow.\"\"\"
    model = os.getenv("LLM_MODEL") or os.getenv("DEFAULT_MODEL", "claude-haiku-4-5-20251001")
    # LiteLLM (CrewAI's LLM backend) treats the 'openai/' prefix as
    # 'use an OpenAI-compatible endpoint at base_url'. Portkey is
    # OpenAI-compatible regardless of which upstream provider the
    # virtual key points to (Anthropic, OpenAI, Google, etc.).
    return LLM(
        model=f"openai/{model}",
        base_url="https://api.portkey.ai/v1",
        api_key=os.getenv("PORTKEY_API_KEY", ""),
        extra_headers={
            "x-portkey-api-key": os.getenv("PORTKEY_API_KEY", ""),
            "x-portkey-virtual-key": os.getenv("PORTKEY_VIRTUAL_KEY", "portkeyclaude"),
        },
        temperature=0.4,
    )

def _create_specialist_agent(self) -> Agent:
    \"\"\"Create a specialist agent with proper configuration.\"\"\"
    return Agent(
        role="Specialist Role",
        goal="Clear, specific goal",
        backstory="Detailed backstory motivating behavior",
        tools=self.tools,
        llm=self._make_llm(),   # ← MUST use the Portkey factory above
        verbose=True,
        memory=True,
        max_iter=15
    )
```

### 4. Output Router (REQUIRED)
```python
import json
import asyncio
import httpx
from pathlib import Path
from datetime import UTC, datetime

class OutputRouter:
    \"\"\"Routes agent output events to files and/or the orchestrator ingest endpoint.\"\"\"

    def __init__(self, deployment_id: str, destinations: Dict[str, bool]):
        self.deployment_id = deployment_id
        self.destinations = destinations
        self.output_root = Path(os.getenv("LAIAS_OUTPUT_ROOT", "/app/outputs"))
        self.ingest_url = os.getenv("LAIAS_OUTPUT_INGEST_URL", "")
        self.run_id = ""

    def set_run_id(self, run_id: str) -> None:
        self.run_id = run_id

    async def emit(self, event_type: str, level: str, message: str, payload: Dict[str, Any]) -> None:
        record = {
            "run_id": self.run_id,
            "event_type": event_type,
            "level": level,
            "message": message,
            "source": "agent",
            "payload": payload,
            "destinations": self.destinations,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        if self.destinations.get("files", False):
            await self._write_file_event(record)
        if self.destinations.get("postgres", False) and self.ingest_url:
            await self._post_event(record)

    def emit_sync(self, event_type: str, level: str, message: str, payload: Dict[str, Any]) -> None:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.emit(event_type, level, message, payload))
        except RuntimeError:
            asyncio.run(self.emit(event_type, level, message, payload))

    async def _write_file_event(self, record: Dict[str, Any]) -> None:
        if not self.run_id:
            return
        run_root = self.output_root / self.run_id
        run_root.mkdir(parents=True, exist_ok=True)
        events_path = run_root / "events.jsonl"
        with events_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\\n")

    async def _post_event(self, record: Dict[str, Any]) -> None:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(self.ingest_url, json=record)
        except Exception as exc:
            logger.warning("Output ingest post failed", error=str(exc))
```

**Wiring in the Flow __init__:**
```python
def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.output_config = self._load_output_config()
    self.output_router = OutputRouter(
        deployment_id=os.getenv("LAIAS_DEPLOYMENT_ID", ""),
        destinations=self.output_config,
    )

def _load_output_config(self) -> Dict[str, bool]:
    raw = os.getenv("LAIAS_OUTPUT_CONFIG", "")
    default_config = {"postgres": True, "files": True}
    if not raw:
        return default_config
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            config = default_config.copy()
            for key in ("postgres", "files"):
                if key in parsed:
                    config[key] = bool(parsed[key])
            return config
    except Exception as e:
        logger.warning(
            "Invalid LAIAS_OUTPUT_CONFIG, using defaults",
            error=str(e),
            context="load_output_config",
        )
    return default_config
```

**Emitting events in flow methods:**
```python
@start()
async def initialize(self) -> AgentState:
    self.output_router.set_run_id(self.state.task_id)
    await self.output_router.emit(
        "run_started", "INFO", "Run started",
        {"task_id": self.state.task_id, "inputs": self.state.inputs},
    )
    # ... rest of initialization ...

@listen("finalize")
async def complete(self, state: AgentState) -> AgentState:
    await self.output_router.emit(
        "run_completed", "INFO", "Run completed",
        {"task_id": self.state.task_id, "status": self.state.status},
    )
    # ... rest of finalization ...
```

## Required Patterns

| Pattern | Required | Description |
|---------|-----------|-------------|
| Flow[State] | Yes | Must use Flow[AgentState] base class |
| @start() | Yes | Entry point decorator |
| @listen() | Yes | Event listener decorator |
| @router() | Yes | Conditional routing |
| @persist() | Yes | State persistence (must include parentheses) |
| try/except | Yes | Error handling |
| logger.info() | Yes | Structured logging |
| Agent factory | Yes | Must have _create_*_agent() factory methods |
| OutputRouter | Yes | Structured output routing for files and database ingest |
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
        (r"OutputRouter", "Must include OutputRouter for output persistence"),
    ],
    "recommended_patterns": [
        (r"@router\\(", "Consider adding @router() for conditional branching"),
        (r"AnalyticsService", "Consider adding analytics for monitoring"),
        (r"async def", "Consider using async methods for better performance"),
    ],
}
