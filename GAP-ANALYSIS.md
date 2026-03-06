# LAIAS Gap Analysis — Path to 100% Functionality

> Generated from exhaustive code review. Every claim cites `file:line`.
> Date: 2026-03-06

---

## Priority Legend

| Priority | Meaning |
|----------|---------|
| **P0** | Blocks core functionality — platform cannot work without this |
| **P1** | Significant deficiency — major feature incomplete or broken |
| **P2** | Quality/reliability gap — works but fragile or incorrect |
| **P3** | Polish/hardening — nice to have for production readiness |

---

## P0 — Blocking Issues

### 1. Python Version Mismatch (agent-generator)

`pyproject.toml:5` declares `requires-python = ">=3.13,<3.14"` but `Dockerfile:13` builds from `python:3.11-slim`.

**Impact**: Any code using Python 3.13 features (e.g., improved error messages, new typing features) will fail in the Docker container. The pyproject.toml constraint means `pip install` will refuse to install the package on 3.11.

**Fix**: Either change Dockerfile to `python:3.13-slim` or relax pyproject.toml to `>=3.11`.

### 2. No Database Migration System

Schema is defined only in `infrastructure/init.sql`. A comment in `database/session.py:71` says "Use Alembic for production migrations instead" — but no Alembic config, migration directory, or `alembic.ini` exists anywhere in the repo.

**Impact**: Any schema change requires manually editing `init.sql` and recreating the database from scratch. No rollback capability. No migration history. Data loss on every schema change.

**Fix**: Initialize Alembic in both services, generate initial migration from `init.sql`, establish migration workflow.

### 3. Authentication is Dev-Mode Only

`auth.py:5` — `TODO: Add production auth (JWT/OAuth) later.`

Current behavior (`auth.py:47-53`): If no `X-User-Id` header is provided, a hardcoded dev user (`00000000-0000-0000-0000-000000000000`) is silently injected. Any request without the header gets full access.

`python-jose` is in `requirements.txt` but JWT validation is not implemented anywhere.

**Impact**: Zero access control. Any HTTP client has full admin access to all endpoints. Agent code, team data, and deployment controls are completely unprotected.

**Fix**: Implement JWT validation in `get_current_user()`, add token issuance endpoint, integrate with frontend auth flow.

### 4. Business Dev Endpoints Return 501

All 3 endpoints in `business_dev.py` return HTTP 501 NOT IMPLEMENTED:
- `POST /api/business-dev-campaign` (line 34)
- `GET /api/business-dev-campaign/{agent_id}` (line 59)
- `POST /api/business-dev-campaign/{agent_id}/stop` (line 78)

**Impact**: If the frontend calls these (and it likely does based on the route registration), users get 501 errors.

**Fix**: Either implement the endpoints or remove them from the router registration and frontend.

---

## P1 — Significant Deficiencies

### 5. Zero Frontend Tests

No test files exist in either frontend app:
- `frontend/studio-ui/` — no `*.test.*`, no `*.spec.*` files
- `frontend/control-room/` — no `*.test.*`, no `*.spec.*` files
- No test dependencies (`jest`, `vitest`, `@testing-library/*`) in any `package.json`
- No test scripts in `package.json`

**Impact**: No regression protection for the entire UI layer. Any change can silently break user-facing functionality.

**Fix**: Add Vitest + @testing-library/react, write tests for critical flows (agent creation, deployment, monitoring).

### 6. Backend Test Coverage is Minimal

**Agent Generator**: 3 test files, 7 test functions defined, 1 commented out:
- `test_generate.py`: `test_root_endpoint`, `test_generate_agent_success` (COMMENTED OUT, lines 54-69), `test_generate_agent_validation_error`, `test_health_endpoint`
- `test_validate.py`: `test_validate_code_success`, `test_validate_code_syntax_error`, `test_validation_rules_endpoint`
- `test_llm_e2e.py` (root level, not in tests/): 1 e2e test
- `test_zai_direct.py` (root level): 1 provider-specific test

**Docker Orchestrator**: 1 test file, 3 test functions:
- `test_health.py`: `test_root_endpoint`, `test_health_endpoint`, `test_containers_list`

**Total**: ~10 test functions for 69 API endpoints = **14% endpoint coverage**.

**Impact**: Most endpoints have zero test coverage. Regressions go undetected.

**Fix**: Prioritize tests for: generate-agent, deploy, container lifecycle, team CRUD, agent CRUD.

### 7. CI Pipeline Missing Frontend Checks

`.github/workflows/ci.yml` runs:
- ✅ pytest for both Python services
- ✅ `ruff check services/`
- ✅ Docker image builds

Missing:
- ❌ `npm run build` for studio-ui
- ❌ `npm run build` for control-room
- ❌ `npm run lint` for frontends
- ❌ `npm run type-check` for frontends
- ❌ Frontend tests (none exist yet — see #5)
- ❌ Integration tests
- ❌ mypy type checking for Python services

**Impact**: Frontend can be broken on main without CI catching it.

**Fix**: Add frontend build/lint/type-check jobs to CI. Add mypy step.

### 8. Silent Error Swallowing (20 instances)

Empty `except: pass` blocks that silently discard errors:

**Agent Generator — Core Services** (errors here mean broken functionality):
| File | Line | Context |
|------|------|---------|
| `app/services/llm_service.py` | 286 | LLM response parsing |
| `app/services/llm_service.py` | 295 | LLM response parsing |
| `app/services/llm_service.py` | 310 | LLM response parsing |
| `app/services/orchestrator_client.py` | 111 | Orchestrator communication |

**Agent Generator — Tool Definitions** (8 files):
| File | Line |
|------|------|
| `app/tools/ai_tools.py` | 209 |
| `app/tools/search_tools.py` | 175 |
| `app/tools/database_tools.py` | 203 |
| `app/tools/web_tools.py` | 139 |
| `app/tools/cloud_tools.py` | 218 |
| `app/tools/file_tools.py` | 145 |
| `app/tools/integration_tools.py` | 385 |
| `app/tools/automation_tools.py` | 189 |

**Docker Orchestrator**:
| File | Line | Context |
|------|------|---------|
| `app/services/log_streamer.py` | 165 | Log streaming |
| `app/api/routes/logs.py` | 165 | Log endpoint |
| `app/api/routes/logs.py` | 172 | Log endpoint |
| `app/api/routes/logs.py` | 232 | Log endpoint |
| `app/api/routes/containers.py` | 82 | Container management |
| `app/api/routes/health.py` | 134 | Health check |

**Impact**: Failures in LLM parsing, orchestrator communication, and container management are silently swallowed. Users see no error — the operation just silently fails or returns incomplete data.

**Fix**: Replace `pass` with `structlog` logging at minimum. For critical paths (llm_service, orchestrator_client), raise or return error responses.

---

## P2 — Quality & Correctness Gaps

### 9. Type Errors in SQLAlchemy Models (30+ instances)

All route files that access SQLAlchemy `Column` attributes have type mismatches — `Column[str]` vs `str`, `Column[datetime]` vs `datetime`, etc. These are in:

- `app/api/routes/agents.py`: lines 178, 180, 184, 185, 188, 189, 191, 256, 287, 318, 325
- `app/api/routes/generate.py`: lines 146, 148
- `app/api/routes/health.py`: line 166 (`"bool" is not awaitable`)
- `app/api/routes/teams.py`: ~20 lines (148-543)
- `app/api/routes/templates.py`: line 204

**Impact**: mypy would flag all of these. Runtime behavior is correct (SQLAlchemy resolves columns at runtime), but the type annotations are wrong, making IDE support and static analysis unreliable.

**Fix**: Use proper SQLAlchemy 2.0 `Mapped[T]` annotations on ORM models, or add `# type: ignore[assignment]` with explanation.

### 10. Ruff Lint Rules Not Configured (agent-generator)

`agent-generator/pyproject.toml:12-14` only sets `line-length=100` and `target-version="py313"`. No `select` or `extend-select` rules.

Compare to `docker-orchestrator/pyproject.toml` which has `select = ["E", "F", "I", "N", "W", "UP"]`.

**Impact**: Agent generator has no enforced lint rules beyond Ruff defaults. Inconsistent code quality between services.

**Fix**: Add matching `[tool.ruff.lint] select = ["E", "F", "I", "N", "W", "UP"]` to agent-generator's pyproject.toml.

### 11. mypy Configuration is Minimal

Both services (`pyproject.toml`) only configure:
```toml
[tool.mypy]
warn_return_any = true
warn_unused_configs = true
```

No `strict = true`, no `disallow_untyped_defs`, no `check_untyped_defs`. This means mypy catches almost nothing.

**Impact**: Type errors (like #9) go undetected. The mypy config provides false confidence.

**Fix**: Incrementally tighten: add `check_untyped_defs = true`, then `disallow_untyped_defs = true`, fix errors as they surface.

### 12. Hardcoded Database Password in docker-compose.yml

`docker-compose.yml:11`: `POSTGRES_PASSWORD: laias_secure_password`

This is committed to the repo in plaintext.

**Impact**: Security risk if repo is public or shared. Password is the same in every environment.

**Fix**: Move to `.env` file (already gitignored) and reference via `${POSTGRES_PASSWORD}` in docker-compose.yml.

---

## P3 — Production Hardening

### 13. No Health Check Dependencies Between Services

Docker Compose services declare `depends_on` but without `condition: service_healthy`. If postgres or redis starts slowly, the FastAPI services will crash on first DB connection attempt.

**Impact**: Intermittent startup failures, especially on cold starts or slow machines.

**Fix**: Add `healthcheck` to postgres/redis services, use `depends_on: { postgres: { condition: service_healthy } }`.

### 14. Frontend TODO: Client-Side Logging

`frontend/studio-ui/app/create/page.tsx:378`: `// TODO: Add proper client-side logging`

**Impact**: Frontend errors are invisible. No way to diagnose user-reported issues.

**Fix**: Add error boundary with logging service (Sentry, LogRocket, or custom).

### 15. No Rate Limiting

No rate limiting middleware on any endpoint. The LLM generation endpoints (`/api/generate-agent`) are expensive operations.

**Impact**: A single client can exhaust LLM API budgets or DoS the service.

**Fix**: Add FastAPI rate limiting middleware (e.g., `slowapi`) at minimum on generation endpoints.

### 16. No CORS Configuration Visible

No explicit CORS middleware configuration found in either FastAPI service's `main.py`.

**Impact**: Frontend apps on different ports (3000, 3001) may not be able to call backend APIs (8001, 8002) from the browser.

**Fix**: Verify if CORS is configured (may be in middleware not yet reviewed). If not, add `CORSMiddleware` with appropriate origins.

### 17. Agent Runner Image is Build-Only

`docker-compose.yml` defines `agent-runner` with `profiles: [build-only]`. This means it's never started by `docker-compose up` — it's only built as a base image.

**Impact**: If the image isn't pre-built, agent deployment will fail because the orchestrator expects `laias/agent-runner:latest` to exist.

**Fix**: Document that `docker-compose build agent-runner` must be run before first deployment. Or add it to a startup script.

### 18. No Graceful Shutdown Handling

No signal handlers or shutdown hooks visible in either FastAPI service for cleaning up:
- Active WebSocket connections (log streaming)
- Running container operations
- Database connection pools

**Impact**: Hard restarts may leave orphaned connections or incomplete operations.

**Fix**: Add FastAPI `lifespan` shutdown handlers for connection cleanup.

---

## Summary

| Priority | Count | Key Theme |
|----------|-------|-----------|
| **P0** | 4 | Version mismatch, no migrations, no auth, stub endpoints |
| **P1** | 4 | No tests (frontend), minimal tests (backend), missing CI, silent errors |
| **P2** | 4 | Type errors, lint gaps, weak mypy, hardcoded secrets |
| **P3** | 6 | Health checks, logging, rate limiting, CORS, runner image, shutdown |

**Total: 18 issues identified.**

### Recommended Fix Order

1. **P0-1**: Python version mismatch (5 min fix, blocks Docker builds)
2. **P0-3**: Auth implementation (high effort, blocks any real usage)
3. **P0-2**: Alembic setup (medium effort, blocks schema evolution)
4. **P0-4**: Business dev endpoints (remove or implement)
5. **P1-8**: Silent error swallowing (systematic, medium effort)
6. **P2-10**: Ruff rules alignment (5 min fix)
7. **P2-12**: Hardcoded password (5 min fix)
8. **P1-7**: CI pipeline for frontends (medium effort)
9. **P2-9**: SQLAlchemy type annotations (medium effort)
10. **P1-5/6**: Test coverage (high effort, ongoing)
11. **P3-***: Production hardening (as needed before deployment)
