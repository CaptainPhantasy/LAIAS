# LAIAS — Single Source of Truth

> Every claim cites `file:line`. Verified against source code 2026-03-06.

---

## 1. Project Identity

| Field | Value | Source |
|-------|-------|--------|
| Name | LAIAS (Legacy AI Agent Studio) | `README.md:1` |
| Purpose | Dockerized platform for generating, deploying, and monitoring CrewAI agents via natural language | `README.md:3` |
| License | MIT | `README.md:bottom` |
| Repository Root | `/Volumes/Storage/LAIAS` | filesystem |

---

## 2. Repository Layout

```
services/agent-generator/        # FastAPI — LLM code generation (port 8001)
services/docker-orchestrator/     # FastAPI — container lifecycle (port 8002)
frontend/studio-ui/               # Next.js 15 — chat-to-agent builder (port 3000)
frontend/control-room/            # Next.js 15 — monitoring dashboard (port 3001)
frontend/shared/                  # Shared TS types and API client
infrastructure/                   # init.sql, redis.conf
templates/presets/                 # 126 agent config YAMLs
agents/                           # 16 standalone agent scripts/dirs (excl. __pycache__, .DS_Store)
.github/workflows/ci.yml          # CI pipeline
docs/                             # OpenAPI specs, design docs, master plan
```

Sources: filesystem directory listings.

---

## 3. Docker Compose Services

File: `docker-compose.yml` (214 lines)

### 3.1 Infrastructure

| Service | Image | Container Name | Host Port | Internal Port | Source |
|---------|-------|----------------|-----------|---------------|--------|
| postgres | `postgres:15-alpine` | `laias-postgres` | 5432 | 5432 | line 7-8, 17 |
| redis | `redis:7-alpine` | `laias-redis` | 6379 | 6379 | line 27-28, 34 |

**PostgreSQL config** (lines 9-12):
- User: `laias`, Password: `laias_secure_password` (hardcoded), Database: `laias`
- Volume: `postgres_data` → `/var/lib/postgresql/data`
- Init script: `./infrastructure/init.sql` mounted read-only to `/docker-entrypoint-initdb.d/`
- Healthcheck: `pg_isready -U laias`, interval 10s, timeout 5s, retries 5

**Redis config** (lines 27-39):
- Command: `redis-server /etc/redis/redis.conf`
- Volume: `redis_data` → `/data`
- Config: `./infrastructure/redis.conf` mounted read-only
- Healthcheck: `redis-cli ping`, interval 10s, timeout 5s, retries 5

### 3.2 Agent Runner (Build-Only)

| Field | Value | Source |
|-------|-------|--------|
| Build context | `.` (repo root) | line 50 |
| Dockerfile | `Dockerfile.agent-runner` | line 51 |
| Image tag | `laias/agent-runner:latest` | line 52 |
| Profile | `build-only` | line 53-54 |

This image is never started by `docker-compose up`. It exists as a base image for spawned agent containers.

### 3.3 Backend Services

**Agent Generator** (lines 62-105):
| Field | Value |
|-------|-------|
| Build context | `./services/agent-generator` |
| Image | `laias/agent-generator:latest` |
| Container name | `laias-agent-generator` |
| Port mapping | `4521:8001` |
| Depends on | postgres (healthy), redis (healthy) |
| Healthcheck | `curl -f http://localhost:8001/health`, interval 30s |

Key environment variables (lines 70-91):
- `DATABASE_URL=postgresql+asyncpg://laias:laias_secure_password@postgres:5432/laias`
- `REDIS_URL=redis://redis:6379/0`
- `ALLOWED_ORIGINS` — includes localhost:4527, localhost:4528, ngrok URLs
- LLM keys: `ZAI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY` (from host `.env`)
- `LLM_PROVIDER=${DEFAULT_LLM_PROVIDER:-zai}`, `DEFAULT_MODEL=${DEFAULT_MODEL:-glm-5}`
- `DOCKER_ORCHESTRATOR_URL=http://docker-orchestrator:8002` (service-to-service)
- `TEMPLATES_DIR=/app/templates/presets`

Volumes: `./templates/presets:/app/templates/presets:ro`

**Docker Orchestrator** (lines 107-141):
| Field | Value |
|-------|-------|
| Build context | `./services/docker-orchestrator` |
| Image | `laias/docker-orchestrator:latest` |
| Container name | `laias-docker-orchestrator` |
| Port mapping | `4522:8002` |
| Depends on | postgres (healthy), redis (healthy) |
| Healthcheck | `curl -f http://localhost:8002/health`, interval 30s |

Key environment variables (lines 115-124):
- `DATABASE_URL=postgresql+asyncpg://laias:laias_secure_password@postgres:5432/laias`
- `REDIS_URL=redis://redis:6379/1` (DB 1, different from agent-generator's DB 0)
- `DOCKER_HOST=unix:///var/run/docker.sock`
- `AGENT_IMAGE_BASE=laias/agent-runner:latest`
- `AGENT_CODE_PATH=/var/laias/agents`

Volumes (lines 125-129):
- `/var/run/docker.sock:/var/run/docker.sock` (host Docker socket for sibling containers)
- `agent_code:/var/laias/agents` (generated agent code)

### 3.4 Frontend Services

**Studio UI** (lines 147-175):
| Field | Value |
|-------|-------|
| Build context | `./frontend` |
| Dockerfile | `studio-ui/Dockerfile` |
| Image | `laias/studio-ui:latest` |
| Container name | `laias-studio-ui` |
| Port mapping | `4527:3000` |
| Depends on | agent-generator (healthy), docker-orchestrator (healthy) |

Build args + env: `NEXT_PUBLIC_AGENT_GENERATOR_URL=http://localhost:4521`, `NEXT_PUBLIC_DOCKER_ORCHESTRATOR_URL=http://localhost:4522`

**Control Room** (lines 177-201):
| Field | Value |
|-------|-------|
| Build context | `./frontend` |
| Dockerfile | `control-room/Dockerfile` |
| Image | `laias/control-room:latest` |
| Container name | `laias-control-room` |
| Port mapping | `4528:3001` |
| Depends on | docker-orchestrator (healthy) |

Build args + env: `NEXT_PUBLIC_DOCKER_ORCHESTRATOR_URL=http://localhost:4522`

### 3.5 Network & Volumes

**Network** (lines 203-206): `laias-network`, driver: `bridge`

**Named Volumes** (lines 208-214):
| Volume | External Name |
|--------|---------------|
| `postgres_data` | `laias-postgres-data` |
| `redis_data` | `laias-redis-data` |
| `agent_code` | `laias-agent-code` |

---

## 4. Database Schema

File: `infrastructure/init.sql` (224 lines)

### 4.1 Extensions

- `uuid-ossp` — line 7

### 4.2 Tables

**agents** (lines 13-42):
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `VARCHAR(50)` | PK, DEFAULT `'gen_' \|\| substr(md5(random()::text), 1, 12)` |
| `name` | `VARCHAR(100)` | NOT NULL |
| `description` | `TEXT` | |
| `flow_code` | `TEXT` | NOT NULL |
| `agents_yaml` | `TEXT` | |
| `state_class` | `TEXT` | |
| `complexity` | `VARCHAR(20)` | CHECK IN ('simple','moderate','complex') |
| `task_type` | `VARCHAR(50)` | CHECK IN ('research','development','analysis','automation','general') |
| `tools` | `JSONB` | DEFAULT '[]' |
| `requirements` | `JSONB` | DEFAULT '[]' |
| `llm_provider` | `VARCHAR(20)` | DEFAULT 'openai' |
| `model` | `VARCHAR(50)` | DEFAULT 'gpt-4o' |
| `estimated_cost_per_run` | `DECIMAL(10,4)` | |
| `complexity_score` | `INTEGER` | CHECK 1-10 |
| `validation_status` | `JSONB` | DEFAULT '{}' |
| `flow_diagram` | `TEXT` | |
| `created_at` | `TIMESTAMPTZ` | DEFAULT NOW() |
| `updated_at` | `TIMESTAMPTZ` | DEFAULT NOW() |
| `owner_id` | `UUID` | FK → users(id), added via ALTER TABLE (line 192) |
| `team_id` | `UUID` | FK → teams(id), added via ALTER TABLE (line 199) |

**deployments** (lines 48-75):
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `VARCHAR(50)` | PK, DEFAULT `'deploy_' \|\| substr(md5(...), 1, 12)` |
| `agent_id` | `VARCHAR(50)` | FK → agents(id) ON DELETE CASCADE |
| `container_id` | `VARCHAR(100)` | |
| `container_name` | `VARCHAR(100)` | |
| `status` | `VARCHAR(20)` | NOT NULL, DEFAULT 'pending', CHECK IN (pending, creating, starting, running, stopped, error, terminated) |
| `cpu_limit` | `DECIMAL(4,2)` | DEFAULT 1.0 |
| `memory_limit` | `VARCHAR(20)` | DEFAULT '512m' |
| `environment_vars` | `JSONB` | DEFAULT '{}' |
| `created_at` | `TIMESTAMPTZ` | DEFAULT NOW() |
| `started_at` | `TIMESTAMPTZ` | |
| `stopped_at` | `TIMESTAMPTZ` | |
| `last_error` | `TEXT` | |
| `error_count` | `INTEGER` | DEFAULT 0 |
| `team_id` | `UUID` | FK → teams(id), added via ALTER TABLE (line 210) |

**execution_logs** (lines 81-95):
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `BIGSERIAL` | PK |
| `deployment_id` | `VARCHAR(50)` | FK → deployments(id) ON DELETE CASCADE |
| `level` | `VARCHAR(20)` | NOT NULL, CHECK IN (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `message` | `TEXT` | NOT NULL |
| `source` | `VARCHAR(100)` | |
| `metadata` | `JSONB` | DEFAULT '{}' |
| `timestamp` | `TIMESTAMPTZ` | DEFAULT NOW() |

**execution_metrics** (lines 101-119):
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `BIGSERIAL` | PK |
| `deployment_id` | `VARCHAR(50)` | FK → deployments(id) ON DELETE CASCADE |
| `cpu_percent` | `DECIMAL(5,2)` | |
| `memory_usage_mb` | `DECIMAL(10,2)` | |
| `tokens_used` | `INTEGER` | DEFAULT 0 |
| `api_calls` | `INTEGER` | DEFAULT 0 |
| `estimated_cost` | `DECIMAL(10,4)` | DEFAULT 0 |
| `execution_duration_seconds` | `INTEGER` | |
| `recorded_at` | `TIMESTAMPTZ` | DEFAULT NOW() |

**users** (lines 157-164):
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | PK, DEFAULT gen_random_uuid() |
| `email` | `VARCHAR(255)` | UNIQUE NOT NULL |
| `name` | `VARCHAR(255)` | |
| `password_hash` | `VARCHAR(255)` | |
| `created_at` | `TIMESTAMPTZ` | DEFAULT NOW() |
| `last_login` | `TIMESTAMPTZ` | |

**teams** (lines 167-173):
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | PK, DEFAULT gen_random_uuid() |
| `name` | `VARCHAR(255)` | NOT NULL |
| `slug` | `VARCHAR(100)` | UNIQUE NOT NULL |
| `owner_id` | `UUID` | FK → users(id) ON DELETE SET NULL |
| `created_at` | `TIMESTAMPTZ` | DEFAULT NOW() |

**team_members** (lines 176-183):
| Column | Type | Constraints |
|--------|------|-------------|
| `team_id` | `UUID` | FK → teams(id) ON DELETE CASCADE, part of composite PK |
| `user_id` | `UUID` | FK → users(id) ON DELETE CASCADE, part of composite PK |
| `role` | `VARCHAR(50)` | DEFAULT 'member', CHECK IN (owner, admin, member, viewer) |
| `joined_at` | `TIMESTAMPTZ` | DEFAULT NOW() |

### 4.3 Indexes (lines 124-224)

17 indexes total:
- `idx_agents_created_at` (DESC), `idx_agents_task_type`, `idx_agents_owner`, `idx_agents_team`
- `idx_deployments_agent_id`, `idx_deployments_status`, `idx_deployments_created_at` (DESC), `idx_deployments_team`
- `idx_execution_logs_deployment_id`, `idx_execution_logs_timestamp` (DESC), `idx_execution_logs_level`
- `idx_execution_metrics_deployment_id`
- `idx_users_email`, `idx_teams_slug`, `idx_teams_owner`, `idx_team_members_team`, `idx_team_members_user`

### 4.4 Triggers

- `update_agents_updated_at` — auto-updates `agents.updated_at` on UPDATE (lines 139-150)

### 4.5 Migration System

**None.** No Alembic config, no migration directory. A comment at `database/session.py:71` says "Use Alembic for production migrations instead." The docker-orchestrator's `requirements.txt:35` includes `alembic>=1.13.0` but it is not initialized.

---

## 5. Agent Generator Service

### 5.1 Identity

| Field | Value | Source |
|-------|-------|--------|
| Package name | `laias-agent-generator` | `pyproject.toml:2` |
| Version (package) | `0.1.0` | `pyproject.toml:3` |
| Version (app) | `1.0.0` | `app/__init__.py:12` |
| Python required | `>=3.13,<3.14` | `pyproject.toml:5` |
| Dockerfile base | `python:3.11-slim` | `Dockerfile:13` |
| Internal port | 8001 | `Dockerfile:40`, `config.py:36` |

### 5.2 Application Structure

```
app/
├── __init__.py          # __version__ = "1.0.0"
├── main.py              # App factory (create_app), lifespan, CORS, routers
├── config.py            # Settings (Pydantic BaseSettings), 157 config fields
├── database/            # SQLAlchemy async session, init/close
├── api/
│   ├── auth.py          # Dev-mode auth (X-User-Id header), TeamRoleChecker
│   └── routes/          # 9 route files (see §5.4)
├── models/
│   ├── database.py      # SQLAlchemy ORM models
│   ├── requests.py      # Pydantic request schemas
│   ├── responses.py     # Pydantic response schemas
│   └── team.py          # Team/User/TeamMember ORM models
├── services/
│   ├── code_generator.py    # Code generation logic
│   ├── llm_provider.py      # Multi-provider LLM client
│   ├── llm_service.py       # LLM orchestration
│   ├── orchestrator_client.py # HTTP client to docker-orchestrator
│   ├── template_service.py  # Template loading/matching
│   └── validator.py         # Code validation
├── tools/               # 11 tool definition files (see §5.5)
├── prompts/             # System prompts for LLM
└── utils/
    └── exceptions.py    # 8 exception classes
```

Source: directory listing of `services/agent-generator/app/`.

### 5.3 Configuration

File: `app/config.py` (222 lines)

- Uses `pydantic_settings.BaseSettings` with `SettingsConfigDict`
- Loads `.env` relative to package root (`Path(__file__).parent.parent / ".env"`)
- `main.py:17-21` also calls `load_dotenv()` to export `.env` to `os.environ`
- 7 LLM provider API key fields: ZAI, Portkey, OpenAI, Anthropic, OpenRouter, Google, Mistral
- Default provider: `zai` (line 66), Default model: `GLM-5` (line 67-68)
- Provider fallback chain: ZAI → Portkey → OpenAI (lines 201-212)
- Rate limiting: `enable_rate_limiting=False` by default (line 101)
- CORS: `allowed_origins` defaults to `["http://localhost:3000", "http://localhost:5173"]` (line 81-83)
- Settings cached with `@lru_cache` (line 215)

### 5.4 API Endpoints

**47 route decorators** across 9 files + 1 root endpoint in `main.py:149` = **48 total endpoints**.

| Route File | Decorator Count | Source |
|------------|-----------------|--------|
| `tools.py` | 14 | grep count |
| `teams.py` | 9 | grep count |
| `agents.py` | 6 | grep count |
| `generate.py` | 4 | grep count |
| `templates.py` | 4 | grep count |
| `business_dev.py` | 3 (all 501 NOT IMPLEMENTED) | grep count, lines 34/59/78 |
| `health.py` | 3 | grep count |
| `users.py` | 2 | grep count |
| `validate.py` | 2 | grep count |
| `main.py` (root `/`) | 1 | line 149 |

9 routers registered in `main.py:126-144`: generate, validate, health, agents, tools, users, teams, templates, business_dev.

### 5.5 Tool Definitions

11 files in `app/tools/`:

| File | Purpose |
|------|---------|
| `registry.py` | Tool registration and lookup |
| `ai_tools.py` | AI/ML tool definitions |
| `automation_tools.py` | Automation tool definitions |
| `cloud_tools.py` | Cloud provider tools |
| `composio_tools.py` | Composio integration (850+ apps) |
| `database_tools.py` | Database tool definitions |
| `file_tools.py` | File/document tools |
| `integration_tools.py` | Third-party integrations |
| `mcp_adapter.py` | MCP (Model Context Protocol) adapter |
| `search_tools.py` | Search tool definitions |
| `web_tools.py` | Web scraping tools |

### 5.6 Exception Hierarchy

File: `app/utils/exceptions.py` (126 lines) — **8 classes**:

1. `AgentGeneratorException` (base) — `message`, `detail`, `error_code`
2. `CodeValidationError` — adds `errors`, `warnings`
3. `LLMServiceException` — adds `provider`, `original_error`
4. `DatabaseException` — adds `query`, `original_error`
5. `CacheException` — adds `key`
6. `ValidationException` — adds `field`, `value`
7. `RateLimitException` — adds `retry_after`
8. `ConfigurationException` — adds `setting`

### 5.7 Authentication

File: `app/api/auth.py` (278 lines)

- **Dev-mode only** — `auth.py:5`: `TODO: Add production auth (JWT/OAuth) later.`
- `get_current_user()` reads `X-User-Id`, `X-User-Email`, `X-User-Name` headers
- If no `X-User-Id` provided, returns hardcoded dev user `00000000-0000-0000-0000-000000000000` (line 49-53)
- `TeamRoleChecker` class with role hierarchy: owner(4) > admin(3) > member(2) > viewer(1) (lines 82-87)
- Helper functions: `get_team_role()`, `verify_team_ownership_or_admin()`, `verify_team_ownership()`
- Factory: `require_team_role()`, pre-built: `require_admin_or_owner`, `require_owner` (lines 271-278)

### 5.8 CORS

Configured in `main.py:104-110`:
```python
CORSMiddleware(
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### 5.9 Dependencies

File: `requirements.txt` (141 lines) — major packages:
- Core: `fastapi>=0.109.0`, `uvicorn[standard]>=0.27.0`, `pydantic>=2.5.3`, `pydantic-settings>=2.1.0`
- LLM: `openai>=1.12.0`, `anthropic>=0.18.0`, `portkey-ai>=1.10.0`
- DB: `sqlalchemy>=2.0.25`, `asyncpg>=0.29.0`, `redis>=5.0.1`
- CrewAI: `crewai>=0.11.0`, `crewai-tools>=0.0.1`, `mcp>=1.0.0`
- AI/ML: `langchain>=0.1.0`, `sentence-transformers>=2.3.0`, `chromadb>=0.4.22`
- Cloud: `boto3>=1.34.0`, `azure-storage-blob>=12.19.0`, `google-cloud-storage>=2.14.0`
- Integration: `composio-core>=0.6.11`, `composio-crewai>=0.1.0`, `slack-sdk>=3.26.0`, `PyGithub>=2.1.0`
- Logging: `structlog>=24.1.0`
- Dev: `ruff>=0.2.0`, `mypy>=1.8.0`, `black>=24.1.0`

### 5.10 Dockerfile

File: `Dockerfile` (48 lines)
- Single-stage build from `python:3.11-slim`
- System deps: `curl` only
- Healthcheck: `curl -f http://localhost:8001/health`
- Env: `PYTHONUNBUFFERED=1`, `PYTHONDONTWRITEBYTECODE=1`
- CMD: `uvicorn app.main:app --host 0.0.0.0 --port 8001`

### 5.11 Lint & Type Config

File: `pyproject.toml` (19 lines)

```toml
[tool.ruff]
line-length = 100
target-version = "py313"
# NOTE: No [tool.ruff.lint] section — no select/ignore rules specified

[tool.mypy]
python_version = "3.13"
warn_return_any = true
warn_unused_configs = true
# NOTE: No strict mode, no disallow_untyped_defs
```

---

## 6. Docker Orchestrator Service

### 6.1 Identity

| Field | Value | Source |
|-------|-------|--------|
| Package name | `laias-docker-orchestrator` | `pyproject.toml:2` |
| Version (package) | `0.1.0` | `pyproject.toml:3` |
| Version (app) | `1.0.0` | `app/__init__.py:8` |
| Service version (config) | `1.0.0` | `config.py:28` |
| Python required | `>=3.11` | `pyproject.toml:9` |
| Dockerfile base | `python:3.11-slim` (multi-stage) | `Dockerfile:5,28` |
| Internal port | 8002 | `Dockerfile:59`, `config.py:37` |

### 6.2 Application Structure

```
app/
├── __init__.py          # __version__ = "1.0.0"
├── main.py              # Direct app creation (not factory), lifespan, CORS
├── config.py            # Settings (Pydantic BaseSettings)
├── api/
│   └── routes/          # 5 route files
├── models/
│   ├── database.py      # SQLAlchemy ORM
│   ├── requests.py      # Pydantic request schemas
│   └── responses.py     # Pydantic response schemas
├── services/
│   ├── analytics_store.py    # Analytics data storage
│   ├── analyticsSeeder.py    # Analytics seed data
│   ├── container_manager.py  # Container lifecycle
│   ├── docker_service.py     # Docker SDK wrapper
│   ├── log_streamer.py       # Log streaming (WebSocket/SSE)
│   └── resource_monitor.py   # Container resource monitoring
└── utils/
    └── exceptions.py    # 7 exception classes + converter function
```

### 6.3 Configuration

File: `app/config.py` (172 lines)

- Uses `pydantic_settings.BaseSettings` with `SettingsConfigDict`
- Docker: `DOCKER_HOST=None` (default socket), `DOCKER_NETWORK=laias-network`, `AGENT_IMAGE_BASE=laias/agent-runner:latest`
- Container limits: `DEFAULT_CPU_LIMIT=1.0` (0.1-4.0), `DEFAULT_MEMORY_LIMIT=512m`, `MAX_CONTAINERS=50` (1-200)
- Security: `SECRET_KEY=change-this-in-production`, `API_KEYS=[]` (disabled by default)
- Metrics: `METRICS_ENABLED=True`, `HEALTH_CHECK_INTERVAL=30`
- Uses `@validator` (Pydantic v1 style) on lines 149 and 157 — should be `@field_validator` for Pydantic v2

### 6.4 API Endpoints

**20 route decorators** across 5 files + 1 root endpoint in `main.py:141` = **21 total endpoints**.

| Route File | Decorator Count | Source |
|------------|-----------------|--------|
| `containers.py` | 7 | grep count |
| `analytics.py` | 6 | grep count |
| `health.py` | 3 | grep count |
| `deploy.py` | 2 | grep count |
| `logs.py` | 2 | grep count |
| `main.py` (root `/`) | 1 | line 141 |

5 routers registered in `main.py:119-137`: deploy, containers, logs, health, analytics.

### 6.5 Exception Hierarchy

File: `app/utils/exceptions.py` (138 lines) — **7 classes** + 1 converter function:

1. `OrchestratorException` (base) — `message`, `detail`, `error_code`
2. `ContainerNotFoundError` — adds `container_id`
3. `DeploymentError` — adds `agent_id`, `reason`
4. `DockerConnectionError` — adds `reason`
5. `ResourceLimitError` — adds `limit_type`, `current`, `maximum`
6. `InvalidConfigurationError` — adds `field`, `reason`
7. `LogStreamingError` — adds `container_id`, `reason`

`exception_to_http_response()` — maps error codes to HTTP status codes (line 114-138)

### 6.6 CORS

Configured in `main.py:88-94`:
```python
CORSMiddleware(
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 6.7 Dependencies

File: `requirements.txt` (37 lines) — major packages:
- Core: `fastapi>=0.104.0`, `uvicorn[standard]>=0.24.0`, `websockets>=12.0`
- Docker: `docker>=7.0.0`
- DB: `sqlalchemy>=2.0.0`, `asyncpg>=0.29.0`, `redis>=5.0.0`, `alembic>=1.13.0` (not initialized)
- Config: `pydantic>=2.5.0`, `pydantic-settings>=2.1.0`
- Logging: `structlog>=23.2.0`
- Dev: `pytest>=7.4.0`, `pytest-asyncio>=0.21.0`, `pytest-cov>=4.1.0`, `pytest-mock>=3.12.0`, `ruff>=0.1.0`, `mypy>=1.7.0`

### 6.8 Dockerfile

File: `Dockerfile` (69 lines) — **multi-stage build**:
- Stage 1 (builder): `python:3.11-slim`, installs gcc, creates venv, installs deps
- Stage 2 (runtime): `python:3.11-slim`, copies venv from builder, installs curl
- Creates non-root user `laias` (uid 1000) — but runs as root for Docker socket access
- Healthcheck: `curl -f http://localhost:8002/health`
- CMD: `uvicorn app.main:app --host 0.0.0.0 --port 8002 --workers 1`

### 6.9 Lint & Type Config

File: `pyproject.toml` (47 lines)

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
# NOTE: No strict mode
```

---

## 7. Frontend — Studio UI

### 7.1 Identity

| Field | Value | Source |
|-------|-------|--------|
| Package name | `laias-studio-ui` | `package.json:2` |
| Version | `0.1.0` | `package.json:3` |
| Framework | Next.js 15.0.3 | `package.json:18` |
| React | 18.3.1 | `package.json:19` |
| TypeScript | 5.6.3 | `package.json:36` |
| Dev port | 3000 | `package.json:6` |

### 7.2 Dependencies

**Runtime** (package.json:13-24):
- `@hookform/resolvers`, `react-hook-form` — form handling
- `@monaco-editor/react` — code editor
- `clsx`, `tailwind-merge` — styling utilities
- `lucide-react` — icons
- `zod` — schema validation
- `zustand` — state management

**Dev** (package.json:26-37):
- `eslint` + `eslint-config-next`
- `tailwindcss`, `postcss`, `autoprefixer`
- `openapi-typescript` — type generation from OpenAPI specs

### 7.3 Scripts

| Script | Command | Source |
|--------|---------|--------|
| `dev` | `next dev --port 3000` | `package.json:6` |
| `build` | `next build` | `package.json:7` |
| `start` | `next start --port 3000` | `package.json:8` |
| `lint` | `next lint` | `package.json:9` |
| `type-check` | `tsc --noEmit` | `package.json:10` |
| `generate:types` | `openapi-typescript ...` | `package.json:11` |

### 7.4 App Router Pages

Directory: `frontend/studio-ui/app/`:
- `page.tsx` — home/landing
- `layout.tsx` — root layout
- `create/` — agent creation flow
- `agents/` — agent list/management
- `templates/` — template browsing
- `settings/` — settings page

---

## 8. Frontend — Control Room

### 8.1 Identity

| Field | Value | Source |
|-------|-------|--------|
| Package name | `laias-control-room` | `package.json:2` |
| Version | `0.1.0` | `package.json:3` |
| Framework | Next.js 15.0.3 | `package.json:15` |
| React | 18.3.1 | `package.json:16` |
| TypeScript | 5.6.3 | `package.json:32` |
| Dev port | 3001 | `package.json:6` |

### 8.2 Dependencies

**Runtime** (package.json:12-21):
- `@tanstack/react-virtual` — list virtualization
- `clsx`, `tailwind-merge` — styling utilities
- `lucide-react` — icons
- `recharts` — charting
- `zustand` — state management

**Dev** (package.json:23-33):
- `eslint` + `eslint-config-next`
- `tailwindcss`, `postcss`, `autoprefixer`

### 8.3 Scripts

| Script | Command | Source |
|--------|---------|--------|
| `dev` | `next dev --port 3001` | `package.json:6` |
| `build` | `next build` | `package.json:7` |
| `start` | `next start --port 3001` | `package.json:8` |
| `lint` | `next lint` | `package.json:9` |
| `type-check` | `tsc --noEmit` | `package.json:10` |

### 8.4 App Router Pages

Directory: `frontend/control-room/app/`:
- `page.tsx` — dashboard overview
- `layout.tsx` — root layout
- `error.tsx` — error boundary
- `loading.tsx` — loading state
- `containers/` — container management
- `metrics/` — system metrics

---

## 9. Shared Frontend Types

File: `frontend/shared/types/index.ts` (239 lines)

- Re-exports from auto-generated `agent-generator.ts` and `docker-orchestrator.ts`
- 46 tool definitions in `AVAILABLE_TOOLS` constant (lines 169-237)
- Tool categories: web (7), files (8), code (4), database (4), communication (5), ai (3), cloud (5), data (3), browser (3), media (3), utility (1)
- Enums: `AgentComplexity`, `AgentTaskType`, `LLMProvider`, `ContainerStatus`, `DeploymentStatus`, `LogLevel`, `ServiceHealthStatus`, `LoadingState`
- Shared interfaces: `ErrorResponse`, `RegenerateRequest`, `LogEntry`, `LogStreamEvent`, `ApiClientConfig`, `AsyncState<T>`, `AgentFormData`
- `API_CONFIG` constant with base URLs falling back to `localhost:4521` / `localhost:4522`

---

## 10. Templates

Directory: `templates/presets/` — **126 YAML files** (verified by directory listing)

Includes `NEW_AGENT_TEMPLATE.yaml` (blank template) and `TOP_20_WORKFLOWS.yaml` (curated list). The rest are production-ready CrewAI agent configurations spanning development, project management, QA, research, security, and more.

Reference template: `templates/godzilla_reference.py` — the "Gold Standard" pattern all generated agents must follow.

---

## 11. Testing

### 11.1 Agent Generator Tests

Directory: `services/agent-generator/tests/` — 3 files:
- `conftest.py` — fixtures
- `test_generate.py` — 4 test functions (1 commented out: `test_generate_agent_success`, lines 54-69)
- `test_validate.py` — 3 test functions

Additional root-level test files (outside `tests/`):
- `test_llm_e2e.py` — 1 async e2e test
- `test_zai_direct.py` — 1 async provider test

**Total: 9 active test functions, 1 commented out.**

### 11.2 Docker Orchestrator Tests

Directory: `services/docker-orchestrator/tests/` — 2 files:
- `conftest.py` — fixtures
- `test_health.py` — 3 test functions

**Total: 3 test functions.**

### 11.3 Frontend Tests

**Zero.** No test files, no test dependencies, no test scripts in either frontend app.

---

## 12. CI Pipeline

File: `.github/workflows/ci.yml` (87 lines)

Triggers: push to `main`/`develop`, PRs to `main` (lines 3-7)

4 jobs:
1. `test-agent-generator` — Python 3.11, `pip install -r requirements.txt`, `pytest -v`
2. `test-docker-orchestrator` — Python 3.11, `pip install -r requirements.txt`, `pytest -v`
3. `lint` — `ruff check services/`
4. `docker-build` — builds 3 images: agent-generator, docker-orchestrator, agent-runner

**Not covered**: frontend build/lint/type-check, mypy, integration tests, deployment.

---

## 13. Endpoint Summary

| Service | Route Decorators | Root Endpoint | Total |
|---------|-----------------|---------------|-------|
| Agent Generator | 47 | 1 (`main.py:149`) | **48** |
| Docker Orchestrator | 20 | 1 (`main.py:141`) | **21** |
| **Grand Total** | | | **69** |

---

## 14. Port Map

| Service | Host Port | Container Port | Source |
|---------|-----------|----------------|--------|
| PostgreSQL | 5432 | 5432 | `docker-compose.yml:17` |
| Redis | 6379 | 6379 | `docker-compose.yml:34` |
| Agent Generator | 4521 | 8001 | `docker-compose.yml:69` |
| Docker Orchestrator | 4522 | 8002 | `docker-compose.yml:114` |
| Studio UI | 4527 | 3000 | `docker-compose.yml:157` |
| Control Room | 4528 | 3001 | `docker-compose.yml:186` |
