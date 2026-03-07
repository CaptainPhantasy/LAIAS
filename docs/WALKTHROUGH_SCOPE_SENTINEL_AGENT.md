# Walkthrough Testing Procedure: The Scope Sentinel Agent

**Document Version:** 1.1  
**Date:** 2026-03-07  
**Target Application:** LAIAS (Legacy AI Agent Studio)  
**Agent Under Test:** The Scope Sentinel — Requirements Architect & Scope Lock Agent

---

## Table of Contents

1. [Test Objective](#1-test-objective)
2. [Prerequisites & Environment Setup](#2-prerequisites--environment-setup)
3. [Phase 1 — Launch & Health Verification](#3-phase-1--launch--health-verification)
4. [Phase 2 — Studio UI: Create the Scope Sentinel Agent](#4-phase-2--studio-ui-create-the-scope-sentinel-agent)
5. [Phase 3 — Code Review & Validation](#5-phase-3--code-review--validation)
6. [Phase 4 — Deploy the Agent](#6-phase-4--deploy-the-agent)
7. [Phase 5 — Control Room: Monitor Execution](#7-phase-5--control-room-monitor-execution)
8. [Phase 6 — Agent Output Verification](#8-phase-6--agent-output-verification)
9. [Phase 7 — Behavioral Acceptance Criteria](#9-phase-7--behavioral-acceptance-criteria)
10. [Appendix A — Complete Agent Description Input](#appendix-a--complete-agent-description-input)
11. [Appendix B — Expected Generated Code Patterns](#appendix-b--expected-generated-code-patterns)
12. [Appendix C — Troubleshooting](#appendix-c--troubleshooting)

---

## 1. Test Objective

Verify end-to-end that the LAIAS platform can:

1. Accept a detailed natural language description of the Scope Sentinel agent
2. Generate production-ready CrewAI Flow code that implements the agent's behavior
3. Validate the generated code against the Godzilla architectural pattern
4. Deploy the agent to an isolated Docker container
5. Monitor execution and retrieve structured output
6. Produce agent output that the user can keep and act upon

The Scope Sentinel agent's mission is to conduct exhaustive initial discovery, lock V1 scope with a deterministic sign-off process, and intercept/catalog all late-stage feature requests into a post-V1 roadmap.

---

## 2. Prerequisites & Environment Setup

### 2.1 System Requirements

| Requirement          | Minimum                           |
|----------------------|-----------------------------------|
| Docker               | Docker Desktop 4.x or Engine 24+  |
| Docker Compose       | v2.20+                            |
| Node.js              | 20+ (for frontend development)    |
| Python               | 3.11+ (for backend development)   |
| Available RAM        | 4 GB minimum, 8 GB recommended    |
| Available Disk       | 10 GB free                        |
| Browser              | Chrome 120+, Firefox 120+, Safari 17+ |
| Stack Auth account   | Free at https://app.stack-auth.com |

### 2.2 Clone & Configure

```bash
# 1. Clone the repository
git clone <repo-url> && cd LAIAS

# 2. Create environment file
cp .env.example .env
```

### 2.3 Generate Security Secrets

Run the following command **three times** and paste each output into `.env`:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

Open `.env` and set these values:

```env
# REQUIRED — Security Secrets
JWT_SECRET_KEY=<paste-first-generated-secret>
POSTGRES_PASSWORD=<paste-second-generated-secret>
ORCHESTRATOR_SECRET_KEY=<paste-third-generated-secret>
REDIS_PASSWORD=<paste-a-strong-password>

# REQUIRED — Stack Auth (frontend authentication)
# Create a project at https://app.stack-auth.com and enable an OAuth provider (GitHub, Google, etc.)
NEXT_PUBLIC_STACK_PROJECT_ID=<your-stack-project-id>
STACK_SECRET_SERVER_KEY=<your-stack-secret-server-key>

# REQUIRED — At least one LLM provider key
OPENAI_API_KEY=sk-your-openai-key-here
# OR
ZAI_API_KEY=your-zai-key-here
# OR
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
```

> **Stack Auth setup:** Go to [app.stack-auth.com](https://app.stack-auth.com), create a project, and enable at least one OAuth provider (GitHub recommended). Copy the Project ID and Secret Server Key into `.env`. Without these, the frontend apps will not build and you cannot proceed with this walkthrough.

> **Important:** The Scope Sentinel agent is complex (multi-agent, stateful, with conditional routing). We recommend using `gpt-4o` or `claude-3-5-sonnet` for generation. Weaker models may produce incomplete code.

### 2.4 Build & Start Services

```bash
# Build the agent runner base image (required before first deployment)
docker-compose build agent-runner

# Start all services
docker-compose up -d

# Wait 15-20 seconds for services to initialize
sleep 20
```

### 2.5 Verify All Services Are Running

```bash
docker-compose ps
```

**Expected output** — all 6 services should show `Up`:

```
NAME                    STATUS
laias-agent-generator   Up
laias-orchestrator      Up  
laias-studio-ui         Up
laias-control-room      Up
laias-postgres          Up
laias-redis             Up
```

---

## 3. Phase 1 — Launch & Health Verification

### Step 1: Check Backend Health

Open a terminal and run:

```bash
# Agent Generator health check
curl -s http://localhost:4521/health | python3 -m json.tool

# Docker Orchestrator health check
curl -s http://localhost:4522/health | python3 -m json.tool
```

**Expected Response (Agent Generator):**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 25.3,
  "llm_status": {
    "openai": "ok"
  },
  "database_status": "ok",
  "redis_status": "ok"
}
```

**Pass Criteria:**
- [ ] `status` is `"healthy"`
- [ ] At least one LLM provider shows `"ok"` (this is the provider you'll use for generation)
- [ ] `database_status` is `"ok"`
- [ ] `redis_status` is `"ok"`

> **If any service shows degraded/unhealthy:** Check the logs with `docker-compose logs <service-name>`. Common issues: missing API keys, database connection failures, Redis authentication errors.

### Step 2: Open Frontend Applications & Sign In

Open two browser tabs:

| Application   | URL                          | Expected Result                    |
|---------------|------------------------------|------------------------------------|
| Studio UI     | http://localhost:4527        | Redirects to Stack Auth sign-in page |
| Control Room  | http://localhost:4528        | Redirects to Stack Auth sign-in page |

Both apps require authentication. You will be redirected to the Stack Auth sign-in page at `/handler/sign-in`.

**To sign in:**

1. Click your configured OAuth provider button (e.g., "Sign in with GitHub")
2. Complete the OAuth flow in the popup/redirect
3. You will be redirected back to the application

After signing in to each app:

| Application   | Expected Result After Login                    |
|---------------|-------------------------------------------------|
| Studio UI     | Landing page with "Build AI Agents with Natural Language" hero |
| Control Room  | Dashboard with KPI cards (0 containers initially)              |

> **Note:** You must sign in to each app separately since they run on different ports. Your session persists via cookies, so you only need to sign in once per browser session.

**Pass Criteria:**
- [ ] Both apps redirect to Stack Auth sign-in when accessed without a session
- [ ] OAuth sign-in completes successfully
- [ ] Studio UI loads after login — hero section visible with "Create Agent" button
- [ ] Control Room loads after login — dashboard shows "Total Containers: 0"
- [ ] No console errors in browser DevTools (F12 → Console tab)

---

## 4. Phase 2 — Studio UI: Create the Scope Sentinel Agent

### Step 1: Navigate to Agent Builder

> **Prerequisite:** You must be signed in to Studio UI (see [Phase 1, Step 2](#step-2-open-frontend-applications--sign-in)).

1. In the Studio UI (http://localhost:4527), click the **"Create Agent"** button in the hero section
   - OR click **"Create Agent"** in the left sidebar navigation (plus-circle icon)
2. You will be navigated to `http://localhost:4527/create`

**What You Should See:**

A three-column layout:
- **Left**: Section navigation (Description, Type, Tools, Output, Advanced)
- **Center**: Form with sections
- **Right**: Code Preview panel showing "Generated code will appear here"

The top bar displays:
- Title: **"Create Agent"**
- Two buttons on the right: **"Validate"** (disabled) and **"Deploy"** (disabled)

**Pass Criteria:**
- [ ] Three-column layout renders correctly
- [ ] Code preview panel shows empty state with sparkles icon
- [ ] "Validate" and "Deploy" buttons are disabled (no code generated yet)
- [ ] Section navigation shows 5 numbered sections

---

### Step 2: Enter the Agent Description

In the **Description** section (Section 1, cyan accent bar), locate the textarea with placeholder text:

> *"Describe your AI agent in natural language. Be specific about what it should do, what tools it needs, and how it should behave."*

**Action:** Copy and paste the full Scope Sentinel agent description below into the textarea.

> **Note:** The complete description is provided in [Appendix A](#appendix-a--complete-agent-description-input). It is critical to paste the **entire description** — the LLM needs all context about the typed state, event-driven logic, prompt constraints, and self-correction behavior to produce correct code.

**Paste the following into the Description textarea:**

```
Create "The Scope Sentinel" agent — an elite requirements architect for a software consulting firm.

MISSION: Conduct exhaustive initial client discovery, lock the V1 scope with an unyielding deterministic sign-off process, and intercept/catalog all late-stage feature requests into a post-V1 roadmap.

TYPED STATE (Pydantic-validated AgentState):
- client_id (str): Unique identifier for the client or sales ticket
- core_objectives (List[str]): Primary business goals for the software
- v1_scope_items (List[str]): Features explicitly approved for V1
- future_roadmap (List[str]): Features cataloged for V1.1+ (quarantined)
- v1_scope_locked (bool, default False): True when client signs off on V1
- client_signoff_status (str, default "pending"): One of "pending", "revisions_requested", "officially_signed"
- discovery_iterations (int, default 0): Number of back-and-forth discovery loops
- error_count (int, default 0): Tracks failures in getting alignment or sign-off
- cost_limit_usd (float, default 5.00): Safety limit for token spend
- intermediate_results (Dict): Stores pain point history and raw chat logs

EVENT-DRIVEN LOGIC:
1. @start(trigger="initial_client_handoff"): Triggers the "Deep Excavation" protocol. Ingest initial sales brief, output rigorous questionnaire to uncover hidden requirements, edge cases, and unspoken assumptions. Log: "Deep Excavation initiated."
2. @router(evaluate_discovery): If discovery_iterations < 3 AND ambiguity remains → route to Follow-Up Interrogation. If ambiguity resolved → route to Generate V1 Blueprint.
3. @listen("Generate V1 Blueprint"): Compile V1 specs and formally request client signature/approval. Require client to reply "APPROVED" to lock scope.
4. @listen("new_feature_request_received"): Check v1_scope_locked. If False → evaluate if feature belongs in V1 or pushes timeline. If True → automatically append to future_roadmap and respond: "Excellent idea. I have cataloged this in our Phase 2 Roadmap to ensure your V1 delivery remains on schedule."

SYSTEM PROMPT CONSTRAINTS:
- Role: "You are The Scope Sentinel, the elite requirements architect for Legacy AI MicroSaaS Solutions."
- Must ask probing edge-case questions during discovery ("What happens if a user inputs X?", "How do you want to handle Y failure?")
- Once V1 Blueprint generated, require explicit "APPROVED" confirmation to lock scope
- After scope lock, NEVER add new features to V1 — acknowledge value, log to Phase 2
- Maintain professional, consultative, but unyielding tone — protect developer velocity

SELF-CORRECTION LOGIC:
- If discovery_iterations >= 3 OR error_count > 0: workflow is at risk of infinite loop
- Trigger prompt adaptation: shift from "open discovery" to "forced prioritization"
- New prompt: "We have reached our discovery limit. Please select the top 3 features from this list that are strictly necessary for launch. The rest will be moved to Phase 2."
- Persist cause of error (e.g., "Client indecision regarding auth flow") to intermediate_results["pain_point_history"]

Include memory for context retention across discovery iterations. Include analytics for cost tracking. Use 3-4 specialized agents: a Discovery Interviewer, a Requirements Compiler, a Scope Guardian, and optionally a Prioritization Facilitator.
```

**What You Should See:**
- Character counter below the textarea updates (approximately 2,200/5,000 characters)
- No validation errors (description exceeds the 10-character minimum)
- The five **"Try a prompt"** suggestion buttons appear below but are not relevant for this test — ignore them

**Pass Criteria:**
- [ ] Full description pasted without truncation
- [ ] Character counter shows the correct count
- [ ] No red error text appears below the textarea

---

### Step 3: Configure Agent Type

Scroll down to the **Agent Configuration** section (Section 2, purple accent bar).

Set the following values:

| Field         | Value        | Reason                                                    |
|---------------|--------------|-----------------------------------------------------------|
| **Complexity**  | `Complex`    | Multi-agent, stateful, conditional routing, self-correction |
| **Task Type**   | `Analysis`   | Requirements analysis is the primary function               |
| **Max Agents**  | `4`          | Discovery Interviewer, Requirements Compiler, Scope Guardian, Prioritization Facilitator |

**How to set each field:**
1. Click the **Complexity** dropdown → select **"Complex"**
2. Click the **Task Type** dropdown → select **"Analysis"**
3. Click the **Max Agents** number input → clear it → type **4**

**Pass Criteria:**
- [ ] Complexity shows "Complex"
- [ ] Task Type shows "Analysis"
- [ ] Max Agents shows "4"

---

### Step 4: Select Tools (Optional)

Scroll down to the **Tools** section (Section 3, pink accent bar).

The Scope Sentinel is primarily a conversational/reasoning agent. It does not require external tools like web scrapers or database connectors. However, selecting a few tools can enhance its capabilities.

**Recommended tool selection** (click each tile to toggle it on — a cyan border and checkmark will appear):

| Tool               | Category | Purpose for Scope Sentinel                    |
|---------------------|----------|-----------------------------------------------|
| `FileReadTool`      | Files    | Read uploaded sales briefs or requirement docs |
| `JSONSearchTool`    | Files    | Parse structured client intake forms           |

**To select a tool:**
1. Scroll through the tools grid, or click the **"files"** category tab to filter
2. Click on the **FileReadTool** tile — it should highlight with a cyan border and checkmark
3. Click on the **JSONSearchTool** tile — same behavior

**What You Should See:**
- A summary bar appears below the tools grid: **"2 tools selected"** (in cyan)

**Pass Criteria:**
- [ ] Selected tools show cyan border with checkmark icon
- [ ] Summary bar shows correct count
- [ ] Unselected tools remain gray

> **Note:** Tool selection is optional. The agent will still generate successfully with zero tools selected. Skip this step if you want to test the minimal configuration.

---

### Step 5: Configure Output Settings

Scroll down to the **Output Configuration** section (Section 4).

| Field              | Value                          | Notes                                  |
|--------------------|--------------------------------|----------------------------------------|
| **Output Path**      | Leave empty or set custom path | Default will be auto-assigned          |
| **Output Format**    | `Markdown`                     | Default — readable scope documents     |
| **Save to Database** | ☑ Checked                      | Persist structured events in PostgreSQL |
| **Save to Files**    | ☑ Checked                      | Write artifacts to output directory     |

**Pass Criteria:**
- [ ] Both output destinations remain checked
- [ ] Output format is "Markdown"

---

### Step 6: Configure LLM Provider (Advanced Options)

Click on the **Advanced Options** section header (Section 5) to expand it. A chevron icon will rotate to indicate the expanded state.

Set the following:

| Field           | Value        | Reason                                                     |
|-----------------|--------------|-------------------------------------------------------------|
| **LLM Provider** | `OpenAI`     | Best code generation quality for complex agents              |
| **Model**        | `gpt-4o`     | Highest capability model — needed for multi-agent generation |

> **Alternative:** If using Anthropic, select `Anthropic` → `claude-3-5-sonnet`. If using ZAI, select `ZAI (Default)` → `default`.

**Pass Criteria:**
- [ ] Advanced Options section is expanded
- [ ] LLM Provider shows selected provider
- [ ] Model dropdown updates to show models for the selected provider
- [ ] Selected model is appropriate for complex code generation

---

### Step 7: Generate the Agent

1. Scroll down to the bottom of the form
2. Click the **"Generate Agent"** button (full-width, cyan, with sparkles icon)

**What You Should See — Generation Progress:**

The button text and code panel update through four states:

| State       | Button Text          | Code Panel Status     | Duration (typical) |
|-------------|----------------------|----------------------|---------------------|
| Analyzing   | "Analyzing..."       | "Ready to generate"  | 1-2 seconds         |
| Generating  | "Generating..."      | "Generating..."      | 30-90 seconds       |
| Validating  | "Validating..."      | "Validating..."      | 2-5 seconds         |
| Complete    | "Generate Agent"     | "Complete" (green ✓) | —                   |

> **Important:** Generation for a complex agent typically takes 30-90 seconds depending on the LLM provider. Do **not** navigate away or refresh the page during generation.

**If Generation Fails:**
- A red error message appears below the Generate button
- Common causes: LLM provider API key invalid, rate limit exceeded, timeout
- Fix: Check `.env` for correct API key, wait and retry
- The button re-enables — you can click "Generate Agent" again

**Pass Criteria:**
- [ ] Button shows animated progress text through each state
- [ ] Code panel shows spinning status indicator during generation
- [ ] After completion, code appears in the right panel
- [ ] Status indicator shows green checkmark with "Complete"
- [ ] No error message appears below the button
- [ ] "Validate" button in the top bar becomes enabled

---

## 5. Phase 3 — Code Review & Validation

### Step 1: Review Generated Code (flow.py Tab)

After generation completes, the **Code Preview Panel** (right column) displays the generated code in a Monaco editor with syntax highlighting.

The editor has **four tabs** across the top:

| Tab              | Language | Contains                                          |
|------------------|----------|---------------------------------------------------|
| `flow.py`        | Python   | The main Flow class — core orchestration logic     |
| `agents`         | YAML     | Agent role/goal/backstory definitions              |
| `state`          | Python   | The `AgentState` Pydantic model                    |
| `requirements`   | Text     | Python package dependencies                        |

**Click the `flow.py` tab** (should be active by default).

**Verify the following patterns exist in the generated code:**

#### A. Imports Section
Look for these critical imports at the top:
```python
from crewai.flow.flow import Flow, listen, start, router
from pydantic import BaseModel, Field
import structlog
```

#### B. AgentState Class
Verify the state class contains the fields from the agent description:
```python
class AgentState(BaseModel):
    client_id: str = Field(...)
    core_objectives: list[str] = Field(default_factory=list)
    v1_scope_items: list[str] = Field(default_factory=list)
    future_roadmap: list[str] = Field(default_factory=list)
    v1_scope_locked: bool = Field(default=False)
    client_signoff_status: str = Field(default="pending")
    discovery_iterations: int = Field(default=0)
    error_count: int = Field(default=0)
    cost_limit_usd: float = Field(default=5.00)
    intermediate_results: dict = Field(default_factory=dict)
```

#### C. Flow Class Structure
Verify the Flow class uses the Godzilla pattern:
```python
class ScopeSentinelFlow(Flow[AgentState]):  # or similar name
    @start()
    async def initialize(self):     # Entry point
        ...
    
    @listen("initialize")           # Deep Excavation protocol
    async def deep_excavation(self):
        ...
    
    @router(deep_excavation)        # Conditional routing
    def evaluate_discovery(self):
        ...
    
    @listen("generate_v1_blueprint")
    async def generate_blueprint(self):
        ...
    
    @listen("new_feature_request")  # Scope lock enforcement
    async def handle_feature_request(self):
        ...
```

#### D. Self-Correction Logic
Look for the forced prioritization fallback:
```python
if self.state.discovery_iterations >= 3 or self.state.error_count > 0:
    # Switch to forced prioritization mode
    ...
```

#### E. Scope Lock Enforcement
Look for the post-lock feature request handling:
```python
if self.state.v1_scope_locked:
    self.state.future_roadmap.append(feature)
    # "Cataloged in Phase 2 Roadmap"
```

**Pass Criteria:**
- [ ] Code is syntactically valid Python (no red squiggly underlines in editor)
- [ ] Flow class extends `Flow[AgentState]`
- [ ] `@start()` decorator present on entry point method
- [ ] `@listen()` decorators chain methods together
- [ ] `@router()` decorator implements conditional branching
- [ ] AgentState contains all specified fields
- [ ] Self-correction logic present (discovery_iterations check)
- [ ] Scope lock enforcement present (v1_scope_locked check)
- [ ] Error handling with try/except blocks present
- [ ] structlog logging statements present

### Step 2: Review agents.yaml Tab

Click the **`agents`** tab in the code panel.

**Verify 3-4 agent definitions exist:**

| Agent Name                   | Expected Role                          |
|------------------------------|----------------------------------------|
| Discovery Interviewer        | Conducts deep client discovery sessions |
| Requirements Compiler        | Compiles and structures V1 specifications |
| Scope Guardian               | Enforces scope lock, quarantines late requests |
| Prioritization Facilitator   | Facilitates forced prioritization when discovery stalls (optional) |

Each agent should have:
- `role:` — title/function
- `goal:` — what the agent aims to achieve
- `backstory:` — context for agent personality and expertise
- `tools:` — list of tools (if applicable)

**Pass Criteria:**
- [ ] At least 3 agents defined
- [ ] Each agent has role, goal, and backstory fields
- [ ] Agent roles align with the Scope Sentinel's mission

### Step 3: Review state.py Tab

Click the **`state`** tab. Verify the `AgentState` Pydantic model matches the typed state definition from the description.

**Pass Criteria:**
- [ ] All 10 state fields present with correct types and defaults

### Step 4: Review requirements.txt Tab

Click the **`requirements`** tab. Verify these minimum dependencies:

```
crewai[tools]>=0.80.0
pydantic>=2.5.0
structlog>=24.0.0
```

**Pass Criteria:**
- [ ] `crewai` present with tools extra
- [ ] `pydantic` present (v2+)
- [ ] `structlog` present

### Step 5: Run Validation

Click the **"Validate"** button in the top bar (to the left of "Deploy").

**What You Should See:**

The validation panel at the bottom of the code preview updates:

| Metric          | Expected Value     | Meaning                                    |
|-----------------|--------------------|--------------------------------------------|
| Quality Score   | 70-100 (green)     | Pattern compliance percentage              |
| Patterns        | ✓ (green check)    | Godzilla pattern requirements met           |
| Warnings        | 0-3 warnings       | Non-critical improvement suggestions        |
| Errors          | 0 errors           | No syntax or structural errors             |

**If Validation Fails (score < 70 or errors present):**
1. Read the error messages in the validation panel
2. You can manually edit the code in the Monaco editor to fix issues
3. Click "Validate" again after making changes
4. Common issues:
   - Missing `@start()` decorator
   - Missing error handling
   - Missing structlog usage

**Pass Criteria:**
- [ ] Quality score is 70 or above
- [ ] Patterns indicator shows green checkmark
- [ ] Zero errors reported
- [ ] "Deploy" button in the top bar becomes **enabled** (cyan, clickable)

---

## 6. Phase 4 — Deploy the Agent

### Step 1: Click Deploy

With validation passing, click the **"Deploy"** button in the top bar (cyan button with arrow-right icon).

**What Happens Behind the Scenes:**

```
Studio UI → POST /api/deploy (Agent Generator)
  → Agent Generator proxies to Docker Orchestrator
    → Creates container from laias/agent-runner image
    → Mounts generated code as read-only volume
    → Sets environment variables (API keys, task config)
    → Starts container (auto_start: true)
  ← Returns deployment response with container_id
```

**What You Should See:**

1. The button text changes to indicate progress
2. After 5-10 seconds, a **new browser tab** opens automatically to the Control Room:
   ```
   http://localhost:4528?agent=<container_id>
   ```
3. The original Studio UI tab shows "Complete" status

**If Deployment Fails:**
- A red error message appears below the Deploy button
- Common causes:
  - Agent runner image not built (`docker-compose build agent-runner`)
  - Docker orchestrator not running
  - Resource limit exceeded (too many containers)
- Check orchestrator logs: `docker-compose logs docker-orchestrator`

**Pass Criteria:**
- [ ] No error message after clicking Deploy
- [ ] New browser tab opens to Control Room
- [ ] Status returns to "Complete" in Studio UI

---

## 7. Phase 5 — Control Room: Monitor Execution

### Step 1: Verify Dashboard Update

Switch to the Control Room tab (http://localhost:4528).

**What You Should See on the Dashboard:**

The KPI cards at the top should update:

| KPI Card          | Expected Value |
|-------------------|----------------|
| Total Containers  | 1 (or +1 from before) |
| Running           | 1              |
| Stopped           | 0              |
| Errors            | 0              |

**Pass Criteria:**
- [ ] At least 1 container shows as "Running"
- [ ] No containers in "Error" state

### Step 2: Locate the Scope Sentinel Container

In the container grid below the KPI cards (or navigate to the **Containers** page via the sidebar), locate the newly deployed container card.

**Container Card should display:**

| Element        | Expected Value                         |
|----------------|----------------------------------------|
| Agent Name     | Contains "ScopeSentinel" or similar    |
| Status Badge   | 🟢 "running" (green)                  |
| CPU Usage      | 0-100% (updating every 5 seconds)      |
| Memory Usage   | Under 512 MB                           |
| Uptime         | Incrementing ("0m", "1m", "2m"...)    |

**Quick Action Buttons visible on the card:**
- **Stop** (square icon) — stops the container
- **Restart** (refresh icon) — restarts the container
- **View Logs** (file icon) — opens log viewer
- **View Metrics** (activity icon) — opens metrics charts

**Pass Criteria:**
- [ ] Container card visible with correct agent name
- [ ] Status badge shows green "running"
- [ ] Resource metrics are updating live
- [ ] All four quick action buttons are present

### Step 3: View Real-Time Logs

Click the **"View Logs"** button (file icon) on the container card, or click the container name to open the detail page and navigate to the logs tab.

**What You Should See:**

A log viewer panel with:
1. **Connection Status**: Green "Connected" badge (top right)
2. **Log Filter**: Buttons for DEBUG, INFO, WARNING, ERROR level filtering
3. **Search**: Text input to filter log messages
4. **Log Stream**: Lines appearing in real-time as the agent executes

**Expected Log Entries (in chronological order):**

```
[INFO]  Run started - Scope Sentinel initializing
[INFO]  Deep Excavation initiated. Awaiting client discovery responses.
[INFO]  Task started: Discovery Interviewer analyzing sales brief
[DEBUG] LLM call: Generating discovery questionnaire
[INFO]  Discovery questionnaire generated (iteration 1)
[INFO]  Task completed: Initial discovery questions prepared
...
[INFO]  Run completed - Scope Sentinel execution finished
```

**Pass Criteria:**
- [ ] Log stream connects (green "Connected" badge)
- [ ] Logs appear in real-time
- [ ] Logs contain structlog-formatted entries with timestamps
- [ ] "Deep Excavation" message appears in logs (verifies the agent's initialization)
- [ ] No ERROR-level entries (unless expected from self-correction logic)
- [ ] Level filter buttons work (click ERROR → only error logs shown)
- [ ] Search filter works (type "Discovery" → only matching logs shown)

### Step 4: Monitor Resource Metrics

If viewing the container detail page, check the **Metrics** section:

| Metric          | Expected Range    | Update Interval |
|-----------------|-------------------|-----------------|
| CPU Usage       | 5-80%             | Every 5 seconds |
| Memory Usage    | 50-400 MB         | Every 5 seconds |
| Network I/O     | Active during LLM calls | Every 5 seconds |

**Pass Criteria:**
- [ ] CPU usage chart shows activity during execution
- [ ] Memory stays within the 512 MB limit
- [ ] Metrics update at regular intervals

### Step 5: Wait for Execution to Complete

The Scope Sentinel agent will execute its Flow pipeline. Depending on the number of discovery iterations and LLM response times, this may take **2-10 minutes**.

**Container Status Transitions:**
```
running → (agent executes all Flow stages) → exited/stopped
```

When the agent completes:
- Container status changes from 🟢 "running" to ⚪ "stopped"
- The "Stop" button is replaced by a "Start" button
- Final logs show `run_completed` event

**Pass Criteria:**
- [ ] Container eventually transitions to "stopped" status
- [ ] Final log entry shows run completion (not a crash/error)
- [ ] Dashboard KPI updates: Running decreases by 1, Stopped increases by 1

---

## 8. Phase 6 — Agent Output Verification

### Step 1: Retrieve Output Artifacts

After the agent completes, its output files are stored in the container's output volume.

**From the Control Room**, click on the container to view its detail page. Look for the **Output Artifacts** section which lists completed runs.

Each run produces three files:

| File             | Format     | Contents                                              |
|------------------|------------|-------------------------------------------------------|
| `events.jsonl`   | JSON Lines | Structured event log — one JSON object per line       |
| `summary.md`     | Markdown   | Human-readable execution summary                      |
| `metrics.json`   | JSON       | Cost, token usage, API call count, duration            |

### Step 2: Verify Output Content

**The agent's output should contain these artifacts for the user to keep:**

#### A. Discovery Questionnaire
A comprehensive list of probing questions generated by the Discovery Interviewer agent, such as:
- "What happens if a user inputs invalid data in the registration form?"
- "How should the system handle concurrent editing conflicts?"
- "What is your expected peak traffic volume?"
- "Are there regulatory compliance requirements (GDPR, HIPAA, SOC2)?"

#### B. V1 Blueprint Document
A structured requirements document containing:
- Client objectives
- Approved V1 scope items (features for initial release)
- Technical requirements and constraints
- Acceptance criteria for each feature
- Timeline estimates

#### C. Future Roadmap
A list of features explicitly quarantined for post-V1:
- Feature name
- Business justification
- Priority ranking
- Phase assignment (V1.1, V2, etc.)

#### D. Pain Point History
A log of discovery challenges stored in `intermediate_results["pain_point_history"]`:
- Which topics caused client indecision
- How many iterations were needed per topic
- Resolution approach used

### Step 3: Verify Execution Metrics

Check `metrics.json` for cost and performance data:

```json
{
  "total_cost": 0.15,        // Should be under cost_limit_usd ($5.00)
  "api_calls": 8,            // Number of LLM calls made
  "tokens_used": 12500,      // Total token consumption
  "start_time": "2026-03-07T10:30:22Z",
  "end_time": "2026-03-07T10:35:45Z"
}
```

**Pass Criteria:**
- [ ] `total_cost` is under the $5.00 safety limit
- [ ] Output files exist and are non-empty
- [ ] Discovery questionnaire contains probing edge-case questions
- [ ] V1 Blueprint document is structured with clear scope items
- [ ] Future roadmap section exists (may be empty if no post-V1 features were generated)
- [ ] `summary.md` provides a human-readable narrative of what the agent did

---

## 9. Phase 7 — Behavioral Acceptance Criteria

These criteria verify the Scope Sentinel agent **behaves correctly** according to its mission. During testing, verify these behaviors either through log analysis or by modifying the agent's input to trigger specific scenarios.

### Criterion 1: Deep Excavation Protocol

| Behavior | Verification Method |
|----------|---------------------|
| Agent generates probing discovery questions | Check output for questionnaire with edge-case scenarios |
| Questions cover hidden requirements | Look for "What happens if..." and "How do you handle..." patterns |
| Discovery iterations are tracked | Check `AgentState.discovery_iterations` increments in logs |

### Criterion 2: Conditional Routing

| Behavior | Verification Method |
|----------|---------------------|
| If ambiguity remains AND iterations < 3 → follow-up interrogation | Log shows routing to follow-up questions |
| If ambiguity resolved → generate V1 Blueprint | Log shows routing to blueprint generation |
| If iterations >= 3 → forced prioritization | Log shows switch to "select top 3 features" mode |

### Criterion 3: V1 Scope Lock

| Behavior | Verification Method |
|----------|---------------------|
| Blueprint requires explicit "APPROVED" to lock | Output contains approval prompt text |
| `v1_scope_locked` transitions from False to True | State change visible in logs |
| `client_signoff_status` updates to "officially_signed" | State change visible in logs |

### Criterion 4: Post-Lock Feature Quarantine

| Behavior | Verification Method |
|----------|---------------------|
| New features after scope lock are quarantined | Feature appended to `future_roadmap` (not `v1_scope_items`) |
| Response includes Phase 2 acknowledgment | Output contains "cataloged in our Phase 2 Roadmap" |
| V1 scope items remain unchanged after lock | `v1_scope_items` list does not grow after lock |

### Criterion 5: Self-Correction Logic

| Behavior | Verification Method |
|----------|---------------------|
| After 3+ iterations, prompt shifts to forced prioritization | Log shows prompt adaptation |
| Pain points are persisted | `intermediate_results["pain_point_history"]` populated |
| Error cause is recorded | Specific indecision reason logged |

### Criterion 6: Cost Safety

| Behavior | Verification Method |
|----------|---------------------|
| Total cost stays under `cost_limit_usd` ($5.00) | Check `metrics.json` total_cost field |
| Analytics service tracks API calls | `api_calls` and `tokens_used` are non-zero |

---

## 10. Interface Expectations Summary

This section describes what the tester can expect to see at each stage of interacting with the agent through the LAIAS platform.

### Studio UI (http://localhost:4527)

| Stage | What You See | What You Do |
|-------|-------------|-------------|
| Sign In | Stack Auth sign-in page with OAuth provider buttons | Click your OAuth provider, complete sign-in |
| Landing Page | Hero with "Build AI Agents" headline, 3 feature cards | Click "Create Agent" |
| Create Page | 3-column layout: navigation, form, code preview | Fill in agent description and configuration |
| Form | Description textarea, dropdowns for complexity/type, tool grid, output config, advanced LLM settings | Configure all sections |
| Generating | Animated button text ("Analyzing..." → "Generating..." → "Validating..."), code panel spinner | Wait 30-90 seconds |
| Complete | Generated Python code in Monaco editor with syntax highlighting, validation score panel | Review code, click Deploy |
| Deployed | New tab opens to Control Room | Switch to Control Room tab |

### Control Room (http://localhost:4528)

| Stage | What You See | What You Do |
|-------|-------------|-------------|
| Sign In | Stack Auth sign-in page with OAuth provider buttons | Click your OAuth provider, complete sign-in |
| Dashboard | KPI cards (Total, Running, Stopped, Errors), system health status | Verify container count increased |
| Container Grid | Card with agent name, green "running" badge, CPU/memory metrics, action buttons | Click container for details |
| Container Detail | Full metrics charts, output artifacts list, log viewer | Monitor execution progress |
| Log Viewer | Real-time scrolling log entries with level/timestamp/message, filter controls | Filter by level, search for key events |
| Completed | Container status changes to "stopped", output artifacts available | Download/view output files |

### Agent Output (User-Keepable Artifacts)

| Artifact | Format | User Value |
|----------|--------|------------|
| Discovery Questionnaire | Markdown sections | Use as client intake template for future projects |
| V1 Blueprint | Structured document | Share with development team as spec |
| Future Roadmap | Prioritized list | Use for release planning beyond V1 |
| Pain Point History | JSON log | Retrospective on difficult discovery areas |
| Execution Summary | Markdown narrative | Documentation of the requirements process |
| Cost Metrics | JSON | Track spend per client engagement |

---

## Appendix A — Complete Agent Description Input

Copy the entire text block from [Step 2 of Phase 2](#step-2-enter-the-agent-description) into the Studio UI description textarea. The description is approximately 2,200 characters and covers:

1. Mission statement
2. Typed state definition (10 Pydantic fields)
3. Event-driven logic (4 event handlers with routing)
4. System prompt constraints (5 rules)
5. Self-correction logic (iteration limit, prompt adaptation)
6. Agent team composition (4 specialized agents)

---

## Appendix B — Expected Generated Code Patterns

The LLM-generated code should follow the Godzilla architectural pattern. Below are the **minimum required patterns** that the LAIAS validator checks:

| Pattern | Regex Checked | Required? |
|---------|---------------|-----------|
| Flow base class | `class \w+\(Flow\[` | ✅ Yes |
| Start decorator | `@start\(\)` | ✅ Yes |
| Listen decorator | `@listen\(` | ✅ Yes |
| Typed state | `class \w+State\(BaseModel\)` | ✅ Yes |
| Agent factory methods | `def _create_\w+_agent\(self\)` | ✅ Yes |
| Error handling | `try:` | ✅ Yes |
| Structured logging | `logger\.` | ✅ Yes |
| Output router | `OutputRouter` | ✅ Yes |
| Router decorator | `@router\(` | ⚡ Recommended |
| Analytics service | `AnalyticsService` | ⚡ Recommended |
| Async methods | `async def` | ⚡ Recommended |

A **compliance score of 0.80 or higher** (80%+) is required for the "Deploy" button to enable.

---

## Appendix C — Troubleshooting

### Problem: Generation takes more than 2 minutes

**Cause:** LLM provider is slow or rate-limited.  
**Fix:** Check LLM provider status page. Try switching to a different provider in Advanced Options. Retry generation.

### Problem: "Generation failed" error

**Cause:** LLM API key is invalid, expired, or has insufficient credits.  
**Fix:** Verify the API key in `.env`. Check your provider dashboard for billing/quota. Restart services after changing `.env`:
```bash
docker-compose down && docker-compose up -d
```

### Problem: Validation score below 70

**Cause:** LLM generated code missing required Godzilla patterns.  
**Fix:** 
1. Read the missing patterns listed in the validation panel
2. Manually add the missing patterns in the Monaco editor
3. Click "Validate" to re-check
4. Alternatively, adjust the description and regenerate

### Problem: Deploy button stays disabled

**Cause:** Validation has not passed (score too low or errors present).  
**Fix:** Click "Validate" first. Address any errors. Ensure `is_valid = true` before deploying.

### Problem: Container shows "Error" status

**Cause:** Generated code has a runtime error (import failure, syntax issue not caught by static validation, missing environment variable).  
**Fix:** 
1. Check container logs in the Control Room
2. Look for Python traceback in the log stream
3. Fix the code in Studio UI and redeploy
4. Common: missing API key environment variable — ensure LLM keys are passed to container

### Problem: New browser tab doesn't open on Deploy

**Cause:** Browser popup blocker is preventing the new tab.  
**Fix:** Allow popups from `localhost:4527` in your browser settings. Or manually navigate to `http://localhost:4528` and find the new container in the grid.

### Problem: "No code to deploy" error

**Cause:** Clicked Deploy before generating code.  
**Fix:** Generate the agent first (click "Generate Agent"), wait for completion, then deploy.

### Problem: Frontend redirects to sign-in but OAuth buttons don't work

**Cause:** Stack Auth project not configured with an OAuth provider, or project ID/server key incorrect.  
**Fix:**
1. Go to [app.stack-auth.com](https://app.stack-auth.com) and open your project
2. Navigate to Auth Methods and enable at least one OAuth provider (GitHub, Google)
3. Verify `NEXT_PUBLIC_STACK_PROJECT_ID` and `STACK_SECRET_SERVER_KEY` in `.env` match your project
4. Rebuild the frontends: `docker-compose up -d --build studio-ui control-room`

### Problem: Frontend shows "project ID not provided" build error

**Cause:** `NEXT_PUBLIC_STACK_PROJECT_ID` is missing from the environment during build.  
**Fix:** Ensure the variable is set in `.env` (root) and in `frontend/studio-ui/.env.local` / `frontend/control-room/.env.local`. Then rebuild.

### Problem: Control Room shows 0 containers after deployment

**Cause:** Docker Orchestrator may not be connected to Docker daemon.  
**Fix:** 
```bash
# Check Docker daemon is running
docker ps

# Check orchestrator logs
docker-compose logs docker-orchestrator

# Verify Docker socket is mounted
docker-compose exec docker-orchestrator ls -la /var/run/docker.sock
```

---

*End of Walkthrough Testing Procedure*
