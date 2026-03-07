# LAIAS System Capabilities Reference

**Legacy AI Agent Studio — Complete Technical Capability Map**
**Last verified: March 7, 2026 | Branch: `feat/agent-output-persistence-routing`**

---

## What LAIAS Is

LAIAS is a Dockerized platform that lets a user describe an AI agent idea in natural language, generates production-ready Python code for that agent, deploys it inside an isolated Docker container, and provides real-time monitoring of the running agent — all through two web interfaces backed by two API services and a shared PostgreSQL/Redis infrastructure.

The platform produces agents built on the CrewAI framework, following a proprietary architectural pattern called "Godzilla" — a structured `Flow[AgentState]` pattern with typed state, YAML-defined agent roles, structured logging, output routing, and conditional branching.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER ENTRY POINTS                            │
├──────────────────────────────┬──────────────────────────────────────────┤
│    Studio UI (Port 4527)     │       Control Room (Port 4528)          │
│    Next.js 15 — Build agents │       Next.js 15 — Monitor agents      │
└──────────┬───────────────────┴────────────────────┬────────────────────┘
           │                                        │
           ▼                                        ▼
┌──────────────────────────────┐  ┌──────────────────────────────────────┐
│  Agent Generator (Port 4521) │  │  Docker Orchestrator (Port 4522)     │
│  FastAPI — Code generation   │──│  FastAPI — Container lifecycle       │
│  Auth, Templates, Validation │  │  Logs, Metrics, Analytics, Outputs   │
└──────────┬───────────────────┘  └────────────────────┬─────────────────┘
           │                                           │
           ▼                                           ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          INFRASTRUCTURE                                  │
│   PostgreSQL (5432) — Agent/deployment/user/team persistence            │
│   Redis (6379) — Caching, session data, rate limiting                    │
│   Docker Engine — Sibling containers via mounted docker.sock             │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Entry Point 1: Studio UI (Port 4527)

The Studio UI is the primary user-facing application. It is a Next.js 15 app with Zustand state management, Tailwind CSS styling, and a cyber-ops visual design language (dark backgrounds, cyan/purple neon accents).

### Pages and What a User Can Do

#### Home Page (`/`)
A landing page with three feature callouts: Describe Your Agent, Review & Edit Code, Deploy Instantly. Links to the Create page and Templates browser.

#### Create Agent Page (`/create`)
**This is the core workflow of the entire platform.** A user fills out a form:

1. **Description** (required, 10–5000 chars) — Natural language description of what the agent should do. Example: "Create a market research swarm that analyzes competitors and generates reports."
2. **Complexity** — `simple`, `moderate`, or `complex`. Controls how many sub-agents and flow branches the LLM generates.
3. **Task Type** — `research`, `development`, `automation`, `analysis`, or `general`. Optimizes the system prompt for the selected domain.
4. **Max Agents** — 1 to 10. Hard cap on the number of sub-agents in the generated crew.
5. **Tools** — Multi-select from available CrewAI tools (SerperDevTool, ScrapeWebsiteTool, FileReadTool, etc.). Only tools with configured API keys are shown as available.
6. **LLM Provider** — `zai` (default), `openai`, `anthropic`, or `openrouter`. Controls which LLM generates the code.
7. **Model** — Optional override for the specific model within the chosen provider.

**Advanced options** include memory enablement, analytics inclusion, and output configuration (where agent results are persisted: Postgres, files, or both).

**Template pre-fill**: If the user navigates from the Templates page with a `?template=<id>` query parameter, the form is pre-filled with that template's defaults.

**On submit**, the form calls `POST /api/generate-agent` on the Agent Generator service. The response populates a tabbed code panel showing:
- **Flow Code** — The generated Python `Flow[AgentState]` class
- **Agents YAML** — CrewAI agent role definitions
- **State Class** — Pydantic `BaseModel` for typed agent state
- **Requirements** — pip dependencies
- **Flow Diagram** — Mermaid-format flow visualization
- **Validation Status** — Pattern compliance score and any missing patterns

The user can review the code in a syntax-highlighted panel, then click **Deploy** to send it to the Docker Orchestrator for containerized execution.

#### Templates Page (`/templates`)
Displays the 100 YAML-defined preset templates. Each template includes:
- Name, description, category, tags
- Default complexity and tools
- Sample prompts (natural language starters)
- Suggested LLM configuration

Templates are filterable by category and searchable by name/description. Clicking a template navigates to `/create?template=<id>` with the form pre-filled.

**Template categories** span: content, sales, engineering, analytics, research, operations, design, QA, security, and more.

#### Agents Page (`/agents`)
Lists all previously generated agents stored in the database. Supports:
- Pagination (limit/offset)
- Filtering by task type and complexity
- Full-text search across name and description
- Team filtering (agents shared with a specific team)

Each agent card shows its name, description, creation date, complexity, provider, and validation score. Clicking an agent shows its full code and metadata.

#### Settings Page (`/settings`)
User profile management and account settings.

#### Team Settings Page (`/settings/team`)
Team management interface:
- Create teams with name and slug
- View team members with roles (owner, admin, member, viewer)
- Add members by user ID
- Remove members (owner cannot remove self)
- Update member roles

#### Business Development Agent Page (`/agents/business-development-indiana-smb`)
A dedicated page for the Indiana SMB business development agent — a pre-built agent targeting local small businesses in Indiana for outreach campaigns.

---

## Entry Point 2: Control Room (Port 4528)

The Control Room is the operations dashboard for monitoring deployed agent containers.

### Pages and What a User Can Do

#### Dashboard (`/`)
Overview page with:
- **KPI Cards** — Total containers, running count, stopped count, error count
- **System Status** — Live health of Database, Redis, and Docker Engine with latency indicators
- **Recent Deployments** — Last 5 deployed agents with status
- **System Metrics** — Total deployments, running containers, total containers

Health data auto-refreshes every 30 seconds.

#### Containers List (`/containers`)
Grid of all deployed agent containers with:
- Container ID, agent name, deployment ID
- Status badge (running, stopped, exited, error)
- CPU and memory usage (for running containers)
- Uptime duration
- Action buttons: Start, Stop, Restart, Remove

Filterable by status. Supports pagination.

#### Container Detail (`/containers/[id]`)
Deep view of a single container:
- Full container metadata (image, labels, network)
- Real-time resource metrics (CPU %, memory MB, uptime)
- Output artifacts panel — shows persisted run results with summary markdown, metrics, and event logs
- Links to logs and metrics sub-pages

#### Container Logs (`/containers/[id]/logs`)
Log viewer with:
- Paginated log retrieval (tail N lines with offset)
- Log level filtering (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Timestamp-based filtering (since parameter)
- **WebSocket streaming** — Real-time log tailing via `ws://` connection with ping/pong keepalive

#### Metrics Page (`/metrics`)
System-wide analytics dashboard with:
- Usage statistics: API call counts, token usage, cost estimates by provider
- Deployment statistics: total/successful/failed deployments, success rate percentage
- Performance metrics: average response time, p50/p95/p99 latencies
- Daily timeseries charts for all metrics over configurable time periods (7/30 days)

---

## Entry Point 3: Agent Generator API (Port 4521)

The Agent Generator is a FastAPI service responsible for LLM-powered code generation, agent persistence, authentication, and template management. All responses are JSON.

### API Endpoints

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `POST /api/generate-agent` | POST | Yes | Generate CrewAI agent code from natural language description |
| `POST /api/generate-and-deploy` | POST | Yes | Generate agent and immediately deploy to container (single call) |
| `POST /api/deploy` | POST | No | Proxy deploy to Docker Orchestrator |
| `POST /api/regenerate` | POST | No | Regenerate agent with user feedback |
| `POST /api/validate-code` | POST | No | Validate Python code against Godzilla pattern |
| `GET /api/validation-rules` | GET | No | Get pattern validation rules |
| `GET /api/agents` | GET | Yes | List saved agents with filtering and pagination |
| `GET /api/agents/{id}` | GET | No | Get agent detail by ID |
| `PUT /api/agents/{id}` | PUT | No | Update agent description, tags, status |
| `DELETE /api/agents/{id}` | DELETE | No | Delete an agent |
| `POST /api/agents/{id}/share` | POST | Yes | Share agent with a team |
| `DELETE /api/agents/{id}/share` | DELETE | Yes | Unshare agent from team |
| `GET /api/templates` | GET | No | List all 100 preset templates |
| `GET /api/templates/categories` | GET | No | List template categories |
| `GET /api/templates/{id}` | GET | No | Get specific template |
| `POST /api/templates/{id}/apply` | POST | No | Apply template to create generation request |
| `GET /tools/` | GET | No | List all available tools with status |
| `GET /tools/categories` | GET | No | List tool categories |
| `GET /tools/available` | GET | No | List only currently available tools |
| `GET /tools/{name}` | GET | No | Get tool detail |
| `POST /tools/instantiate` | POST | No | Instantiate a tool with config |
| `GET /tools/mcp/servers` | GET | No | List MCP servers |
| `GET /tools/mcp/presets` | GET | No | List MCP server presets |
| `POST /tools/mcp/connect` | POST | No | Connect to MCP server |
| `POST /tools/mcp/connect-all` | POST | No | Connect to all available MCP servers |
| `POST /auth/register` | POST | No | Register new user, returns JWT tokens |
| `POST /auth/login` | POST | No | Login, returns JWT tokens |
| `POST /auth/refresh` | POST | No | Refresh JWT access token |
| `GET /auth/me` | GET | Yes | Get current user info |
| `GET /api/users/me` | GET | Yes | Get current user profile |
| `PUT /api/users/me` | PUT | Yes | Update current user profile |
| `GET /api/teams` | GET | Yes | List user's teams |
| `POST /api/teams` | POST | Yes | Create team (user becomes owner) |
| `GET /api/teams/{id}` | GET | Yes | Get team with member list |
| `PUT /api/teams/{id}` | PUT | Yes | Update team name (owner/admin) |
| `DELETE /api/teams/{id}` | DELETE | Yes | Delete team (owner only) |
| `POST /api/teams/{id}/members` | POST | Yes | Add member (owner/admin) |
| `DELETE /api/teams/{id}/members/{uid}` | DELETE | Yes | Remove member |
| `PUT /api/teams/{id}/members/{uid}` | PUT | Yes | Update member role |
| `POST /api/teams/{id}/transfer-ownership/{uid}` | POST | Yes | Transfer ownership |
| `GET /health` | GET | No | Full health check (LLM, DB, Redis) |
| `GET /readiness` | GET | No | Kubernetes readiness probe |
| `GET /liveness` | GET | No | Kubernetes liveness probe |

### Authentication System
- **JWT-based** — Access tokens (1 hour) and refresh tokens
- **bcrypt** password hashing (direct, not passlib)
- **Dev mode bypass** — When `AUTH_MODE=dev`, requests without tokens get a fallback dev user. Custom user via `X-User-Id` header
- **RBAC** on teams — Owner, Admin, Member, Viewer roles with enforced permission checks

### LLM Provider System
The generator supports 7 LLM providers with automatic fallback:

| Provider | Default Model | API Key Env Var |
|----------|---------------|-----------------|
| ZAI | GLM-5 | `ZAI_API_KEY` |
| Portkey | @zhipu/glm-4.7-flashx | `PORTKEY_API_KEY` |
| OpenAI | gpt-4o | `OPENAI_API_KEY` |
| Anthropic | claude-sonnet-4-20250514 | `ANTHROPIC_API_KEY` |
| OpenRouter | anthropic/claude-sonnet-4 | `OPENROUTER_API_KEY` |
| Google | gemini-2.0-flash-exp | `GOOGLE_API_KEY` |
| Mistral | mistral-large-latest | `MISTRAL_API_KEY` |

**Fallback chain**: If the primary provider fails, the service automatically tries the next available provider in priority order (ZAI → OpenAI → Anthropic → OpenRouter → Google → Mistral). Only providers with configured API keys are included in the chain.

**Retry logic**: 3 attempts per provider with exponential backoff (2–10 second wait).

### Code Validation
The validator checks generated code against the Godzilla pattern:
- Python syntax validation
- Pattern compliance scoring (0–1.0 scale)
- Required patterns: `Flow[AgentState]`, `@start()`, `@listen()`, `@router()`, structured logging, typed state
- Missing pattern identification
- Improvement suggestions

---

## Entry Point 4: Docker Orchestrator API (Port 4522)

The Docker Orchestrator is a FastAPI service that manages the lifecycle of agent containers. It communicates with the Docker Engine via the mounted `/var/run/docker.sock`.

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /api/deploy` | POST | Deploy agent code to new container |
| `DELETE /api/deploy/{id}` | DELETE | Remove deployment and container |
| `GET /api/containers` | GET | List all containers with metrics |
| `GET /api/containers/{id}` | GET | Get container detail with metrics |
| `POST /api/containers/{id}/start` | POST | Start stopped container |
| `POST /api/containers/{id}/stop` | POST | Stop running container |
| `POST /api/containers/{id}/restart` | POST | Restart container |
| `DELETE /api/containers/{id}` | DELETE | Remove container |
| `GET /api/containers/{id}/metrics` | GET | Get CPU/memory/uptime metrics |
| `GET /api/containers/{id}/logs` | GET | Get paginated logs with filtering |
| `WS /api/containers/{id}/logs/stream` | WebSocket | Real-time log streaming |
| `POST /api/deployments/{id}/outputs/events` | POST | Ingest structured output event |
| `GET /api/deployments/{id}/outputs/runs` | GET | List persisted output runs |
| `GET /api/deployments/{id}/outputs/runs/{rid}` | GET | Get run artifacts (summary, metrics, events) |
| `POST /api/convert` | POST | Convert content between Markdown and HTML |
| `GET /api/filesystem/browse` | GET | Browse server filesystem (path-traversal protected) |
| `POST /api/filesystem/mkdir` | POST | Create directory on server |
| `GET /api/analytics` | GET | Get all analytics (usage + deployments + performance) |
| `GET /api/analytics/usage` | GET | API call counts, token usage, cost estimates |
| `GET /api/analytics/deployments` | GET | Deployment counts, success rates |
| `GET /api/analytics/performance` | GET | Response time percentiles |
| `POST /api/analytics/events` | POST | Record analytics event (internal) |
| `POST /api/analytics/seed` | POST | Seed sample analytics data (dev) |
| `GET /health` | GET | Health check (Docker, DB, Redis) |
| `GET /health/live` | GET | Kubernetes liveness probe |
| `GET /health/ready` | GET | Kubernetes readiness probe |

### Deployment Strategy
The orchestrator uses a **No-Build deployment model**:
1. A pre-built `laias/agent-runner:latest` Docker image contains all CrewAI dependencies
2. Generated agent code is written to the host filesystem
3. A new container is created from the base image with the code mounted as a read-only volume at `/app/agent`
4. The container starts execution immediately (if `auto_start=true`)

This means deployments take seconds, not minutes — no Docker build step is required.

### Container Resource Limits
Each deployment accepts configurable limits:
- **CPU**: Decimal value (default: 1.0 core)
- **Memory**: String with unit (default: `512m`)
- Platform enforces a maximum container count (`MAX_CONTAINERS` setting)

### Output Persistence System
Agents can emit structured output events during execution. These are persisted to:
- **PostgreSQL** — `crew_runs`, `task_results`, `llm_calls`, `tool_usage` tables
- **Filesystem** — Markdown summaries and JSON artifacts at configurable paths

Each run produces:
- Summary markdown (human-readable report)
- Metrics dictionary (token counts, latencies, costs)
- Event log (ordered list of agent actions)

### Analytics Engine
The orchestrator tracks three metric categories:
- **Usage**: API call counts by endpoint, token consumption by provider, cost estimates using per-model pricing tables
- **Deployments**: Total/successful/failed counts, success rate percentage, status distribution
- **Performance**: Average response time, p50/p95/p99 latencies, daily request counts

All metrics support configurable lookback periods and daily timeseries aggregation.

---

## Data Layer

### PostgreSQL Schema (11 Tables)

| Table | Purpose |
|-------|---------|
| `agents` | Generated agent definitions, code, config, validation status |
| `deployments` | Container deployments linked to agents, resource limits, lifecycle timestamps |
| `execution_logs` | Structured logs from agent runs (level, message, source, metadata) |
| `execution_metrics` | Per-execution resource usage and cost tracking |
| `crew_runs` | Top-level run records for structured execution tracking |
| `task_results` | Per-task results from CrewAI events (output, agent role, status) |
| `llm_calls` | LLM-level observability (model, tokens, latency, cost) |
| `tool_usage` | Tool invocation tracking (args, output, cache hits, timing) |
| `users` | User accounts with email, name, password hash |
| `teams` | Team definitions with name, slug, owner |
| `team_members` | Membership junction table with RBAC roles |

All tables use `TIMESTAMP WITH TIME ZONE`, UUID primary keys for identity tables, and have proper foreign key cascades and check constraints.

### Redis
Used for:
- Rate limiting (via `slowapi`)
- Session caching
- Health check ping verification

---

## Platform Strengths

### 1. End-to-End Automation
The platform covers the complete lifecycle from natural language idea to running containerized agent. No manual Python coding, Dockerfile authoring, or container orchestration is required from the user.

### 2. Architectural Consistency
Every generated agent follows the same Godzilla pattern. This means agents are structurally predictable: typed state, YAML-defined roles, structured logging, and conditional routing. The code validator enforces this consistency with a quantified compliance score.

### 3. Multi-Provider LLM Resilience
The automatic fallback chain across 7 providers means generation rarely fails due to a single provider outage. The system silently retries with the next available provider.

### 4. No-Build Deployment Speed
Using a pre-built base image with volume-mounted code means deployments complete in seconds. No Docker build step, no layer caching concerns, no image registry.

### 5. Full Observability Stack
From LLM token costs to container CPU usage to per-task agent outputs, the platform tracks everything. The analytics engine provides cost estimates using real per-model pricing tables.

### 6. Team Collaboration
RBAC team system with ownership transfer, role-based permissions, and agent sharing allows multiple users to work on a shared agent library.

### 7. 100 Production-Ready Templates
The YAML template library covers content creation, sales, engineering, analytics, research, operations, design, QA, and security — giving users concrete starting points rather than blank-page syndrome.

### 8. Enterprise-Grade Code Quality
- Zero deprecation warnings across both Python services
- Full Pydantic v2 migration (no v1 `@validator` or `class Config` patterns)
- 56 passing tests (37 agent-generator + 19 orchestrator) with strict deprecation error promotion
- All tests run without live Docker daemon or Postgres (fully mocked)
- Ruff lint clean, ESLint clean, TypeScript strict mode clean, both frontends build successfully

---

## Platform Shortcomings

### 1. No Production Authentication on Orchestrator
The Docker Orchestrator has no authentication or authorization layer. Any client with network access can deploy, start, stop, or remove containers. The Agent Generator has JWT auth, but the Orchestrator is fully open.

### 2. In-Memory Analytics Store
The analytics engine (`analytics_store`) uses an in-memory store, not Postgres. Analytics data is lost on service restart. The database schema defines observability tables (`crew_runs`, `task_results`, `llm_calls`, `tool_usage`), but the analytics endpoints read from the in-memory store, not these tables.

### 3. No CI/CD for Frontends
The GitHub Actions CI pipeline runs Python tests and ruff lint, but does not build or test the Next.js frontends. TypeScript errors and build failures in the frontends would not be caught until manual verification.

### 4. Agent Execution is Fire-and-Forget
Once an agent container starts, the platform can stream its logs and monitor its resource usage, but it cannot:
- Pause or resume execution mid-run
- Inject input or parameters after startup
- Cancel a specific task within a running crew
- Retry a failed task without restarting the entire container

### 5. No Agent Versioning
When an agent is updated (`PUT /api/agents/{id}`), the previous version is overwritten. There is no version history, diff view, or rollback capability.

### 6. Single-Node Docker Only
The orchestrator manages containers on a single Docker host via the local socket. There is no Kubernetes, Docker Swarm, or multi-node support. Horizontal scaling of agent execution is not possible.

### 7. Template Directory Mismatch in Development
The template service looks for YAML files at `/app/templates/presets` (the Docker container path). In local development, this path does not exist — templates are at `<repo>/templates/presets/`. The `TEMPLATES_DIR` environment variable must be set manually for local development.

### 8. Limited Error Recovery
If a deployment fails partway through (code written to disk but container creation fails), the cleanup runs as a background task. If the background task also fails, orphaned agent code remains on disk with no automated garbage collection.

### 9. No WebSocket Authentication
The WebSocket log streaming endpoint (`/api/containers/{id}/logs/stream`) accepts connections without any authentication. Combined with the lack of Orchestrator auth (shortcoming #1), anyone with network access can stream logs from any container.

### 10. Hardcoded LLM Pricing
Cost estimates use hardcoded per-model pricing in `analytics.py`. When providers change their pricing (which happens frequently), the estimates become inaccurate until the code is manually updated.

### 11. Two `datetime.utcnow()` Calls Remain in `generate.py`
The `generate-and-deploy` endpoint at lines 173 and 209 still uses `datetime.utcnow()` instead of `datetime.now(UTC)`. These are in the DB persistence path for the combined generate-and-deploy flow and were not caught in the migration because they import `datetime` locally inside the function body.

### 12. Dev User Seeded in Production Schema
The `init.sql` seeds a dev user (`00000000-0000-0000-0000-000000000000`, `dev@laias.local`) with `ON CONFLICT DO NOTHING`. This row exists in every database instance including production, which is a minor security surface.

### 13. Business Development Endpoints Return 501
The `/api/business-dev-campaign` endpoints are placeholder stubs that return `501 Not Implemented`. They exist in the route table but serve no function.
