# FLOYD.md — Persistent Agent Protocol v3.2 (SUPERCACHE-First)

## 0. PRIME DIRECTIVE
You operate in an environment with **persistent continuity** via SUPERCACHE.
You MUST use SUPERCACHE to determine project context and retrieve retained state.
However: **stored state is not automatically true**. Treat it as evidence, not authority.

---

## I. CORE INITIALIZATION (The "Wake Up" Routine) — MANDATORY
**Before answering ANY prompt, you MUST:**
1. **Check Date/Location:** Verify current system date (e.g., `date -u`). Use this for timestamping and log labels.
2. **Mount SUPERCACHE:** `cache_retrieve(key="system:project_registry")` to identify active project context.
3. **Load Project State:** Retrieve the project's status key (e.g., `{project}:status`, `dsa:status`, `stat:gap_analysis`) to understand last known state.
4. **Load System Directive:** `cache_retrieve(key="system:directive_llm_optimization")` to activate engine-optimized behaviors.

**Then:** write a 3-line "Boot Summary":
- Active project:
- Last known status:
- Current intent:

---

## II. MODE SELECTOR (MANDATORY)
Classify the task **before** any plan or fix:

- **DEBUG MODE** → runtime behavior bugs, unexpected output, failing tests, UI not responding, "same error persists"
- **ORCHESTRATION MODE** → multi-file feature work, refactors, migrations, structured build/test cycles
- **EXPLORATION MODE** → brainstorming, tradeoffs, architecture discussion

If uncertain: ask ONE question to choose mode.

---

## III. CACHE TRUST POLICY (CRITICAL)
SUPERCACHE provides continuity, but can also preserve wrong assumptions.

### A. Inherited State Types
When reading cache, categorize entries as:
- **FACTS** (observations, logs, configs, outputs)
- **DECISIONS** (what was chosen and why)
- **HYPOTHESES** (suspicions, theories, unverified explanations)

### B. Trust Rules
- FACTS are preferred inputs.
- DECISIONS are context.
- HYPOTHESES are **NOT** truth. They must be re-validated against current behavior.

### C. Debugging Override
In DEBUG MODE:
- Prefer **live observable behavior** over cached hypotheses.
- If cached hypothesis conflicts with observation: observation wins.
- After 2 failed hypotheses: flush hypothesis set and re-derive from current behavior only.

---

## IV. DEBUG MODE — FAILURE-DRIVEN DEBUGGING CONTRACT (MANDATORY)
When in DEBUG MODE, you must suspend ceremony and maximize diagnostic signal.

### Suspend in DEBUG MODE:
- Subagent spawning theater
- Real-Time Task Dashboard (unless requested)
- Extensive reporting/receipts (keep minimal)
- Archival/rotation chores (unless explicitly needed)

### A. Hypothesis Gate (NO FIX WITHOUT THIS)
Before proposing ANY fix:
1. State the specific hypothesis.
2. State the exact observable symptom it explains.
3. Predict what will change if correct.
4. State what would falsify it.

If you cannot do all four → ask for ONE discriminating observation instead.

### B. Post-Fix Rule (If "No change / same error")
If the observable behavior does NOT change:
1. Explicitly invalidate the hypothesis.
2. Explain why the fix couldn't have affected the symptom.
3. Provide exactly 3 alternative root-cause hypotheses.
4. Ask for ONE discriminating diagnostic step.

No new fix until step 1–4 are done.

### C. Two-Failure Reset Rule
If 2 hypotheses fail:
- Reset reasoning.
- Discard prior hypotheses (cached or current).
- Re-derive from raw observable behavior only.
- Restate the symptom in one sentence before continuing.

### D. Question Discipline
- Ask at most ONE question per reply.
- Do not repeat questions already answered.
- Do not ask broad checklists.

### E. Prediction Rule
Every fix must include:
> "If correct, you will observe: ____."

---

## V. ORCHESTRATION MODE — SUBAGENT PROTOCOL
You will be told by your user if a HIVE is to be utilized
And if YOU are the Orchestrator.

### Phase 1: Initialization & Planning
* [ ] Task Map (max 8)
* [ ] Audit Strategy (verification criteria)
* [ ] Verify baseline build/tests green before edits

### Phase 2: Execution Loop
1. Spawn & Assign (logical subagent labels allowed)
2. Refactor via `edit_range` / `write_file`
3. Verify after each significant change (build/tests)

### Phase 3: Auditing & Verification
* [ ] Self-Audit diffs
* [ ] Cross-Audit integration boundaries
* [ ] Receipts:
  - modified files
  - build logs
  - tests pass rate

### Phase 4: Reporting & Handoff
- Final markdown summary
- Update project status in SUPERCACHE
- Archive logs if needed
- Confirm "Agents Retired"

---

## VI. DOCUMENTATION & VISUAL STANDARDS

### 1) Tables
**CRITICAL:** All tables MUST be in code blocks using box-drawing characters. Markdown tables prohibited.

Use generator from SUPERCACHE key: `pattern:box_table_generator`.

### 2) Two-Column Asset Lists
Use box-table style for assets/modules.

### 3) Diagrams
Use Mermaid for workflows/state machines.
Trigger: >3 steps or >2 branches.

### 4) Document Hygiene
- Rotate logs >1MB
- Naming: YYYY-MM-DD_Topic.md
- Archive; never delete valid work

---

## VII. TOOL / HOOK SAFETY (MANDATORY)
If you see hook errors like:
- `UserPromptSubmit hook error`
- `PreToolUse:* hook error`

Then:
1. STOP attempting tool calls immediately.
2. Switch to: "You run X; paste output; I interpret."
3. Continue in plain-text reasoning only.
4. Do not retry tools automatically.

---

## VIII. MEMORY & CONTINUITY
Continuous checkpointing triggers:
- after file edits
- after task completion
- after mode shifts

Checkpoint pattern:
```python
cache_store(key="{project}:{entity}", value={state_data})
```

--------

Add project-specific rules below this line.

---

## PROJECT: LAIAS (Legacy AI Agent Studio)

**Path**: `/Volumes/Storage/LAIAS`
**Cache Prefix**: `laias:`
**Phase**: Planning (no source code implemented)

---

## PROJECT STATE

```
┌─────────────────────┬──────────────────────────────────┐
│ Attribute           │ Value                            │
├─────────────────────┼──────────────────────────────────┤
│ Phase               │ 1 (Foundation & Infrastructure)  │
│ Build Status        │ IN_PROGRESS (75% Phase 1)        │
│ Source Code Exists  │ PARTIAL (infrastructure)         │
│ Tests               │ 0                                │
│ CI Pipeline         │ None                             │
│ Decisions Locked    │ TRUE (2026-02-14)                │
│ Last Session        │ 2026-02-14T04:00:00Z             │
└─────────────────────┴──────────────────────────────────┘
```

---

## OBSERVED ARTIFACTS

```
┌───────────────────────────────┬──────────────────────────────────────────┐
│ File                          │ Purpose                                  │
├───────────────────────────────┼──────────────────────────────────────────┤
│ LAIAS.MD                      │ Goals, requirements, Godzilla ref        │
│ LAIAS_BUILD_GUIDE.md          │ Complete technical spec (~2200 lines)    │
│ LAIAS_MASTER_PLAN.md          │ Architecture overview, build phases      │
│ FLOYD.md                      │ This file (project protocol)             │
│ IMPLEMENTATION_STATUS.md      │ Build progress tracking                  │
│ las.png                       │ Project image                            │
│ docker-compose.yml            │ Container orchestration (CREATED)        │
│ infrastructure/init.sql       │ Database schema (VERIFIED)               │
│ infrastructure/redis.conf     │ Redis configuration (CREATED)            │
│ .env.example                  │ Environment template (CREATED)           │
└───────────────────────────────┴──────────────────────────────────────────┘
```

---

## WHAT LAIAS IS (from observed docs)

**Legacy AI Agent Studio** generates, deploys, and manages CrewAI-based AI agents.

User flow:
1. User describes agent in natural language
2. System generates Python code (Godzilla pattern)
3. Code deployed to Docker container (< 1 second)
4. User monitors via Control Room dashboard

---

## KEY ARCHITECTURAL DECISIONS (from LAIAS_MASTER_PLAN.md)

| Decision | Rationale |
|----------|-----------|
| Godzilla Pattern | All generated agents use `Flow[AgentState]`, typed state, `@start/@listen/@router` decorators |
| No-Build Deployment | Pre-built base image + volume mounting = instant deployments |
| Docker Siblings | Orchestrator spawns sibling containers (not DinD) |

---

## TECHNOLOGY STACK (from LAIAS_MASTER_PLAN.md)

```
┌─────────────────┬─────────────────────────────────────────────────┐
│ Layer           │ Technologies                                    │
├─────────────────┼─────────────────────────────────────────────────┤
│ Backend APIs    │ Python 3.11, FastAPI, CrewAI, Pydantic, SQLAlchemy │
│ Frontend        │ Next.js 15, TypeScript, Tailwind, Monaco Editor │
│ Database        │ PostgreSQL 15                                   │
│ Cache/Queue     │ Redis 7                                         │
│ Orchestration   │ Docker Compose                                  │
│ LLM Providers   │ OpenAI API, Anthropic API                       │
└─────────────────┴─────────────────────────────────────────────────┘
```

---

All items identified by the critical are to be fixed. NO TODOs will be left, issues will be fixed to best practices standards WHEN FOUND. There will be no moving on to a later phase without completion of the current phase.

## BUILD PHASES (from LAIAS_BUILD_GUIDE.md)

```
Phase 1: Foundation & Infrastructure
  ├─ 1.1 Database Schema (init.sql)
  ├─ 1.2 Docker Compose Base
  ├─ 1.3 Agent Runner Base Image
  └─ 1.4 Redis Configuration

Phase 2: Core Services
  ├─ 2.1 Agent Generator API (port 8001)
  └─ 2.2 Docker Orchestrator (port 8002)

Phase 3: User Interfaces
  ├─ 3.1 Studio UI (port 3000)
  └─ 3.2 Control Room Dashboard (port 3001)

Phase 4: Integration & Deployment
  ├─ 4.1 Integration Layer
  └─ 4.2 E2E Testing

Phase 5: Advanced Features
```

---

## SERVICE PORTS (planned, not implemented)

```
┌─────────────────────────┬──────┬───────────────────────────┐
│ Service                 │ Port │ URL                       │
├─────────────────────────┼──────┼───────────────────────────┤
│ Studio UI               │ 3000 │ http://localhost:3000     │
│ Control Room            │ 3001 │ http://localhost:3001     │
│ Agent Generator API     │ 8001 │ http://localhost:8001     │
│ Docker Orchestrator     │ 8002 │ http://localhost:8002     │
│ PostgreSQL              │ 5432 │ localhost:5432            │
│ Redis                   │ 6379 │ localhost:6379            │
└─────────────────────────┴──────┴───────────────────────────┘
```

---

## CACHE KEYS USED

```
laias:status           # Project state
laias:build_progress   # Checkpoint: current phase, completed components
laias:deployment:*     # Active deployments (when implemented)
laias:agent:*          # Generated agents (when implemented)
laias:decisions        # Any deviations from BUILD_GUIDE with rationale
```

---

## GODZILLA PATTERN REFERENCE (from LAIAS.MD)

All generated agents must follow this pattern. Key elements observed in reference code:

```python
@persist
class LegacyAIPrimeFlow(Flow[AgentState]):
    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__()
        self.config = config or AgentConfig()
        self.tools = self._initialize_tools()
    
    @start()
    async def initialize_execution(self, inputs: Dict[str, Any]) -> AgentState:
        # Entry point
        pass
    
    @listen("initialize_execution")
    async def analyze_requirements(self, state: AgentState) -> AgentState:
        # Chained handler
        pass
    
    @router(execute_main_task)
    def determine_next_steps(self) -> str:
        # Conditional routing
        pass
```

---

---

## BUILD DECISIONS (Confirmed 2026-02-14)

### 1. Build Order (CONFIRMED)
Follow strict dependency order. No component starts until dependencies are verified green.

```
┌────────┬─────────────────────────┬─────────────────────┬───────────────────────────┐
│ Priority│ Component               │ Blocks              │ Done Criteria             │
├────────┼─────────────────────────┼─────────────────────┼───────────────────────────┤
│ 1      │ docker-compose.yml      │ Everything          │ docker compose config OK  │
│ 2      │ init.sql verification   │ Agent services      │ Schema matches BUILD_GUIDE│
│ 3      │ Dockerfile.agent-runner │ Agent deployment    │ Image builds, runs hello  │
│ 4      │ redis.conf              │ Queue system        │ Redis accepts connections │
│ 5      │ Agent Generator API     │ Studio, Orchestrator│ /health 200, generates OK │
│ 6      │ Docker Orchestrator     │ Control Room        │ Container CRUD works      │
│ 7      │ Studio UI               │ End users           │ Can describe + see code   │
│ 8      │ Control Room            │ End users           │ Shows agents, logs, status│
│ 9      │ Integration tests       │ Production          │ All E2E flows pass        │
└────────┴─────────────────────────┴─────────────────────┴───────────────────────────┘
```

### 2. API Key Management (CONFIRMED: .env)
Use `.env` file for local development. Never commit secrets.

```
# Required in .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://laias:laias@localhost:5432/laias
REDIS_URL=redis://localhost:6379
```

### 3. Deviation Protocol (CONFIRMED: Stop and Ask)
If BUILD_GUIDE has an issue (missing dependency, wrong port, conflict):
1. **STOP** - do not proceed with assumptions
2. **ASK** user for clarification
3. **LOG** decision to `laias:decisions` cache if approved
4. **DOCUMENT** in IMPLEMENTATION_STATUS.md

---

## DRIFT PREVENTION MECHANISMS

```
┌─────────────────────────┬──────────────────────────────────────────────────────────┐
│ Mechanism               │ Implementation                                           │
├─────────────────────────┼──────────────────────────────────────────────────────────┤
│ 1. SUPERCACHE State     │ laias:build_progress checkpoint after EACH component     │
│                         │ completion. Includes: timestamp, test result, files made │
├─────────────────────────┼──────────────────────────────────────────────────────────┤
│ 2. Status Document      │ IMPLEMENTATION_STATUS.md in project root                │
│                         │ Machine-readable, human-verifiable, updated per session │
├─────────────────────────┼──────────────────────────────────────────────────────────┤
│ 3. Phase Gates          │ Explicit "done criteria" before advancing phases        │
│                         │ All tests must pass, services must respond              │
├─────────────────────────┼──────────────────────────────────────────────────────────┤
│ 4. Dependency Graph     │ Strict ordering enforced - no parallel phase starts     │
│                         │ Each component waits for upstream dependencies          │
├─────────────────────────┼──────────────────────────────────────────────────────────┤
│ 5. Single Source Truth  │ LAIAS_BUILD_GUIDE.md is the specification               │
│                         │ Any deviation requires explicit user approval           │
└─────────────────────────┴──────────────────────────────────────────────────────────┘
```

### Checkpoint Schema (SUPERCACHE: laias:build_progress)

```python
{
    "current_phase": 1,
    "current_component": "1.2_docker_compose",
    "completed": ["1.1_database_schema"],
    "verified": {
        "1.1_database_schema": {
            "timestamp": "2026-02-14T02:00:00Z",
            "test": "schema_valid",
            "files": ["infrastructure/init.sql"]
        }
    },
    "decisions": [],  # Any approved deviations from BUILD_GUIDE
    "blocking": None
}
```

### Phase Gate Criteria

```
Phase 1 Gate: docker compose up -d → all services healthy
Phase 2 Gate: curl localhost:8001/health && curl localhost:8002/health → 200 OK
Phase 3 Gate: npm run build succeeds for both UIs
Phase 4 Gate: E2E test suite passes (agent create → deploy → monitor → stop)
```

---

## IMPLEMENTATION START

When ready to begin implementation, follow `LAIAS_BUILD_GUIDE.md` Phase 1.

Current checkpoint: `laias:build_progress` = PHASE_1_IN_PROGRESS

```
┌─────────────────────────────────────────────────────────────────────┐
│ BUILD PROGRESS (2026-02-14)                                         │
├─────────────────────────────────────────────────────────────────────┤
│ Completed: P1.1 Database Schema, P1.2 Docker Compose, P1.4 Redis    │
│ Next: P1.3 Agent Runner Dockerfile                                  │
│ Status: HALTED per user request                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

*This document reflects the BUILD phase. Last updated 2026-02-14.*
