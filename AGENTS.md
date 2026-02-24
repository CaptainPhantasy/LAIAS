# AGENTS.md — LAIAS Codebase Guide for AI Agents

## Project Overview

LAIAS (Legacy AI Agent Studio) is a Dockerized platform for generating, deploying, and
monitoring CrewAI agents via natural language. It has two Python/FastAPI backend services
and two Next.js 15 frontend apps, all orchestrated with Docker Compose.

## Repository Layout

```
services/agent-generator/     # FastAPI — LLM-powered code generation (port 8001)
services/docker-orchestrator/  # FastAPI — container lifecycle management (port 8002)
frontend/studio-ui/            # Next.js 15 — chat-to-agent builder (port 3000)
frontend/control-room/         # Next.js 15 — agent monitoring dashboard (port 3001)
frontend/shared/               # Shared types and utilities for both frontends
infrastructure/                # PostgreSQL init SQL, Redis config
templates/                     # Gold-standard CrewAI agent templates (126 configs)
agents/                        # Standalone agent scripts and imported agents
```

## Build, Lint, and Test Commands

### Full Stack (Docker)

```bash
docker-compose up -d                      # Start all services
docker-compose up -d --build              # Rebuild and start
docker-compose down                       # Stop all services
```

### Agent Generator (Python — `services/agent-generator/`)

```bash
# Install
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload --port 8001

# Tests — all
pytest -v

# Tests — single file
pytest tests/test_generate.py -v

# Tests — single test function
pytest tests/test_generate.py::test_health_endpoint -v

# Tests — by marker
pytest -m asyncio -v          # async tests only
pytest -m integration -v      # integration tests only

# Lint
ruff check app/ tests/

# Type check
mypy app/
```

### Docker Orchestrator (Python — `services/docker-orchestrator/`)

```bash
# Install
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload --port 8002

# Tests — all
pytest -v

# Tests — single file
pytest tests/test_health.py -v

# Tests — single test function
pytest tests/test_health.py::test_function_name -v

# Lint
ruff check app/ tests/

# Type check
mypy app/
```

### Studio UI (Next.js — `frontend/studio-ui/`)

```bash
npm install
npm run dev          # Dev server on port 3000
npm run build        # Production build
npm run lint         # ESLint (next/core-web-vitals)
npm run type-check   # TypeScript strict check (tsc --noEmit)
```

### Control Room (Next.js — `frontend/control-room/`)

```bash
npm install
npm run dev          # Dev server on port 3001
npm run build        # Production build
npm run lint         # ESLint
npm run type-check   # TypeScript strict check (tsc --noEmit)
```

### CI Pipeline (`.github/workflows/ci.yml`)

CI runs on push to `main`/`develop` and PRs to `main`. Steps: pytest for both
Python services, `ruff check services/` for linting, Docker image builds.

## Python Code Style (Backend Services)

### Formatter & Linter

- **Ruff** is the linter. Config in each service's `pyproject.toml`.
- Line length: **100 characters**.
- Lint rules (docker-orchestrator, canonical): `E, F, I, N, W, UP` (pycodestyle,
  pyflakes, isort, pep8-naming, warnings, pyupgrade). `E501` is ignored.
- Target: Python 3.11+ (orchestrator), Python 3.13 (agent-generator).

### Imports

- Standard library first, then third-party, then local (`app.*`).
- Ruff enforces isort-compatible ordering (`I` rule).
- Use absolute imports from `app` package: `from app.config import settings`.
- Lazy imports inside functions are used for circular dependency avoidance
  (see `app/main.py` importing routers inside `create_app()`).

### Typing

- Use `from typing import Optional, Literal` for type annotations.
- Use modern syntax where possible: `list[str]` over `List[str]`, `str | None` patterns.
- Pydantic v2 `BaseModel` for all request/response schemas.
- `pydantic-settings` `BaseSettings` for configuration with `SettingsConfigDict`.
- `Field(...)` with descriptions on all Pydantic model fields.
- Use `@field_validator` (not `@validator`) — this is Pydantic v2.

### Naming Conventions

- **Files**: `snake_case.py` — e.g., `llm_provider.py`, `code_generator.py`.
- **Classes**: `PascalCase` — e.g., `GenerateAgentRequest`, `OrchestratorException`.
- **Functions/methods**: `snake_case` — e.g., `create_app`, `validate_agent_name`.
- **Constants**: `UPPER_SNAKE_CASE` — e.g., `ENV_FILE_PATH`, `CONFIG_DIR`.
- **API routes**: kebab-case URLs — e.g., `/api/generate-agent`, `/api/validate-code`.

### Error Handling

- Custom exception hierarchy per service (see `app/utils/exceptions.py`).
- Base exception class (e.g., `OrchestratorException`) with `message`, `detail`, `error_code`.
- Specific subclasses: `ContainerNotFoundError`, `DeploymentError`, `ResourceLimitError`.
- FastAPI exception handlers convert custom exceptions to structured JSON responses.
- Global `Exception` handler catches unhandled errors and returns 500 with `structlog` logging.

### Logging

- Use `structlog` exclusively — not stdlib `logging`.
- JSON-formatted output with ISO timestamps.
- Get logger with `logger = structlog.get_logger()`.
- Structured key-value pairs: `logger.info("message", key=value)`.

### Testing

- `pytest` with `pytest-asyncio` for async tests.
- Mark async tests with `@pytest.mark.asyncio`.
- Custom markers: `asyncio`, `integration` (defined in `conftest.py`).
- Use `FastAPI TestClient` for endpoint tests.
- Mocking: `unittest.mock.AsyncMock` and `patch` for LLM providers.
- Fixtures in `tests/conftest.py`.

### Project Structure Pattern

```
app/
  __init__.py          # Package init with __version__
  main.py              # FastAPI app factory (create_app) and lifespan
  config.py            # Pydantic Settings class
  api/
    routes/            # One file per route group (generate.py, health.py, etc.)
    dependencies.py    # FastAPI dependency injection
  models/
    requests.py        # Pydantic request schemas
    responses.py       # Pydantic response schemas
    database.py        # SQLAlchemy ORM models
  services/            # Business logic (llm_provider.py, code_generator.py)
  utils/               # Helpers and custom exceptions
tests/
  conftest.py          # Fixtures and markers
  test_*.py            # Test files mirror app structure
```

## TypeScript/Next.js Code Style (Frontend)

### Framework & Config

- **Next.js 15** with App Router (`app/` directory).
- **TypeScript** in strict mode (`"strict": true` in tsconfig).
- **Tailwind CSS 3** for styling with CSS custom properties (design tokens).
- **Zustand** for state management (not Redux).
- ESLint extends `next/core-web-vitals`.

### Path Aliases

Use `@/` prefix for imports (configured in tsconfig `paths`):
- `@/components/*`, `@/hooks/*`, `@/lib/*`, `@/types/*`, `@/store/*`, `@/styles/*`
- `@/shared/*` resolves to `../shared/*` (cross-app shared code).

### Naming Conventions

- **Component files**: `PascalCase` directories, files match component name.
- **Utility files**: `kebab-case.ts` — e.g., `keyboard-navigation.ts`, `state-machine.ts`.
- **Types files**: `index.ts` barrel exports in `types/` directory.
- **Store files**: `kebab-case.ts` — e.g., `builder-store.ts`.
- **Interfaces/Types**: `PascalCase` — e.g., `BuilderState`, `ValidationStatus`.

### Patterns

- Export named functions (not default) for utilities and API clients.
- Use `export const` for constant objects and `as const` for literal types.
- API client in `lib/api.ts` — plain `fetch` with typed error handling (`ApiError` class).
- Zustand stores: `create<State>()(persist(...))` pattern with selectors and action hooks.
- Custom hooks: extracted into `hooks/` or co-exported from store files.
- Use `cn()` helper (clsx + tailwind-merge) for conditional class names.

### Styling

- Tailwind with custom design tokens via CSS variables (see `tailwind.config.ts`).
- Color tokens: `bg-primary`, `surface`, `text-primary`, `accent-cyan`, etc.
- Dark mode via `[data-theme="dark"]` class strategy.
- Fonts: Inter (sans), JetBrains Mono (mono).
- Elevation system: `shadow-elevation-{0-5}`, glow effects: `shadow-glow-cyan`.

### Section Separators

Both Python and TypeScript files use comment-block section separators:
```python
# =============================================================================
# Section Name
# =============================================================================
```
```typescript
// ============================================================================
// Section Name
// ============================================================================
```

## Environment Variables

- Backend services read from `.env` files via `pydantic-settings` AND `python-dotenv`.
- Frontend uses `NEXT_PUBLIC_*` prefix for client-side env vars (baked at build time).
- Never commit `.env` files. Use `.env.example` as reference.
- Key vars: `ZAI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `DATABASE_URL`, `REDIS_URL`.

## Docker Ports (Production)

| Service              | Host Port | Container Port |
|----------------------|-----------|----------------|
| Agent Generator      | 4521      | 8001           |
| Docker Orchestrator  | 4522      | 8002           |
| Studio UI            | 4527      | 3000           |
| Control Room         | 4528      | 3001           |
| PostgreSQL           | 5432      | 5432           |
| Redis                | 6379      | 6379           |
