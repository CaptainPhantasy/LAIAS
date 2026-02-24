# LAIAS: From Cold Start to Working Research Workflow

**Document Type:** Operational Guide
**Date Created:** February 21, 2026
**Last Updated:** February 24, 2026 (Cold start audit — port fixes, type fixes, doc corrections)
**Author:** FLOYD v4.0.0
**Purpose:** Step-by-step guide for taking LAIAS from stopped to running a custom 4-agent research workflow

---

## ISSUES FOUND & FIXED (2026-02-24 Cold Start Audit)

| # | Issue | Location | Fix |
|---|-------|----------|-----|
| 1 | 21 hardcoded references to internal container ports (8001, 8002, 3001) in frontend source | studio-ui, control-room, shared libs | Replaced all with correct host ports (4521, 4522, 4528) or env var fallbacks |
| 2 | Control Room dashboard: "Unable to connect — port 8002" error message | `control-room/components/dashboard/system-status.tsx` | Changed to port 4522 |
| 3 | Control Room metrics page: raw `http://localhost:8002` fetch (no env var) | `control-room/app/metrics/page.tsx` | Replaced with `NEXT_PUBLIC_DOCKER_ORCHESTRATOR_URL` env var |
| 4 | Studio UI sidebar: Control Room link pointed to `localhost:3001` | `studio-ui/components/layout/app-shell.tsx` | Changed to `localhost:4528` |
| 5 | Studio UI create page: deploy redirect to `localhost:3001` | `studio-ui/app/create/page.tsx` | Changed to `localhost:4528` |
| 6 | Studio UI team settings: 6 raw `localhost:8001` API calls | `studio-ui/app/settings/team/page.tsx` | Changed to `localhost:4521` |
| 7 | Control Room `page.tsx`: wrong type import (`HealthResponse` vs `DockerHealthResponse`) | `control-room/app/page.tsx` | Fixed to `DockerHealthResponse` |
| 8 | Control Room `page.tsx`: referenced non-existent `health.checks.llm_provider` | `control-room/app/page.tsx` | Changed to `health.checks.docker` |
| 9 | Control Room `page.tsx`: referenced non-existent metrics (`total_agents`, `cache_hits`) | `control-room/app/page.tsx` | Changed to orchestrator metrics (`total_deployments`, etc.) |
| 10 | Shared types: missing `ErrorResponse` and `RegenerateRequest` exports | `shared/types/index.ts` | Added both types |
| 11 | Control Room `types/index.ts`: imported non-existent `ErrorResponse`, wrong `HealthResponse` | `control-room/types/index.ts` | Re-mapped to `DockerErrorResponse` and `DockerHealthResponse` |
| 12 | This doc: wrong ports in health check table, docker ps output, Control Room URL | This file | All corrected to 4521/4522/4527/4528 |

---

## CRITICAL: ZAI API Configuration (Verified 2026-02-24)

**READ THIS FIRST if using ZAI as LLM provider:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ZAI API - VERIFIED WORKING CONFIG                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Endpoint:  https://api.z.ai/api/paas/v4/chat/completions                   │
│  Model:     GLM-4-Plus (20 concurrent) or GLM-4.7 (5 concurrent)            │
│  Temp:      0.2 MAX                                                          │
│  REQUIRED:  "thinking": {"type": "disabled"}                                │
│                                                                              │
│  WITHOUT thinking disabled, content returns EMPTY and goes to               │
│  reasoning_content field instead!                                           │
│                                                                              │
│  See: /Volumes/Storage/LAIAS/docs/ZAI_API_VERIFIED.md                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## What This Document Covers

This guide documents the exact process used to:

1. Start the LAIAS platform from a cold stop
2. Verify all services are healthy
3. Understand the LAIAS architecture
4. Create a custom 4-agent research workflow
5. Test the workflow inside the Docker environment

**Target Audience:** Someone who has never used LAIAS but has basic terminal skills.

---

## ROADMAP: What To Do First

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  START HERE - DO THESE IN ORDER                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. START SERVICES                                                           │
│     cd /Volumes/Storage/LAIAS && docker compose up -d                        │
│                                                                              │
│  2. VERIFY HEALTH                                                            │
│     docker ps --format "table {{.Names}}\t{{.Status}}"                        │n│     All services must show (healthy)                                         │
│                                                                              │
│  3. CHECK API KEYS                                                           │
│     cat /Volumes/Storage/LAIAS/services/agent-generator/.env                 │
│     Ensure ZAI_API_KEY or OPENAI_API_KEY is set                              │
│                                                                              │
│  4. TEST GENERATION (use openai to avoid ZAI concurrency issues)             │
│     curl -X POST http://localhost:4521/api/generate-agent \                  │
│       -H 'Content-Type: application/json' \                                  │
│       -d '{"description":"Simple greeter","agent_name":"Test"}'            │
│                                                                              │
│  5. IF STEP 4 FAILLS: Check logs                                             │
│     docker logs laias-agent-generator --tail 50                              │
│     Look for "LLM request failed" or JSON parse errors                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## KNOWN FAILURE POINTS (Updated 2026-02-24)

| Issue | Cause | Fix |
|-------|-------|-----|
| Empty LLM response | ZAI thinking mode enabled | Add `"thinking": {"type": "disabled"}` to payload |
| JSON parse error | LLM returns markdown, not JSON | Check `extract_code_from_markdown` helper |
| ZAI concurrency limit | GLM-5 has low concurrency | Use `GLM-4-Plus` (20 concurrent) |
| Wrong ZAI endpoint | Using /api/coding/paas/v4 | Use /api/paas/v4 |
| Model name case | glm-4-plus vs GLM-4-Plus | Use exact case: `GLM-4-Plus` |

---

## Part 1: What LAIAS Is

LAIAS (Legacy AI Agent Studio) is a platform that generates, deploys, and monitors AI agents. It uses CrewAI under the hood and follows a pattern called "Godzilla" for production-grade agent workflows.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              LAIAS PLATFORM                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  USER INTERFACES                                                             │
│  ───────────────                                                             │
│  • Studio UI (port 4527)      → Chat interface to create agents             │
│  • Control Room (port 4528)   → Dashboard to monitor running agents         │
│                                                                              │
│  BACKEND SERVICES                                                            │
│  ────────────────                                                            │
│  • Agent Generator (port 4521) → Generates agent code from descriptions     │
│  • Docker Orchestrator (4522)  → Deploys agents to containers               │
│                                                                              │
│  INFRASTRUCTURE                                                              │
│  ──────────────                                                              │
│  • PostgreSQL (port 5432)      → Stores agents, deployments, logs           │
│  • Redis (port 6379)           → Task queues, caching                       │
│                                                                              │
│  DIRECTORY STRUCTURE                                                         │
│  ────────────────────                                                        │
│  /Volumes/Storage/LAIAS/                                                     │
│  ├── docker-compose.yml        → Service orchestration                      │
│  ├── services/                                                              │
│  │   ├── agent-generator/      → FastAPI service (port 4521)               │
│  │   └── docker-orchestrator/  → FastAPI service (port 4522)               │
│  ├── frontend/                                                              │
│  │   ├── studio-ui/            → Next.js app (port 4527)                   │
│  │   └── control-room/         → Next.js app (port 4528)                   │
│  ├── templates/                                                             │
│  │   ├── godzilla_reference.py → Gold standard agent pattern               │
│  │   ├── presets/              → 100+ pre-built agent configs              │
│  │   └── agents/               → Agents organized by category              │
│  ├── agents/                   → Custom agent workflows (we created this)   │
│  └── infrastructure/                                                        │
│      ├── init.sql              → Database schema                            │
│      └── redis.conf            → Redis configuration                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 2: Starting LAIAS from Cold Stop

### Prerequisites

- Docker Desktop must be installed and running
- Docker Compose must be available
- Ports 4527, 4528, 5432, 6379, 4521, 4522 must not be in use by other applications

### Step 1: Verify Docker is Running

Open Terminal and run:

```bash
docker ps
```

Expected output: A table showing running containers (may be empty if nothing is running).

If you see "Cannot connect to the Docker daemon":
- Open Docker Desktop application
- Wait for it to start (whale icon in menu bar should be steady)
- Try again

### Step 2: Navigate to LAIAS Directory

```bash
cd /Volumes/Storage/LAIAS
```

### Step 3: Start All Services

```bash
docker compose up -d
```

This command:
- Reads `docker-compose.yml` to understand what services to start
- Pulls/builds images if needed
- Starts all services in the correct order (database first, then services that depend on it)
- The `-d` flag runs them in "detached" mode (background)

Expected output:
```
 Container laias-redis Starting 
 Container laias-postgres Starting 
 Container laias-redis Started 
 Container laias-postgres Started 
 Container laias-redis Healthy 
 Container laias-postgres Healthy 
 Container laias-agent-generator Starting 
 Container laias-docker-orchestrator Starting 
 Container laias-docker-orchestrator Started 
 Container laias-agent-generator Healthy 
 Container laias-control-room Starting 
 Container laias-control-room Started 
 Container laias-studio-ui Starting 
 Container laias-studio-ui Started 
```

### Step 4: Verify All Services Are Running

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

Expected output:
```
NAMES                       STATUS                    PORTS
laias-studio-ui             Up X seconds (healthy)    0.0.0.0:4527->3000/tcp
laias-control-room          Up X seconds (healthy)    0.0.0.0:4528->3001/tcp
laias-docker-orchestrator   Up X seconds (healthy)    0.0.0.0:4522->8002/tcp
laias-agent-generator       Up X seconds (healthy)    0.0.0.0:4521->8001/tcp
laias-postgres              Up X seconds (healthy)    0.0.0.0:5432->5432/tcp
laias-redis                 Up X seconds (healthy)    0.0.0.0:6379->6379/tcp
```

All 6 services should show "(healthy)" status.

### Step 5: Check API Health Endpoints

You can verify each service is responding by checking their health endpoints in a browser or with curl:

| Service | Health Check URL |
|---------|------------------|
| Agent Generator | http://localhost:4521/health |
| Docker Orchestrator | http://localhost:4522/health |
| Studio UI | http://localhost:4527 |
| Control Room | http://localhost:4528 |

**Note:** If curl is blocked, just open the URLs in a browser. You should see JSON responses for the health endpoints.

---

## Part 3: Understanding the Godzilla Pattern

The "Godzilla Pattern" is LAIAS's architectural standard for agent workflows. Every production agent follows this structure.

### The Pattern Structure

```python
# 1. IMPORTS
from crewai import Agent, Task, Crew, Process, LLM
from crewai.flow.flow import Flow, listen, start, router
from pydantic import BaseModel, Field

# 2. STATE CLASS - Typed data that flows through the workflow
class AgentState(BaseModel):
    task_id: str = ""
    status: str = "pending"
    error_count: int = 0
    progress: float = 0.0
    # ... domain-specific fields

# 3. FLOW CLASS - The main orchestration
class MyFlow(Flow[AgentState]):
    
    def __init__(self):
        super().__init__()
        # Initialize resources
    
    # ENTRY POINT - Marked with @start()
    @start()
    async def initialize(self, inputs: Dict[str, Any]) -> AgentState:
        # First method that runs
        self.state.task_id = inputs.get('task_id', 'default')
        return self.state
    
    # SUBSEQUENT STEPS - Marked with @listen("previous_method_name")
    @listen("initialize")
    async def do_work(self, state: AgentState) -> AgentState:
        # Runs after initialize completes
        # ... actual work happens here
        return self.state
    
    # CONDITIONAL BRANCHING - Marked with @router(previous_method)
    @router(do_work)
    def decide_next(self) -> str:
        if self.state.error_count > 3:
            return "escalate"
        return "continue"
    
    # AGENT FACTORY METHODS - Create specialized agents
    def _create_researcher_agent(self) -> Agent:
        return Agent(
            role="Researcher",
            goal="Find information",
            backstory="Expert researcher...",
            llm=self.llm,
            tools=[...]
        )

# 4. MAIN ENTRY POINT
async def main():
    flow = MyFlow()
    result = await flow.kickoff_async(inputs={"topic": "..."})
    print(flow.state.status)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### Key Concepts

| Concept | What It Does |
|---------|--------------|
| `Flow[StateClass]` | Base class that manages workflow state |
| `@start()` | Marks the entry point method |
| `@listen("method_name")` | Runs after the named method completes |
| `@router(method)` | Conditional branching - returns string matching next @listen |
| `self.state` | The typed state object that persists through the flow |
| `Agent` | An AI agent with a role, goal, and tools |
| `Task` | A unit of work assigned to an agent |
| `Crew` | A team of agents working together |

---

## Part 4: Creating a Custom Research Workflow

### The Goal

Create a 4-agent workflow that:
1. **Researches** a topic using web search
2. **Analyzes** how it applies to Legacy AI specifically
3. **Documents** the findings in a structured markdown file
4. **Builds** a new workflow if the research indicates one is needed

### Step 1: Create the Agents Directory

```bash
mkdir -p /Volumes/Storage/LAIAS/agents
```

This is where custom agent workflows live (separate from the templates).

### Step 2: Create the Workflow File

Create a new file at `/Volumes/Storage/LAIAS/agents/legacy_research_workflow.py`

The complete code is in Appendix A, but here's the structure:

```
legacy_research_workflow.py
│
├── IMPORTS (CrewAI, Pydantic, etc.)
│
├── ResearchWorkflowState (Pydantic model)
│   ├── task_id
│   ├── research_topic
│   ├── status
│   ├── progress
│   ├── research_findings
│   ├── legacy_analysis
│   ├── documentation_path
│   └── generated_workflow
│
├── LegacyResearchWorkflow (Flow class)
│   │
│   ├── Agent Factories
│   │   ├── _create_researcher()
│   │   ├── _create_analyst()
│   │   ├── _create_documenter()
│   │   └── _create_workflow_builder()
│   │
│   └── Flow Methods
│       ├── initialize_workflow()     [@start]
│       ├── conduct_research()        [@listen]
│       ├── analyze_for_legacy()      [@listen]
│       ├── create_documentation()    [@listen]
│       ├── determine_build_need()    [@router]
│       ├── build_workflow()          [@listen]
│       └── finalize()                [@listen]
│
└── main() (entry point)
```

### Step 3: Copy Workflow to Docker Container

LAIAS runs inside Docker containers. Your local Python might not have the right dependencies (CrewAI requires Python 3.10+). To run the workflow, copy it into the container:

```bash
# Create agents directory in container if it doesn't exist
docker exec laias-agent-generator mkdir -p /app/agents

# Copy the workflow file
docker cp /Volumes/Storage/LAIAS/agents/legacy_research_workflow.py laias-agent-generator:/app/agents/
```

### Step 4: Test the Workflow Imports

Before running the full workflow, verify it loads correctly:

```bash
docker exec laias-agent-generator python -c "
import sys
sys.path.insert(0, '/app/agents')
from legacy_research_workflow import LegacyResearchWorkflow, ResearchWorkflowState
print('✅ Workflow imports successfully')
workflow = LegacyResearchWorkflow()
print(f'✅ Workflow initialized')
print(f'   Status: {workflow.state.status}')
print(f'   Progress: {workflow.state.progress}%')
"
```

Expected output:
```
✅ Workflow imports successfully
Legacy Research Workflow initialized
✅ Workflow initialized
   Status: pending
   Progress: 0.0%
```

---

## Part 5: Running the Workflow

### Interactive Test Run

To run the workflow with a test topic:

```bash
docker exec laias-agent-generator python -c "
import asyncio
import sys
sys.path.insert(0, '/app/agents')
from legacy_research_workflow import LegacyResearchWorkflow

async def test():
    workflow = LegacyResearchWorkflow()
    
    result = await workflow.kickoff_async(inputs={
        'topic': 'Best LinkedIn posting times for AI founders',
        'output_directory': '/app/output'
    })
    
    print(f'Status: {workflow.state.status}')
    print(f'Progress: {workflow.state.progress}%')
    print(f'Documentation: {workflow.state.documentation_path}')

asyncio.run(test())
"
```

**Note:** This will consume LLM API tokens and take 2-5 minutes depending on the topic complexity.

### What Happens During Execution

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  EXECUTION FLOW                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. INITIALIZE (5%)                                                          │
│     • Set task_id and research_topic                                        │
│     • Initialize state                                                       │
│                                                                              │
│  2. RESEARCH (10% → 35%)                                                     │
│     • Researcher agent activated                                            │
│     • Performs web searches (if tools configured)                           │
│     • Synthesizes findings                                                   │
│     • Results stored in state.research_findings                             │
│                                                                              │
│  3. ANALYZE (40% → 65%)                                                      │
│     • Analyst agent activated                                               │
│     • Applies findings to Legacy AI context                                 │
│     • Identifies opportunities and threats                                  │
│     • Results stored in state.legacy_analysis                               │
│                                                                              │
│  4. DOCUMENT (70% → 85%)                                                     │
│     • Documenter agent activated                                            │
│     • Creates markdown file with proper naming                              │
│     • Saves to output_directory                                             │
│     • Path stored in state.documentation_path                               │
│                                                                              │
│  5. BUILD CHECK (router)                                                     │
│     • Analyzes whether new workflow is needed                               │
│     • If yes → build_workflow() at 90%                                      │
│     • If no → finalize() directly                                           │
│                                                                              │
│  6. FINALIZE (100%)                                                          │
│     • Sets status to "completed"                                            │
│     • Records completion timestamp                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 6: Accessing the User Interfaces

### Studio UI (Agent Builder)

1. Open browser to: http://localhost:4527
2. This is a chat interface where you can describe agents in natural language
3. LAIAS generates CrewAI code based on your description

### Control Room (Monitoring)

1. Open browser to: http://localhost:4528
2. Shows running containers and agent status
3. Can view logs from running agents

### API Documentation

The API docs are disabled in production mode for security. To enable:

1. Edit `/Volumes/Storage/LAIAS/services/agent-generator/.env`
2. Set `DEBUG=true`
3. Restart: `docker compose restart laias-agent-generator`
4. Access docs at: http://localhost:4521/docs

---

## Part 7: Stopping LAIAS

To stop all services:

```bash
cd /Volumes/Storage/LAIAS
docker compose down
```

To stop but preserve data:

```bash
docker compose stop
```

To restart after stopping:

```bash
docker compose start
```

---

## Part 8: What's Next (Future Work)

The workflow is created and verified, but these pieces are not yet implemented:

### 1. Webhook Trigger

Currently the workflow must be triggered manually. To enable Google Sheets → LAIAS automation:

- Create a FastAPI endpoint in agent-generator that receives POST requests
- Configure Zapier to watch Google Sheets and POST to the endpoint
- The endpoint would call `LegacyResearchWorkflow().kickoff_async()`

### 2. Shift Supervisor Daemon

A background process that runs workflows on schedule:

```python
# shift_supervisor.py (not yet created)
import schedule
import requests

def run_marketing_agent():
    # Trigger marketing workflow
    requests.post("http://localhost:4521/api/trigger", json={"workflow": "marketing"})

schedule.every().day.at("08:00").do(run_marketing_agent)
```

### 3. Integration with SUPERCACHE

The workflow should checkpoint results to SUPERCACHE for persistence across sessions.

---

## Appendix A: Complete Workflow Code

File: `/Volumes/Storage/LAIAS/agents/legacy_research_workflow.py`

```python
"""
================================================================================
            LEGACY AI RESEARCH WORKFLOW
            "From Question to Actionable Intelligence"
================================================================================

A 4-agent research pipeline that takes a topic, researches it deeply,
analyzes it for Legacy AI's context, documents the findings, and
optionally generates new workflows.

FLOW:
    Trigger (webhook/manual) → Research → Analyze → Document → Build

Author: Legacy AI
Date: February 2026
Version: 1.0
================================================================================
"""

from crewai import Agent, Task, Crew, Process, LLM
from crewai.flow.flow import Flow, listen, start, router, or_
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog
import os
import json

# =============================================================================
# LOGGING
# =============================================================================

logger = structlog.get_logger()


# =============================================================================
# STATE CLASS
# =============================================================================

class ResearchWorkflowState(BaseModel):
    """State for the Research Workflow."""
    
    # Execution Identity
    task_id: str = Field(default="", description="Unique task identifier")
    research_topic: str = Field(default="", description="Topic to research")
    
    # Status Tracking
    status: str = Field(default="pending")
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    
    # Error Handling
    error_count: int = Field(default=0)
    last_error: Optional[str] = Field(default=None)
    
    # Agent Outputs
    research_findings: Dict[str, Any] = Field(default_factory=dict)
    legacy_analysis: Dict[str, Any] = Field(default_factory=dict)
    documentation_path: Optional[str] = Field(default=None)
    generated_workflow: Optional[str] = Field(default=None)
    
    # Configuration
    output_directory: str = Field(default="/Volumes/Storage/Research")
    max_retries: int = Field(default=3)
    
    # Metadata
    created_at: Optional[str] = Field(default=None)
    completed_at: Optional[str] = Field(default=None)


# =============================================================================
# THE FLOW
# =============================================================================

class LegacyResearchWorkflow(Flow[ResearchWorkflowState]):
    """
    Legacy AI Research Workflow
    
    A 4-stage pipeline:
    1. RESEARCH: Deep web research on the topic
    2. ANALYZE: Apply findings to Legacy AI context
    3. DOCUMENT: Create structured documentation
    4. BUILD: Generate workflows if needed
    """
    
    def __init__(self):
        super().__init__()
        self.llm = self._get_llm()
        logger.info("Legacy Research Workflow initialized")
    
    def _get_llm(self) -> LLM:
        """Get the LLM configured for this workflow."""
        provider = os.getenv("LAIAS_LLM_PROVIDER", "zai")
        model = os.getenv("LAIAS_LLM_MODEL", "glm-4")
        
        if provider == "zai":
            return LLM(
                model="glm-4",
                api_key=os.getenv("ZAI_API_KEY"),
                base_url="https://open.bigmodel.cn/api/paas/v4"
            )
        else:
            return LLM(model=model or "gpt-4o")
    
    # =========================================================================
    # AGENT FACTORIES
    # =========================================================================
    
    def _create_researcher(self) -> Agent:
        """Create the Research Agent."""
        return Agent(
            role="Senior Research Analyst",
            goal="Conduct comprehensive research and gather actionable intelligence",
            backstory="""You are an expert researcher with 15+ years of experience 
            in technology and business research. You excel at finding relevant 
            information, verifying sources, and synthesizing findings into 
            structured, actionable insights. You are thorough but efficient.""",
            llm=self.llm,
            verbose=True,
            max_iter=20
        )
    
    def _create_analyst(self) -> Agent:
        """Create the Legacy AI Analyst Agent."""
        return Agent(
            role="Legacy AI Strategy Analyst",
            goal="Analyze research findings and identify opportunities for Legacy AI",
            backstory="""You are a strategic analyst specializing in AI tooling 
            and solo founder businesses. You understand Legacy AI's ecosystem:
            - FLOYD: AI coding assistant ecosystem
            - LAIAS: Agent factory platform
            - SUPERCACHE: 3-tier memory system
            - Philosophy: BALLS (Borderless, Autonomous, Loud, Living, Subversive)
            - Founder: Douglas Talley, solo developer in Indiana
            
            You identify how research findings apply to this specific context
            and prioritize opportunities by impact and feasibility.""",
            llm=self.llm,
            verbose=True,
            max_iter=15
        )
    
    def _create_documenter(self) -> Agent:
        """Create the Documenter Agent."""
        return Agent(
            role="Technical Documentation Specialist",
            goal="Create clear, well-organized documentation following best practices",
            backstory="""You are a technical writer who creates documentation 
            that is both comprehensive and accessible. You follow document 
            management best practices:
            - YYYY-MM-DD_[Topic].md naming convention
            - Structured sections with clear hierarchy
            - Executive summaries for quick scanning
            - Actionable recommendations
            - Proper categorization and tagging""",
            llm=self.llm,
            verbose=True,
            max_iter=10
        )
    
    def _create_workflow_builder(self) -> Agent:
        """Create the Workflow Builder Agent."""
        return Agent(
            role="Agent Workflow Architect",
            goal="Generate CrewAI workflow code following the Godzilla pattern",
            backstory="""You are an expert in CrewAI and the Godzilla architectural 
            pattern. You generate production-ready agent code that includes:
            - Typed state management with Pydantic
            - Event-driven architecture with @start, @listen, @router decorators
            - Error handling with retry logic
            - Analytics and monitoring integration
            
            You only generate code when a new workflow is genuinely needed.""",
            llm=self.llm,
            verbose=True,
            max_iter=25
        )
    
    # =========================================================================
    # FLOW METHODS
    # =========================================================================
    
    @start()
    async def initialize_workflow(self, inputs: Dict[str, Any]) -> ResearchWorkflowState:
        """Initialize the research workflow."""
        try:
            self.state.task_id = inputs.get(
                'task_id',
                f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            self.state.research_topic = inputs.get('topic', inputs.get('research_topic', ''))
            self.state.output_directory = inputs.get(
                'output_directory',
                '/Volumes/Storage/Research'
            )
            self.state.created_at = datetime.utcnow().isoformat()
            self.state.status = "initialized"
            self.state.progress = 5.0
            
            logger.info(
                "Research workflow initialized",
                task_id=self.state.task_id,
                topic=self.state.research_topic
            )
            
            return self.state
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            self.state.status = "error"
            return self.state
    
    @listen("initialize_workflow")
    async def conduct_research(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        """Stage 1: Conduct deep research on the topic."""
        if self.state.status == "error":
            return self.state
        
        try:
            self.state.status = "researching"
            self.state.progress = 10.0
            logger.info("Starting research", topic=self.state.research_topic)
            
            researcher = self._create_researcher()
            
            research_task = Task(
                description=f"""
                Conduct comprehensive research on: {self.state.research_topic}
                
                Your research should:
                1. Define the topic and its significance
                2. Gather information from multiple perspectives
                3. Identify key players, technologies, or concepts
                4. Note recent developments and trends
                5. Find data, statistics, or evidence
                6. Identify knowledge gaps or uncertainties
                
                Output a structured research summary with:
                - Overview
                - Key Findings (bullet points with sources)
                - Trends and Patterns
                - Open Questions
                - Source List
                """,
                expected_output="Structured research summary with citations",
                agent=researcher
            )
            
            crew = Crew(
                agents=[researcher],
                tasks=[research_task],
                process=Process.sequential,
                verbose=True
            )
            
            result = await crew.kickoff_async()
            
            self.state.research_findings = {
                "raw_output": str(result),
                "topic": self.state.research_topic,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.state.progress = 35.0
            
            logger.info("Research completed", task_id=self.state.task_id)
            return self.state
            
        except Exception as e:
            logger.error(f"Research failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state
    
    @listen("conduct_research")
    async def analyze_for_legacy(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        """Stage 2: Analyze findings for Legacy AI context."""
        if self.state.error_count > self.state.max_retries:
            return self.state
        
        try:
            self.state.status = "analyzing"
            self.state.progress = 40.0
            logger.info("Starting Legacy AI analysis")
            
            analyst = self._create_analyst()
            
            analysis_task = Task(
                description=f"""
                Analyze the following research findings for Legacy AI:
                
                RESEARCH FINDINGS:
                {self.state.research_findings.get('raw_output', 'No findings available')}
                
                YOUR ANALYSIS SHOULD ADDRESS:
                1. RELEVANCE: How does this apply to Legacy AI's business?
                   - FLOYD ecosystem (AI coding assistant)
                   - LAIAS platform (agent factory)
                   - Solo founder model
                
                2. OPPORTUNITIES: What opportunities does this create?
                   - New features or products
                   - Market positioning
                   - Competitive advantages
                
                3. THREATS: What risks or challenges does this present?
                
                4. ACTIONS: What should Legacy AI do about this?
                   - Immediate actions (next 7 days)
                   - Short-term (next 30 days)
                   - Long-term considerations
                
                5. PRIORITY: Rank opportunities by impact and feasibility
                
                Output a structured analysis with clear recommendations.
                """,
                expected_output="Strategic analysis with prioritized recommendations",
                agent=analyst
            )
            
            crew = Crew(
                agents=[analyst],
                tasks=[analysis_task],
                process=Process.sequential,
                verbose=True
            )
            
            result = await crew.kickoff_async()
            
            self.state.legacy_analysis = {
                "raw_output": str(result),
                "timestamp": datetime.utcnow().isoformat()
            }
            self.state.progress = 65.0
            
            logger.info("Analysis completed", task_id=self.state.task_id)
            return self.state
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state
    
    @listen("analyze_for_legacy")
    async def create_documentation(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        """Stage 3: Create structured documentation."""
        if self.state.error_count > self.state.max_retries:
            return self.state
        
        try:
            self.state.status = "documenting"
            self.state.progress = 70.0
            logger.info("Creating documentation")
            
            documenter = self._create_documenter()
            
            date_str = datetime.now().strftime('%Y-%m-%d')
            safe_topic = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in self.state.research_topic)
            safe_topic = safe_topic[:50].strip().replace(' ', '_')
            filename = f"{date_str}_{safe_topic}.md"
            
            doc_task = Task(
                description=f"""
                Create a comprehensive research document following best practices.
                
                RESEARCH FINDINGS:
                {self.state.research_findings.get('raw_output', 'N/A')}
                
                LEGACY AI ANALYSIS:
                {self.state.legacy_analysis.get('raw_output', 'N/A')}
                
                DOCUMENT STRUCTURE:
                
                # {self.state.research_topic}
                
                **Date:** {date_str}
                **Document Type:** Research Analysis
                **Status:** Complete
                
                ---
                
                ## Executive Summary
                [2-3 paragraph overview for quick reading]
                
                ## Key Findings
                [Bulleted list of most important discoveries]
                
                ## Legacy AI Relevance
                [How this applies to our business]
                
                ## Opportunities
                [Ranked list of actionable opportunities]
                
                ## Recommendations
                [Specific next steps with priority levels]
                
                ## Open Questions
                [What we still don't know]
                
                ## Sources
                [List of references]
                
                ---
                
                *Generated by Legacy AI Research Workflow*
                
                OUTPUT THE COMPLETE MARKDOWN DOCUMENT.
                """,
                expected_output="Complete markdown document",
                agent=documenter
            )
            
            crew = Crew(
                agents=[documenter],
                tasks=[doc_task],
                process=Process.sequential,
                verbose=True
            )
            
            result = await crew.kickoff_async()
            
            doc_content = str(result)
            doc_path = os.path.join(self.state.output_directory, filename)
            
            os.makedirs(self.state.output_directory, exist_ok=True)
            
            with open(doc_path, 'w') as f:
                f.write(doc_content)
            
            self.state.documentation_path = doc_path
            self.state.progress = 85.0
            
            logger.info("Documentation created", path=doc_path)
            return self.state
            
        except Exception as e:
            logger.error(f"Documentation failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state
    
    @router(create_documentation)
    def determine_build_need(self) -> str:
        """Determine if a new workflow needs to be built."""
        analysis = self.state.legacy_analysis.get('raw_output', '')
        
        workflow_keywords = [
            'automate this',
            'create an agent',
            'build a workflow',
            'new agent needed',
            'should be automated',
            'workflow required'
        ]
        
        if any(kw in analysis.lower() for kw in workflow_keywords):
            logger.info("Workflow build triggered based on analysis")
            return "build_workflow"
        
        logger.info("No workflow build needed")
        return "finalize"
    
    @listen("build_workflow")
    async def build_workflow(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        """Stage 4: Build a new workflow if needed."""
        try:
            self.state.status = "building"
            self.state.progress = 90.0
            logger.info("Building new workflow")
            
            builder = self._create_workflow_builder()
            
            build_task = Task(
                description=f"""
                Based on the research and analysis, generate a CrewAI workflow 
                following the Godzilla pattern.
                
                RESEARCH TOPIC: {self.state.research_topic}
                
                ANALYSIS:
                {self.state.legacy_analysis.get('raw_output', 'N/A')}
                
                Generate a complete Python file that:
                1. Follows the Godzilla architectural pattern
                2. Uses typed state with Pydantic BaseModel
                3. Has event-driven flow with @start, @listen, @router decorators
                4. Includes error handling and retry logic
                5. Is production-ready
                
                Output the complete Python code.
                """,
                expected_output="Complete Python workflow code",
                agent=builder
            )
            
            crew = Crew(
                agents=[builder],
                tasks=[build_task],
                process=Process.sequential,
                verbose=True
            )
            
            result = await crew.kickoff_async()
            
            self.state.generated_workflow = str(result)
            self.state.progress = 95.0
            
            logger.info("Workflow built", task_id=self.state.task_id)
            return self.state
            
        except Exception as e:
            logger.error(f"Workflow build failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state
    
    @listen(or_("finalize", "build_workflow"))
    async def finalize(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        """Finalize the workflow and return results."""
        try:
            self.state.status = "completed"
            self.state.progress = 100.0
            self.state.completed_at = datetime.utcnow().isoformat()
            
            summary = {
                "task_id": self.state.task_id,
                "topic": self.state.research_topic,
                "status": self.state.status,
                "documentation_path": self.state.documentation_path,
                "workflow_generated": self.state.generated_workflow is not None,
                "created_at": self.state.created_at,
                "completed_at": self.state.completed_at
            }
            
            logger.info("Research workflow completed", **summary)
            
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
    """Run the research workflow."""
    import asyncio
    
    topic = os.getenv("RESEARCH_TOPIC", "Best practices for LinkedIn posting times for AI/tech founders")
    
    workflow = LegacyResearchWorkflow()
    
    inputs = {
        "topic": topic,
        "output_directory": "/app/output"
    }
    
    result = await workflow.kickoff_async(inputs=inputs)
    
    print("\n" + "="*60)
    print("RESEARCH WORKFLOW COMPLETE")
    print("="*60)
    print(f"Status: {workflow.state.status}")
    print(f"Progress: {workflow.state.progress}%")
    print(f"Documentation: {workflow.state.documentation_path}")
    if workflow.state.generated_workflow:
        print(f"Workflow Generated: Yes")
    print("="*60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## Appendix B: Quick Reference Commands

```bash
# Start LAIAS
cd /Volumes/Storage/LAIAS && docker compose up -d

# Check status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# View logs
docker logs laias-agent-generator --tail 50

# Stop LAIAS
docker compose down

# Test workflow import
docker exec laias-agent-generator python -c "
import sys; sys.path.insert(0, '/app/agents')
from legacy_research_workflow import LegacyResearchWorkflow
print('✅ OK')
"

# Run workflow
docker exec laias-agent-generator python -c "
import asyncio, sys, os
sys.path.insert(0, '/app/agents')
os.chdir('/app')
from legacy_research_workflow import LegacyResearchWorkflow

async def run():
    w = LegacyResearchWorkflow()
    await w.kickoff_async({'topic': 'YOUR_TOPIC_HERE', 'output_directory': '/app/output'})
    print(f'Done: {w.state.documentation_path}')

asyncio.run(run())
"
```

---

## Appendix C: File Locations Summary

| File | Location | Purpose |
|------|----------|---------|
| docker-compose.yml | `/Volumes/Storage/LAIAS/` | Service definitions |
| godzilla_reference.py | `/Volumes/Storage/LAIAS/templates/` | Pattern reference |
| legacy_research_workflow.py | `/Volumes/Storage/LAIAS/agents/` | Custom workflow |
| Agent Generator code | `/Volumes/Storage/LAIAS/services/agent-generator/` | Backend API |
| Studio UI code | `/Volumes/Storage/LAIAS/frontend/studio-ui/` | Chat interface |
| Control Room code | `/Volumes/Storage/LAIAS/frontend/control-room/` | Monitoring UI |
| Agent templates | `/Volumes/Storage/LAIAS/templates/presets/` | 100+ pre-built configs |
| Environment config | `/Volumes/Storage/LAIAS/services/agent-generator/.env` | API keys |

---

**DOCUMENT ENDS**

**Author:** FLOYD v4.0.0
*"Document the journey so others can follow the path."*
