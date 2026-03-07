# Output Destination Configuration & Bug Fixes

## TL;DR

> **Quick Summary**: Build a complete output destination configuration system so users can choose WHERE agent outputs go (filesystem path via in-app file browser), WHAT format (markdown, HTML), and WHICH backends (database, files, both) — all configured in the Studio UI before running an agent. Also fix the broken teams feature (missing dev user seed + hardcoded URLs) and the critical volume mount bug that loses outputs on container restart.
>
> **Deliverables**:
> - Docker-compose volume mount fix for persistent outputs
> - Dev user seed in init.sql + teams page URL/error fixes
> - Output Configuration SectionPanel in Studio UI create page
> - File browser API endpoint on orchestrator with path traversal protection
> - File browser tree component in Studio UI
> - Extended deploy payload (output_path, output_format) through full chain
> - Format conversion service (markdown → HTML) in orchestrator
> - Control Room output viewing integration (already partially built)
>
> **Estimated Effort**: Large
> **Parallel Execution**: YES - 4 waves
> **Critical Path**: Task 1 → Task 4 → Task 8 → Task 10 → Task 13 → Task 14 → F1-F4

---

## Context

### Original Request
User wants agent outputs to be the primary deliverable — "People are tasking agents because they actually want the fucking documents and work to be retained." The system must let users configure output destination (filesystem path via explorer), format (markdown/PDF/HTML), and backend (database/files/both) BEFORE running an agent. Additionally, the teams feature is broken and outputs are lost on container restart.

### Interview Summary
**Key Discussions**:
- File picker: In-app file browser (tree-view via API browsing configurable root) — NOT native OS picker (browser limitation)
- Browseable root: Configurable root path (set in .env, scoped browsing)
- Format generation: Post-processing conversion (agent produces markdown, system converts to HTML/PDF)
- Config scope: Per-run only (choose output settings each time you run)
- Teams bug: Create team button doesn't work, only lets user enter names

**Research Findings**:
- Studio UI create page uses react-hook-form + zod + SectionPanel components in 3-column grid
- Builder store uses Zustand + persist middleware (only formData and isAdvancedOpen persisted)
- Orchestrator already has output_config (postgres/files toggles) in deploy flow but frontend never sends it
- Teams API exists at agent-generator but init.sql never seeds the dev user → FK violation on team create
- Teams page hardcodes `localhost:4521` instead of using NEXT_PUBLIC_AGENT_GENERATOR_URL env var
- AGENT_OUTPUT_PATH is NOT mounted as a volume in docker-compose.yml — outputs live in ephemeral container storage

### Metis Review
**Identified Gaps** (addressed):
- Teams bug root cause: Missing dev user seed in init.sql → FK constraint violation → silent 500 error
- Volume mount architecture: Docker SDK interprets paths as HOST paths (sibling container pattern), so named volume on orchestrator makes outputs accessible
- File browser security: Must prevent directory traversal attacks with strict path validation
- PDF conversion adds heavy dependencies (WeasyPrint needs Pango/Cairo/+100MB) — deferred to v2, start with HTML only
- output_config schema: Add new fields alongside existing Dict[str, bool], don't break existing shape
- Teams page swallows errors to console.error — user never sees failure message
- Deploy flow: Frontend `deployAgent()` in api.ts never sends output_config — uses backend defaults

---

## Work Objectives

### Core Objective
Enable users to fully configure agent output destinations, formats, and storage backends from the Studio UI before running an agent, while fixing critical bugs that prevent teams from working and outputs from persisting.

### Concrete Deliverables
- `docker-compose.yml` with `agent_outputs` named volume for `/var/laias/outputs`
- `infrastructure/init.sql` with dev user seed
- `frontend/studio-ui/app/settings/team/page.tsx` with env var URLs and error display
- `frontend/studio-ui/components/agent-builder/output-config-panel.tsx` — new SectionPanel
- `frontend/studio-ui/components/agent-builder/file-browser.tsx` — tree-view component
- `services/docker-orchestrator/app/api/routes/filesystem.py` — file browser API
- Extended `DeployAgentRequest`, `DeployProxyRequest`, `OrchestratorClient` with output_path + output_format
- `services/docker-orchestrator/app/services/format_converter.py` — markdown → HTML conversion
- `services/docker-orchestrator/app/api/routes/convert.py` — conversion endpoint

### Definition of Done
- [ ] `docker-compose restart docker-orchestrator` → outputs survive (volume persists)
- [ ] `curl POST /api/teams` with dev user → returns team object (not 500)
- [ ] Studio UI create page shows Output Configuration section between Tools and Advanced Options
- [ ] File browser API returns directory listing, rejects path traversal attempts
- [ ] Deploy payload includes output_path, output_format, output_destinations
- [ ] Agent container receives LAIAS_OUTPUT_PATH env var with user-chosen path
- [ ] Format conversion endpoint converts markdown to HTML
- [ ] `npm run build && npm run type-check` passes for studio-ui
- [ ] `pytest -v` passes for docker-orchestrator
- [ ] `ruff check app/ tests/` passes for both Python services

### Must Have
- Persistent volume mount for agent outputs
- Dev user seed so teams feature works
- Output config UI section in create page
- File browser with path traversal protection
- Deploy flow carries output_path and output_format end-to-end
- HTML format conversion (markdown → HTML via mistune)

### Must NOT Have (Guardrails)
- No native OS file picker (browser limitation — in-app tree only)
- No PDF conversion in v1 (WeasyPrint adds +100MB to Docker image — deferred)
- No real-time file watching/streaming in file browser
- No output file viewer/browser UI (this is output CONFIGURATION, not viewing)
- No multi-format simultaneous conversion (one format per run)
- No custom CSS/templates for converted output (single built-in style)
- No changes to agent runner base image
- No auth system changes beyond seeding dev user
- No teams feature refactoring beyond fixing the bug
- No `as any` type casts, `@ts-ignore`, or empty catch blocks
- No hardcoded URLs in frontend code (use env vars)
- No breaking changes to existing output_config Dict[str, bool] shape

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: YES (pytest for Python, vitest config exists for frontend)
- **Automated tests**: Tests-after (add tests for new endpoints and services)
- **Framework**: pytest (Python), vitest (frontend if needed)

### QA Policy
Every task MUST include agent-executed QA scenarios.
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Frontend/UI**: Use Playwright (playwright skill) — Navigate, interact, assert DOM, screenshot
- **API/Backend**: Use Bash (curl) — Send requests, assert status + response fields
- **Infrastructure**: Use Bash (docker commands) — Verify volumes, container state

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — bug fixes + foundation, ALL independent):
├── Task 1: Fix docker-compose.yml volume mount [quick]
├── Task 2: Seed dev user in init.sql [quick]
├── Task 3: Fix teams page hardcoded URLs + error display [quick]
├── Task 4: File browser API endpoint on orchestrator [deep]
├── Task 5: Output config types + Zod schema extensions [quick]
├── Task 6: Format converter service (markdown → HTML) [unspecified-high]

Wave 2 (After Wave 1 — UI components + backend extensions):
├── Task 7: File browser tree component (depends: 4, 5) [visual-engineering]
├── Task 8: Output config SectionPanel (depends: 5, 7) [visual-engineering]
├── Task 9: Extend orchestrator deploy models (depends: 5) [quick]
├── Task 10: Extend agent-generator proxy + client (depends: 9) [quick]

Wave 3 (After Wave 2 — integration + wiring):
├── Task 11: Wire Studio UI deploy flow with output config (depends: 8, 10) [unspecified-high]
├── Task 12: Conversion endpoint + post-run hook (depends: 6, 9) [unspecified-high]
├── Task 13: Docker rebuild + integration smoke test (depends: 1, 11, 12) [quick]

Wave 4 (After Wave 3 — rebuild + verify):
├── Task 14: Control Room rebuild + output panel verify (depends: 1, 13) [quick]

Wave FINAL (After ALL tasks — independent review, 4 parallel):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Real manual QA (unspecified-high)
├── Task F4: Scope fidelity check (deep)

Critical Path: Task 1 → Task 4 → Task 8 → Task 10 → Task 13 → Task 14 → F1-F4
Parallel Speedup: ~65% faster than sequential
Max Concurrent: 6 (Wave 1)
```

### Dependency Matrix

| Task | Depends On | Blocks | Wave |
|------|-----------|--------|------|
| 1 | — | 13, 14 | 1 |
| 2 | — | — | 1 |
| 3 | — | — | 1 |
| 4 | — | 7 | 1 |
| 5 | — | 7, 8, 9 | 1 |
| 6 | — | 12 | 1 |
| 7 | 4, 5 | 8 | 2 |
| 8 | 5, 7 | 11 | 2 |
| 9 | 5 | 10, 12 | 2 |
| 10 | 9 | 11 | 2 |
| 11 | 8, 10 | 13 | 3 |
| 12 | 6, 9 | 13 | 3 |
| 13 | 1, 11, 12 | 14 | 3 |
| 14 | 1, 13 | F1-F4 | 4 |
| F1-F4 | 14 | — | FINAL |

### Agent Dispatch Summary

- **Wave 1**: **6 tasks** — T1 → `quick`, T2 → `quick`, T3 → `quick`, T4 → `deep`, T5 → `quick`, T6 → `unspecified-high`
- **Wave 2**: **4 tasks** — T7 → `visual-engineering`, T8 → `visual-engineering`, T9 → `quick`, T10 → `quick`
- **Wave 3**: **3 tasks** — T11 → `unspecified-high`, T12 → `unspecified-high`, T13 → `quick`
- **Wave 4**: **1 task** — T14 → `quick`
- **FINAL**: **4 tasks** — F1 → `oracle`, F2 → `unspecified-high`, F3 → `unspecified-high`, F4 → `deep`

---

## TODOs

- [ ] 1. Fix docker-compose.yml — Add persistent volume mount for agent outputs

  **What to do**:
  - Add `agent_outputs` named volume to the `volumes:` section at bottom of `docker-compose.yml` (after `agent_code`)
  - Add volume mount `agent_outputs:/var/laias/outputs` to the `docker-orchestrator` service `volumes:` list (after `agent_code:/var/laias/agents`)
  - This is a 2-line change. Do NOT modify any other service or volume.

  **Must NOT do**:
  - Do not change any other service's volume configuration
  - Do not add bind mounts (use named Docker volume)
  - Do not modify the agent-runner, studio-ui, or control-room services

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3, 4, 5, 6)
  - **Blocks**: Tasks 13, 14
  - **Blocked By**: None

  **References**:

  **Pattern References**:
  - `docker-compose.yml:126-130` — Existing orchestrator volumes section (Docker socket + agent_code). Add the new mount here.
  - `docker-compose.yml:209-215` — Existing named volumes section (postgres_data, redis_data, agent_code). Add `agent_outputs` here.

  **API/Type References**:
  - `services/docker-orchestrator/app/config.py:56-58` — `AGENT_OUTPUT_PATH = "/var/laias/outputs"` — this is the path that must be backed by the volume

  **WHY Each Reference Matters**:
  - `docker-compose.yml:126-130`: Shows exact YAML indentation and format for adding a volume mount to the orchestrator service
  - `docker-compose.yml:209-215`: Shows exact YAML format for declaring named volumes
  - `config.py:56-58`: Confirms the container path that must match the volume mount target

  **Acceptance Criteria**:
  - [ ] `docker-compose.yml` contains `agent_outputs:/var/laias/outputs` under docker-orchestrator volumes
  - [ ] `docker-compose.yml` contains `agent_outputs:` with `name: laias-agent-outputs` under top-level volumes

  **QA Scenarios**:

  ```
  Scenario: Volume mount persists outputs across container restart
    Tool: Bash (docker commands)
    Preconditions: docker-compose services running
    Steps:
      1. Run: docker-compose exec docker-orchestrator mkdir -p /var/laias/outputs/test-persistence
      2. Run: docker-compose exec docker-orchestrator sh -c "echo 'persist-test' > /var/laias/outputs/test-persistence/test.txt"
      3. Run: docker-compose restart docker-orchestrator
      4. Wait 30s for health check to pass
      5. Run: docker-compose exec docker-orchestrator cat /var/laias/outputs/test-persistence/test.txt
    Expected Result: Output is "persist-test" — file survived restart
    Failure Indicators: "No such file or directory" or empty output
    Evidence: .sisyphus/evidence/task-1-volume-persistence.txt

  Scenario: Volume appears in docker volume list
    Tool: Bash (docker commands)
    Preconditions: docker-compose up -d completed
    Steps:
      1. Run: docker volume ls --filter name=laias-agent-outputs --format "{{.Name}}"
    Expected Result: Output contains "laias-agent-outputs"
    Failure Indicators: Empty output
    Evidence: .sisyphus/evidence/task-1-volume-exists.txt
  ```

  **Commit**: YES (groups with Tasks 2, 3)
  - Message: `fix(infra): add output volume mount, seed dev user, fix teams page URLs`
  - Files: `docker-compose.yml`
  - Pre-commit: `docker-compose config --quiet` (validates YAML)

- [ ] 2. Seed dev user in infrastructure/init.sql

  **What to do**:
  - Add an INSERT statement at the end of `infrastructure/init.sql` to seed the dev user
  - SQL: `INSERT INTO users (id, email, name) VALUES ('00000000-0000-0000-0000-000000000000', 'dev@laias.local', 'Dev User') ON CONFLICT (id) DO NOTHING;`
  - The `users` table schema is: `id UUID PK, email VARCHAR UNIQUE, name VARCHAR, password_hash VARCHAR, created_at TIMESTAMPTZ, last_login TIMESTAMPTZ`. There is NO `is_active` column — do NOT include it.
  - Also run this INSERT directly against the running Postgres container so it takes effect immediately without requiring a full DB reset
  - Command: `docker exec laias-postgres psql -U laias -d laias -c "INSERT INTO users (id, email, name) VALUES ('00000000-0000-0000-0000-000000000000', 'dev@laias.local', 'Dev User') ON CONFLICT (id) DO NOTHING;"`

  **Must NOT do**:
  - Do not modify the users table schema
  - Do not add any other seed data
  - Do not change auth middleware behavior

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3, 4, 5, 6)
  - **Blocks**: None (teams page fix in Task 3 is independent)
  - **Blocked By**: None

  **References**:

  **Pattern References**:
  - `infrastructure/init.sql:238-245` — Users table schema showing columns: id (UUID PK), email (VARCHAR UNIQUE), name (VARCHAR), password_hash (VARCHAR), created_at (TIMESTAMPTZ), last_login (TIMESTAMPTZ). NOTE: There is NO `is_active` column.

  **API/Type References**:
  - `frontend/studio-ui/app/settings/team/page.tsx:57-58` — Dev user ID and email used in X-User-Id header: `'00000000-0000-0000-0000-000000000000'` and `'dev@laias.local'`

  **WHY Each Reference Matters**:
  - `init.sql:238-245`: Shows exact column names and types for the INSERT statement — must match schema
  - `team/page.tsx:57-58`: Shows the exact UUID and email the frontend sends — seed data must match these values

  **Acceptance Criteria**:
  - [ ] `infrastructure/init.sql` contains INSERT for dev user with UUID `00000000-0000-0000-0000-000000000000`
  - [ ] Running `docker exec laias-postgres psql -U laias -c "SELECT id FROM users WHERE id='00000000-0000-0000-0000-000000000000';"` returns 1 row

  **QA Scenarios**:

  ```
  Scenario: Dev user exists in database
    Tool: Bash (docker exec)
    Preconditions: Postgres container running
    Steps:
      1. Run: docker exec laias-postgres psql -U laias -d laias -c "SELECT id, email, name FROM users WHERE id = '00000000-0000-0000-0000-000000000000';"
    Expected Result: One row returned with id=00000000-0000-0000-0000-000000000000, email=dev@laias.local, name=Dev User
    Failure Indicators: "(0 rows)" or error
    Evidence: .sisyphus/evidence/task-2-dev-user-exists.txt

  Scenario: Create team succeeds after seed
    Tool: Bash (curl)
    Preconditions: Dev user seeded, agent-generator running
    Steps:
      1. Run: curl -s -X POST http://localhost:4521/api/teams -H "Content-Type: application/json" -H "X-User-Id: 00000000-0000-0000-0000-000000000000" -d '{"name":"Smoke Test Team"}'
      2. Parse response JSON
    Expected Result: HTTP 200/201, response contains "id" field with UUID value
    Failure Indicators: HTTP 500, response contains "detail" with error message
    Evidence: .sisyphus/evidence/task-2-create-team-works.txt
  ```

  **Commit**: YES (groups with Tasks 1, 3)
  - Message: `fix(infra): add output volume mount, seed dev user, fix teams page URLs`
  - Files: `infrastructure/init.sql`
  - Pre-commit: none

- [ ] 3. Fix teams page — Replace hardcoded URLs + add error display

  **What to do**:
  - In `frontend/studio-ui/app/settings/team/page.tsx`, replace ALL 6 instances of hardcoded `http://localhost:4521` with a constant: `const API_BASE = process.env.NEXT_PUBLIC_AGENT_GENERATOR_URL || 'http://localhost:4521';`
  - Add the constant at the top of the file (after imports, before component)
  - Replace each `fetch('http://localhost:4521/api/...` with `fetch(\`${API_BASE}/api/...`
  - Lines to change: 55, 79, 99, 141, 171, 189
  - Add user-facing error display in `createTeam()` function (line 95-122): currently catches errors with `console.error` but shows nothing to user. Add state `const [error, setError] = React.useState<string | null>(null);` and display it below the Create Team button
  - Also add error display for `addMember()` function — currently uses `alert()` for some errors but `console.error` for network failures

  **Must NOT do**:
  - Do not refactor the teams page beyond fixing URLs and error display
  - Do not add a Zustand store for teams
  - Do not change the API contract or add new endpoints
  - Do not modify the teams API backend

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 4, 5, 6)
  - **Blocks**: None
  - **Blocked By**: None

  **References**:

  **Pattern References**:
  - `frontend/studio-ui/app/create/page.tsx:32-34` — Pattern for API_BASE constant with env var fallback: `const API_BASE = typeof window !== 'undefined' ? ... : (process.env.NEXT_PUBLIC_AGENT_GENERATOR_URL || 'http://localhost:4521');`
  - `frontend/studio-ui/app/create/page.tsx:767-769` — Pattern for inline error display: `{generationError && (<p className="mt-2 text-sm text-error text-center">{generationError}</p>)}`

  **API/Type References**:
  - `frontend/studio-ui/app/settings/team/page.tsx:55` — First hardcoded URL instance (fetchTeams)
  - `frontend/studio-ui/app/settings/team/page.tsx:79` — Second instance (fetchTeamDetails)
  - `frontend/studio-ui/app/settings/team/page.tsx:99` — Third instance (createTeam)
  - `frontend/studio-ui/app/settings/team/page.tsx:141` — Fourth instance (addMember)
  - `frontend/studio-ui/app/settings/team/page.tsx:171` — Fifth instance (updateMemberRole)
  - `frontend/studio-ui/app/settings/team/page.tsx:189` — Sixth instance (removeMember)

  **WHY Each Reference Matters**:
  - `create/page.tsx:32-34`: Shows the exact pattern used elsewhere in the app for API base URL with env var — must follow same pattern for consistency
  - `create/page.tsx:767-769`: Shows the error display pattern with Tailwind classes — reuse same styling
  - `team/page.tsx` lines: All 6 locations where hardcoded URL must be replaced

  **Acceptance Criteria**:
  - [ ] `grep -c "localhost:4521" frontend/studio-ui/app/settings/team/page.tsx` returns 0
  - [ ] `grep -c "API_BASE" frontend/studio-ui/app/settings/team/page.tsx` returns ≥ 7 (1 declaration + 6 usages)
  - [ ] Error state variable exists and is rendered in the component
  - [ ] `cd frontend/studio-ui && npm run type-check` passes

  **QA Scenarios**:

  ```
  Scenario: Teams page loads without hardcoded URLs
    Tool: Bash (grep)
    Preconditions: File edited
    Steps:
      1. Run: grep -n "localhost:4521" frontend/studio-ui/app/settings/team/page.tsx
    Expected Result: No output (no matches)
    Failure Indicators: Any line containing "localhost:4521"
    Evidence: .sisyphus/evidence/task-3-no-hardcoded-urls.txt

  Scenario: Teams page TypeScript compiles
    Tool: Bash (npm)
    Preconditions: Dependencies installed
    Steps:
      1. Run: cd frontend/studio-ui && npm run type-check
    Expected Result: Exit code 0, no type errors
    Failure Indicators: Non-zero exit code, type error messages
    Evidence: .sisyphus/evidence/task-3-typecheck.txt

  Scenario: Create team shows error on failure
    Tool: Playwright
    Preconditions: Studio UI running, NO dev user seeded (to trigger error)
    Steps:
      1. Navigate to http://localhost:4527/settings/team
      2. Click button with text "+ Create New Team"
      3. Fill input[label="Team Name"] with "Error Test Team"
      4. Click button with text "Create Team"
      5. Wait 2s for API response
      6. Assert: element with class "text-error" is visible
    Expected Result: Error message displayed to user (not just console.error)
    Failure Indicators: No visible error, team silently fails
    Evidence: .sisyphus/evidence/task-3-error-display.png
  ```

  **Commit**: YES (groups with Tasks 1, 2)
  - Message: `fix(infra): add output volume mount, seed dev user, fix teams page URLs`
  - Files: `frontend/studio-ui/app/settings/team/page.tsx`
  - Pre-commit: `cd frontend/studio-ui && npm run type-check`

- [ ] 4. File browser API endpoint on orchestrator

  **What to do**:
  - Create `services/docker-orchestrator/app/api/routes/filesystem.py` with a single GET endpoint
  - Endpoint: `GET /api/filesystem/browse` with optional query param `path` (default: root of browseable area)
  - Add `FILESYSTEM_BROWSE_ROOT` setting to `services/docker-orchestrator/app/config.py` with default value matching `AGENT_OUTPUT_PATH` (i.e., `/var/laias/outputs`) and validator ensuring absolute path
  - The file browser browses the SAME named volume already mounted at `/var/laias/outputs` (from Task 1). NO additional bind mount is needed — the `agent_outputs` named volume is already read-write on the orchestrator container, so both browsing and mkdir work.
  - Do NOT add a separate `:ro` bind mount — that would conflict with mkdir. The named volume at `/var/laias/outputs` is the single source of truth for both output storage and browsing.
  - Response model: `FileBrowserResponse` with fields: `current_path: str`, `parent_path: str | None`, `entries: List[FileBrowserEntry]` where `FileBrowserEntry` has `name: str`, `path: str`, `type: Literal["directory"]`, `children_count: int`
  - ONLY return directories (not files) — this is for selecting an output DESTINATION path
  - Security: Resolve symlinks with `os.path.realpath()`, verify resolved path starts with browse root, reject `..` components, return 403 on traversal attempts
  - Support `POST /api/filesystem/mkdir` to create new directories under the browse root (user requirement: "I can create a new folder")
  - Register router in `services/docker-orchestrator/app/main.py`

  **Must NOT do**:
  - Do not return file entries (directories only)
  - Do not allow browsing outside the configured root
  - Do not allow deleting or modifying existing directories
  - Do not add recursive listing (one level at a time)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Security-critical endpoint requiring careful path validation, multiple edge cases
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3, 5, 6)
  - **Blocks**: Task 7
  - **Blocked By**: None

  **References**:

  **Pattern References**:
  - `services/docker-orchestrator/app/api/routes/outputs.py:1-14` — Router setup pattern: imports, `router = APIRouter(prefix="/api", tags=["..."])`, endpoint decorators
  - `services/docker-orchestrator/app/config.py:53-58` — Settings field pattern with validator: `AGENT_OUTPUT_PATH` field + `@validator("AGENT_OUTPUT_PATH")` for absolute path check
  - `services/docker-orchestrator/app/main.py` — Router registration pattern (import and include_router)

  **API/Type References**:
  - `services/docker-orchestrator/app/models/responses.py:40-59` — Pydantic response model pattern with Field descriptions

  **External References**:
  - Python `os.path.realpath()` — Resolves symlinks for path traversal prevention
  - Python `pathlib.Path.iterdir()` — Directory listing

  **WHY Each Reference Matters**:
  - `outputs.py:1-14`: Exact import pattern and router setup to follow for consistency
  - `config.py:53-58`: Shows how to add a new setting with validator — follow same pattern for FILESYSTEM_BROWSE_ROOT
  - `main.py`: Shows where to register the new router
  - `responses.py:40-59`: Shows Pydantic model pattern with Field descriptions for the response model

  **Acceptance Criteria**:
  - [ ] `GET /api/filesystem/browse` returns 200 with directory listing
  - [ ] `GET /api/filesystem/browse?path=/../etc` returns 403
  - [ ] `POST /api/filesystem/mkdir` with `{"path": "new-folder"}` creates directory and returns 201
  - [ ] Response only contains entries with `type: "directory"` (no files)
  - [ ] `ruff check app/api/routes/filesystem.py` passes

  **QA Scenarios**:

  ```
  Scenario: Browse root directory returns entries
    Tool: Bash (curl)
    Preconditions: Orchestrator running with FILESYSTEM_BROWSE_ROOT configured
    Steps:
      1. Run: curl -s http://localhost:4522/api/filesystem/browse | jq '.entries | length'
    Expected Result: Number ≥ 0 (may be 0 if empty, but response is valid JSON with entries array)
    Failure Indicators: HTTP 500, invalid JSON, missing "entries" field
    Evidence: .sisyphus/evidence/task-4-browse-root.txt

  Scenario: Path traversal is blocked
    Tool: Bash (curl)
    Preconditions: Orchestrator running
    Steps:
      1. Run: curl -s -o /dev/null -w "%{http_code}" "http://localhost:4522/api/filesystem/browse?path=/../etc/passwd"
      2. Run: curl -s -o /dev/null -w "%{http_code}" "http://localhost:4522/api/filesystem/browse?path=/../../"
      3. Run: curl -s -o /dev/null -w "%{http_code}" "http://localhost:4522/api/filesystem/browse?path=%2F..%2F..%2Fetc"
    Expected Result: All three return HTTP 403
    Failure Indicators: HTTP 200 or any status other than 403
    Evidence: .sisyphus/evidence/task-4-path-traversal-blocked.txt

  Scenario: Create new directory works
    Tool: Bash (curl)
    Preconditions: Orchestrator running
    Steps:
      1. Run: curl -s -X POST http://localhost:4522/api/filesystem/mkdir -H "Content-Type: application/json" -d '{"path": "test-new-folder-'$(date +%s)'"}'
      2. Parse response for created path
      3. Run: curl -s http://localhost:4522/api/filesystem/browse | jq '.entries[].name' to verify folder appears
    Expected Result: HTTP 201, folder appears in browse listing
    Failure Indicators: HTTP 500, folder not in listing
    Evidence: .sisyphus/evidence/task-4-mkdir.txt

  Scenario: Only directories returned (no files)
    Tool: Bash (curl + jq)
    Preconditions: Browse root contains both files and directories
    Steps:
      1. Run: docker-compose exec docker-orchestrator sh -c "touch /var/laias/outputs/test-file.txt && mkdir -p /var/laias/outputs/test-dir"
      2. Run: curl -s http://localhost:4522/api/filesystem/browse | jq '[.entries[] | select(.type != "directory")] | length'
    Expected Result: 0 (no non-directory entries)
    Failure Indicators: Any number > 0
    Evidence: .sisyphus/evidence/task-4-dirs-only.txt
  ```

  **Commit**: YES (groups with Tasks 5, 6)
  - Message: `feat(orchestrator): file browser API and format converter service`
  - Files: `services/docker-orchestrator/app/api/routes/filesystem.py`, `services/docker-orchestrator/app/config.py`, `services/docker-orchestrator/app/main.py`
  - Pre-commit: `cd services/docker-orchestrator && ruff check app/`

- [ ] 5. Output config types + Zod schema extensions in Studio UI

  **What to do**:
  - In `frontend/studio-ui/types/index.ts`, add new types:
    - `OutputFormat = 'markdown' | 'html'` (no PDF in v1)
    - `OutputDestinations = { postgres: boolean; files: boolean }`
    - `OutputConfig = { output_path: string; output_format: OutputFormat; output_destinations: OutputDestinations }`
    - `DEFAULT_OUTPUT_CONFIG: OutputConfig = { output_path: '', output_format: 'markdown', output_destinations: { postgres: true, files: true } }`
  - In `frontend/studio-ui/types/index.ts`, add `FileBrowserEntry` and `FileBrowserResponse` types for the file browser API response
  - In `frontend/studio-ui/store/builder-store.ts`:
    - Add `outputConfig: OutputConfig` to `BuilderState` interface
    - Add `setOutputConfig: (config: Partial<OutputConfig>) => void` action
    - Add initial value `outputConfig: DEFAULT_OUTPUT_CONFIG` to store
    - Add `outputConfig` to the `partialize` function so it persists in localStorage
    - Add selector `selectOutputConfig`
  - In `frontend/studio-ui/lib/api.ts`, add `browseFilesystem(path?: string): Promise<FileBrowserResponse>` and `createDirectory(path: string): Promise<{path: string}>` functions that call the orchestrator API (use `DOCKER_API_URL`)

  **Must NOT do**:
  - Do not add PDF to OutputFormat (deferred to v2)
  - Do not modify existing types — only add new ones
  - Do not change the existing formSchema zod object in create/page.tsx (output config is separate state, not part of the generation form)

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3, 4, 6)
  - **Blocks**: Tasks 7, 8, 9
  - **Blocked By**: None

  **References**:

  **Pattern References**:
  - `frontend/studio-ui/types/index.ts:46-56` — Type definition pattern: `export type X = ...` and `export interface X { ... }`
  - `frontend/studio-ui/types/index.ts:139-144` — Default constant pattern: `export const DEFAULT_X: Type = { ... }`
  - `frontend/studio-ui/store/builder-store.ts:23-65` — BuilderState interface pattern with state + actions
  - `frontend/studio-ui/store/builder-store.ts:196-203` — Persist partialize pattern showing which fields survive page reload
  - `frontend/studio-ui/store/builder-store.ts:210-216` — Selector pattern: `export const selectX = (state: BuilderState) => state.x`
  - `frontend/studio-ui/lib/api.ts:28-29` — API URL constants: `AGENT_API_URL` and `DOCKER_API_URL`
  - `frontend/studio-ui/lib/api.ts:46-65` — `handleResponse<T>` pattern for typed API calls

  **WHY Each Reference Matters**:
  - `types/index.ts:46-56`: Shows naming convention and export pattern for types
  - `types/index.ts:139-144`: Shows how to export default config objects
  - `builder-store.ts:23-65`: Shows exact interface structure to extend
  - `builder-store.ts:196-203`: Shows partialize — must add outputConfig here for persistence
  - `lib/api.ts:28-29`: Shows DOCKER_API_URL is already defined — use it for file browser calls

  **Acceptance Criteria**:
  - [ ] `OutputConfig`, `OutputFormat`, `OutputDestinations` types exported from `types/index.ts`
  - [ ] `DEFAULT_OUTPUT_CONFIG` constant exported from `types/index.ts`
  - [ ] `outputConfig` field exists in BuilderState with setter action
  - [ ] `browseFilesystem` and `createDirectory` functions exist in `lib/api.ts`
  - [ ] `cd frontend/studio-ui && npm run type-check` passes

  **QA Scenarios**:

  ```
  Scenario: Types compile without errors
    Tool: Bash (npm)
    Preconditions: Dependencies installed
    Steps:
      1. Run: cd frontend/studio-ui && npm run type-check
    Expected Result: Exit code 0
    Failure Indicators: Type errors mentioning OutputConfig, OutputFormat, or related types
    Evidence: .sisyphus/evidence/task-5-typecheck.txt

  Scenario: Store persists outputConfig
    Tool: Bash (grep)
    Preconditions: Store file edited
    Steps:
      1. Run: grep -A5 "partialize" frontend/studio-ui/store/builder-store.ts
    Expected Result: Output contains "outputConfig"
    Failure Indicators: "outputConfig" not found in partialize block
    Evidence: .sisyphus/evidence/task-5-store-persist.txt
  ```

  **Commit**: YES (groups with Tasks 4, 6)
  - Message: `feat(orchestrator): file browser API and format converter service`
  - Files: `frontend/studio-ui/types/index.ts`, `frontend/studio-ui/store/builder-store.ts`, `frontend/studio-ui/lib/api.ts`
  - Pre-commit: `cd frontend/studio-ui && npm run type-check`

- [ ] 6. Format converter service (markdown → HTML)

  **What to do**:
  - Add `mistune>=3.0.0` to `services/docker-orchestrator/requirements.txt`
  - Create `services/docker-orchestrator/app/services/format_converter.py`:
    - Class `FormatConverter` with method `convert(content: str, target_format: str) -> str`
    - Support `target_format="html"` using `mistune.html(content)` — wraps in minimal HTML document with inline CSS
    - Support `target_format="markdown"` as passthrough (return content as-is)
    - Raise `ValueError` for unsupported formats
    - Singleton pattern matching `get_output_persistence_service()` from `output_persistence.py`
  - Create `services/docker-orchestrator/app/api/routes/convert.py`:
    - Endpoint: `POST /api/convert` with request body `{"content": str, "format": str}`
    - Response: `{"converted": str, "format": str, "content_length": int}`
    - Register router in `main.py`
  - Create Pydantic request/response models in the route file (small enough to inline, following the `DeployProxyRequest` pattern from generate.py)

  **Must NOT do**:
  - Do not add WeasyPrint or any PDF library (deferred to v2)
  - Do not add custom CSS templates — use a single minimal built-in style
  - Do not add file I/O — this is a stateless conversion endpoint

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Requires understanding mistune API and building a clean service with proper error handling
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3, 4, 5)
  - **Blocks**: Task 12
  - **Blocked By**: None

  **References**:

  **Pattern References**:
  - `services/docker-orchestrator/app/services/output_persistence.py:302-309` — Singleton pattern: `_instance = None` + `get_service()` function
  - `services/docker-orchestrator/app/api/routes/outputs.py:1-14` — Router setup pattern
  - `services/agent-generator/app/api/routes/generate.py:228-236` — Inline Pydantic model pattern (DeployProxyRequest defined in route file)

  **External References**:
  - mistune 3.x docs: `import mistune; html = mistune.html(markdown_text)` — simple one-call API

  **WHY Each Reference Matters**:
  - `output_persistence.py:302-309`: Exact singleton pattern to follow for FormatConverter
  - `outputs.py:1-14`: Router setup pattern for the new convert route
  - `generate.py:228-236`: Shows it's acceptable to define small Pydantic models inline in route files

  **Acceptance Criteria**:
  - [ ] `mistune` in `requirements.txt`
  - [ ] `FormatConverter.convert("# Hello", "html")` returns string containing `<h1>Hello</h1>`
  - [ ] `POST /api/convert` endpoint registered and accessible
  - [ ] `ruff check app/services/format_converter.py app/api/routes/convert.py` passes

  **QA Scenarios**:

  ```
  Scenario: Markdown to HTML conversion
    Tool: Bash (curl)
    Preconditions: Orchestrator running with new endpoint
    Steps:
      1. Run: curl -s -X POST http://localhost:4522/api/convert -H "Content-Type: application/json" -d '{"content":"# Hello\\n\\nWorld **bold**","format":"html"}'
      2. Parse response JSON field "converted"
    Expected Result: Response contains "<h1>Hello</h1>" and "<strong>bold</strong>"
    Failure Indicators: HTTP 500, missing HTML tags, raw markdown in output
    Evidence: .sisyphus/evidence/task-6-html-conversion.txt

  Scenario: Markdown passthrough
    Tool: Bash (curl)
    Preconditions: Orchestrator running
    Steps:
      1. Run: curl -s -X POST http://localhost:4522/api/convert -H "Content-Type: application/json" -d '{"content":"# Hello","format":"markdown"}'
    Expected Result: Response "converted" field equals "# Hello"
    Failure Indicators: Content modified
    Evidence: .sisyphus/evidence/task-6-markdown-passthrough.txt

  Scenario: Unsupported format returns error
    Tool: Bash (curl)
    Preconditions: Orchestrator running
    Steps:
      1. Run: curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:4522/api/convert -H "Content-Type: application/json" -d '{"content":"test","format":"pdf"}'
    Expected Result: HTTP 400 or 422
    Failure Indicators: HTTP 200 or 500
    Evidence: .sisyphus/evidence/task-6-unsupported-format.txt
  ```

  **Commit**: YES (groups with Tasks 4, 5)
  - Message: `feat(orchestrator): file browser API and format converter service`
  - Files: `services/docker-orchestrator/requirements.txt`, `services/docker-orchestrator/app/services/format_converter.py`, `services/docker-orchestrator/app/api/routes/convert.py`, `services/docker-orchestrator/app/main.py`
  - Pre-commit: `cd services/docker-orchestrator && ruff check app/`

- [ ] 7. File browser tree component in Studio UI

  **What to do**:
  - Create `frontend/studio-ui/components/agent-builder/file-browser.tsx`:
    - Tree-view component that displays directories from the file browser API
    - Props: `onSelect: (path: string) => void`, `selectedPath: string`, `className?: string`
    - Uses `browseFilesystem()` from `lib/api.ts` to fetch directory listings
    - Renders as a collapsible tree with folder icons (use lucide-react `Folder`, `FolderOpen`, `ChevronRight` icons)
    - Clicking a directory selects it (calls `onSelect` with full path)
    - Clicking the expand chevron loads children (lazy loading — only fetch when expanded)
    - "New Folder" button at bottom that calls `createDirectory()` API and refreshes the tree
    - Loading state with spinner while fetching
    - Error state if API call fails
    - Follow the design system: `bg-surface`, `border-border`, `text-text-primary`, `text-text-secondary` classes
  - Export from `frontend/studio-ui/components/agent-builder/index.ts`

  **Must NOT do**:
  - Do not show files (directories only)
  - Do not implement drag-and-drop
  - Do not implement file preview or content viewing
  - Do not implement recursive pre-loading (lazy load one level at a time)
  - Do not use any external tree library — build with native React + Tailwind

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: UI component with tree interaction, expand/collapse, loading states
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: Tree-view component requires careful UX for expand/collapse, selection, loading states

  **Parallelization**:
  - **Can Run In Parallel**: NO (needs Task 4 API + Task 5 types)
  - **Parallel Group**: Wave 2 (with Tasks 8, 9, 10)
  - **Blocks**: Task 8
  - **Blocked By**: Tasks 4, 5

  **References**:

  **Pattern References**:
  - `frontend/studio-ui/components/agent-builder/tool-tile.tsx` — Component pattern: 'use client', React.FC, props interface, cn() for conditional classes
  - `frontend/studio-ui/components/agent-builder/section-panel.tsx:38` — useState for collapse/expand state
  - `frontend/studio-ui/components/agent-builder/index.ts` — Barrel export pattern

  **API/Type References**:
  - `frontend/studio-ui/types/index.ts` — `FileBrowserEntry` and `FileBrowserResponse` types (added in Task 5)
  - `frontend/studio-ui/lib/api.ts` — `browseFilesystem()` and `createDirectory()` functions (added in Task 5)

  **External References**:
  - lucide-react icons: `Folder`, `FolderOpen`, `ChevronRight`, `Plus`, `Loader2`

  **WHY Each Reference Matters**:
  - `tool-tile.tsx`: Shows exact component structure pattern used in agent-builder directory
  - `section-panel.tsx:38`: Shows useState pattern for expand/collapse — reuse for tree nodes
  - `index.ts`: Must add FileBrowser export here for other components to import

  **Acceptance Criteria**:
  - [ ] `FileBrowser` component exported from `components/agent-builder/index.ts`
  - [ ] Component renders directory tree from API response
  - [ ] Clicking a directory calls `onSelect` with the path
  - [ ] "New Folder" button creates directory via API
  - [ ] `cd frontend/studio-ui && npm run type-check` passes

  **QA Scenarios**:

  ```
  Scenario: File browser renders and shows directories
    Tool: Playwright
    Preconditions: Studio UI running, orchestrator running with file browser API
    Steps:
      1. Navigate to http://localhost:4527/create
      2. Scroll to Output Configuration section
      3. Click "Browse" button to open file browser
      4. Wait for directory listing to load (spinner disappears)
      5. Assert: at least one element with data-testid="file-browser-entry" is visible
      6. Assert: all entries show folder icon (no file icons)
    Expected Result: Directory tree renders with folder entries
    Failure Indicators: Spinner never disappears, no entries shown, error message displayed
    Evidence: .sisyphus/evidence/task-7-file-browser-renders.png

  Scenario: Selecting a directory updates selection
    Tool: Playwright
    Preconditions: File browser visible with entries
    Steps:
      1. Click first directory entry in the tree
      2. Assert: clicked entry has selected styling (e.g., bg-accent-cyan/10 or similar)
      3. Assert: parent component receives the selected path
    Expected Result: Directory is visually selected
    Failure Indicators: No visual change, onSelect not called
    Evidence: .sisyphus/evidence/task-7-directory-select.png

  Scenario: Create new folder works
    Tool: Playwright
    Preconditions: File browser visible
    Steps:
      1. Click "New Folder" button
      2. Enter folder name "test-folder" in the input that appears
      3. Click confirm/create button
      4. Wait for tree to refresh
      5. Assert: "test-folder" appears in the directory listing
    Expected Result: New folder created and visible in tree
    Failure Indicators: Error message, folder not appearing
    Evidence: .sisyphus/evidence/task-7-create-folder.png
  ```

  **Commit**: YES (groups with Task 8)
  - Message: `feat(studio-ui): output config panel with file browser tree`
  - Files: `frontend/studio-ui/components/agent-builder/file-browser.tsx`, `frontend/studio-ui/components/agent-builder/index.ts`
  - Pre-commit: `cd frontend/studio-ui && npm run type-check`

- [ ] 8. Output Configuration SectionPanel in Studio UI create page

  **What to do**:
  - Create `frontend/studio-ui/components/agent-builder/output-config-panel.tsx`:
    - New component `OutputConfigPanel` that wraps a `SectionPanel` with output configuration controls
    - Props: `outputConfig: OutputConfig`, `onConfigChange: (config: Partial<OutputConfig>) => void`, `disabled?: boolean`
    - Contains three sub-sections:
      1. **Output Path**: Text input showing selected path + "Browse" button that opens the `FileBrowser` component in a modal/dropdown. When user selects a path in FileBrowser, it populates the text input.
      2. **Output Format**: Radio group or Select with options: "Markdown" (default), "HTML"
      3. **Output Destinations**: Two checkboxes: "Save to Database" (postgres), "Save to Files" (files) — at least one must be checked
    - Use `SectionPanel` with `id="output-config"`, `title="Output Configuration"`, `accentColor="cyan"`, `description="Configure where and how agent outputs are saved"`
  - In `frontend/studio-ui/app/create/page.tsx`:
    - Import `OutputConfigPanel` from `@/components/agent-builder`
    - Import `selectOutputConfig` from store and `useBuilderStore` for `setOutputConfig`
    - Add `OutputConfigPanel` between the Tools section (line 699, end of `</div>` for tools-section) and Advanced Options section (line 702, start of `<SectionPanel id="advanced"`)
    - Pass `outputConfig` from store and `setOutputConfig` as handler
    - Add "Output" to the left nav section list (after Tools, icon "4", bump Advanced to "5")
  - Export from `frontend/studio-ui/components/agent-builder/index.ts`

  **Must NOT do**:
  - Do not add PDF option to format selector (v2)
  - Do not modify the existing form schema (output config is separate from generation form)
  - Do not add output config to the zod validation (it's optional — agent can run without it)
  - Do not use a native file input or OS file picker

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: UI component with multiple interactive controls, modal/dropdown, form integration
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: Complex form section with multiple control types and state management

  **Parallelization**:
  - **Can Run In Parallel**: NO (needs Task 5 types + Task 7 FileBrowser)
  - **Parallel Group**: Wave 2 (with Tasks 7, 9, 10)
  - **Blocks**: Task 11
  - **Blocked By**: Tasks 5, 7

  **References**:

  **Pattern References**:
  - `frontend/studio-ui/app/create/page.tsx:572-624` — SectionPanel usage pattern for "Agent Configuration" section with grid layout and Controller components
  - `frontend/studio-ui/app/create/page.tsx:627-699` — SectionPanel usage pattern for "Tools" section — this is the section BEFORE the new output config panel
  - `frontend/studio-ui/app/create/page.tsx:701-743` — SectionPanel usage pattern for "Advanced Options" — this is the section AFTER the new output config panel
  - `frontend/studio-ui/app/create/page.tsx:503-528` — Left nav section list — must add "Output" entry here
  - `frontend/studio-ui/components/agent-builder/section-panel.tsx` — SectionPanel component interface
  - `frontend/studio-ui/components/ui/input.tsx` — Input, Select components
  - `frontend/studio-ui/components/ui/checkbox.tsx` — Checkbox component

  **API/Type References**:
  - `frontend/studio-ui/types/index.ts` — `OutputConfig`, `OutputFormat`, `OutputDestinations`, `DEFAULT_OUTPUT_CONFIG` (added in Task 5)
  - `frontend/studio-ui/store/builder-store.ts` — `selectOutputConfig`, `setOutputConfig` (added in Task 5)

  **WHY Each Reference Matters**:
  - `create/page.tsx:627-699`: This is the EXACT insertion point — new panel goes after this closing `</div>`
  - `create/page.tsx:701-743`: This is what comes AFTER — verify the new panel doesn't break layout
  - `create/page.tsx:503-528`: Left nav must be updated to include the new section
  - `section-panel.tsx`: Must use exact same component with matching props

  **Acceptance Criteria**:
  - [ ] `OutputConfigPanel` component exported from `components/agent-builder/index.ts`
  - [ ] Output Configuration section visible in create page between Tools and Advanced Options
  - [ ] Path input + Browse button functional
  - [ ] Format selector shows Markdown and HTML options
  - [ ] Destination checkboxes for Database and Files
  - [ ] Left nav shows "Output" as section 4 (Advanced becomes 5)
  - [ ] `cd frontend/studio-ui && npm run build && npm run type-check` passes

  **QA Scenarios**:

  ```
  Scenario: Output config section renders in correct position
    Tool: Playwright
    Preconditions: Studio UI running
    Steps:
      1. Navigate to http://localhost:4527/create
      2. Scroll down past Tools section
      3. Assert: element with id="output-config" exists
      4. Assert: element with id="output-config" appears BEFORE element with id="advanced"
      5. Assert: element with id="output-config" appears AFTER element with id="tools"
      6. Screenshot the full form
    Expected Result: Output Configuration section visible between Tools and Advanced Options
    Failure Indicators: Section missing, wrong position, overlapping with other sections
    Evidence: .sisyphus/evidence/task-8-output-section-position.png

  Scenario: Format selector works
    Tool: Playwright
    Preconditions: Output config section visible
    Steps:
      1. Find the format selector within #output-config section
      2. Assert: "Markdown" is selected by default
      3. Select "HTML" option
      4. Assert: selection changed to HTML
    Expected Result: Format can be toggled between Markdown and HTML
    Failure Indicators: Selector not interactive, options missing
    Evidence: .sisyphus/evidence/task-8-format-selector.png

  Scenario: Destination checkboxes enforce at-least-one
    Tool: Playwright
    Preconditions: Output config section visible
    Steps:
      1. Assert: both "Save to Database" and "Save to Files" checkboxes are checked by default
      2. Uncheck "Save to Database"
      3. Assert: "Save to Files" remains checked
      4. Try to uncheck "Save to Files" (the last remaining checked box)
      5. Assert: at least one checkbox remains checked (either prevent uncheck or show validation error)
    Expected Result: Cannot uncheck both — at least one destination must be selected
    Failure Indicators: Both checkboxes unchecked simultaneously
    Evidence: .sisyphus/evidence/task-8-destination-validation.png

  Scenario: Left nav includes Output section
    Tool: Playwright
    Preconditions: Studio UI running on desktop viewport (lg breakpoint)
    Steps:
      1. Navigate to http://localhost:4527/create
      2. Assert: left nav contains items: Description (1), Type (2), Tools (3), Output (4), Advanced (5)
    Expected Result: 5 nav items in correct order
    Failure Indicators: Missing "Output" item, wrong numbering
    Evidence: .sisyphus/evidence/task-8-left-nav.png
  ```

  **Commit**: YES (groups with Task 7)
  - Message: `feat(studio-ui): output config panel with file browser tree`
  - Files: `frontend/studio-ui/components/agent-builder/output-config-panel.tsx`, `frontend/studio-ui/components/agent-builder/index.ts`, `frontend/studio-ui/app/create/page.tsx`
  - Pre-commit: `cd frontend/studio-ui && npm run build && npm run type-check`

- [ ] 9. Extend orchestrator deploy models with output_path + output_format

  **What to do**:
  - In `services/docker-orchestrator/app/models/requests.py`, add to `DeployAgentRequest`:
    - `output_path: Optional[str] = Field(default=None, description="User-chosen output directory path")` 
    - `output_format: str = Field(default="markdown", description="Output format: markdown or html")`
    - Add `@validator("output_format")` that validates value is in `{"markdown", "html"}`
    - Add `@validator("output_path")` that validates path is absolute if provided, and does NOT contain `..` components
  - In `services/docker-orchestrator/app/models/responses.py`, add to `DeploymentResponse`:
    - `output_path: Optional[str] = Field(default=None, description="Configured output path")`
    - `output_format: str = Field(default="markdown", description="Configured output format")`
  - In `services/docker-orchestrator/app/services/docker_service.py`, update `deploy_agent()`:
    - Add `output_path: Optional[str] = None` and `output_format: str = "markdown"` parameters
    - If `output_path` is provided, use it instead of the default `AGENT_OUTPUT_PATH/{deployment_id}` for the output directory
    - Add `LAIAS_OUTPUT_FORMAT` env var to the agent container's environment
    - Add `LAIAS_OUTPUT_PATH` env var with the user-chosen path (or default)

  **Must NOT do**:
  - Do not change the existing `output_config: Dict[str, bool]` field shape
  - Do not remove any existing fields or validators
  - Do not modify the container creation logic beyond adding new env vars and optional path override

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (only needs Task 5 types conceptually, but Python backend is independent)
  - **Parallel Group**: Wave 2 (with Tasks 7, 8, 10)
  - **Blocks**: Tasks 10, 12
  - **Blocked By**: Task 5 (conceptual alignment on field names)

  **References**:

  **Pattern References**:
  - `services/docker-orchestrator/app/models/requests.py:59-96` — Existing `output_config` field with `@validator` — add new fields following same pattern
  - `services/docker-orchestrator/app/models/requests.py:64-71` — `@validator("memory_limit")` pattern with regex validation
  - `services/docker-orchestrator/app/services/docker_service.py:107-128` — Deploy method parameter list and env var injection

  **API/Type References**:
  - `services/docker-orchestrator/app/models/responses.py:12-31` — `DeploymentResponse` model to extend

  **WHY Each Reference Matters**:
  - `requests.py:59-96`: Shows exact pattern for adding validated fields to DeployAgentRequest
  - `docker_service.py:107-128`: Shows where to add new parameters and env vars in deploy flow

  **Acceptance Criteria**:
  - [ ] `DeployAgentRequest` has `output_path` and `output_format` fields
  - [ ] `DeploymentResponse` has `output_path` and `output_format` fields
  - [ ] `deploy_agent()` accepts and uses `output_path` and `output_format`
  - [ ] `ruff check app/models/ app/services/docker_service.py` passes

  **QA Scenarios**:

  ```
  Scenario: Deploy with output_path and output_format
    Tool: Bash (curl)
    Preconditions: Orchestrator running
    Steps:
      1. Run: curl -s -X POST http://localhost:4522/api/deploy -H "Content-Type: application/json" -d '{"agent_id":"test-output-config","agent_name":"Test","flow_code":"print(1)","agents_yaml":"agents: []","output_path":"/var/laias/outputs/custom","output_format":"html","output_config":{"postgres":true,"files":true}}'
      2. Parse response JSON
    Expected Result: Response contains output_path="/var/laias/outputs/custom" and output_format="html"
    Failure Indicators: HTTP 422 (validation error) or missing fields in response
    Evidence: .sisyphus/evidence/task-9-deploy-with-output-config.txt

  Scenario: Invalid output_format rejected
    Tool: Bash (curl)
    Preconditions: Orchestrator running
    Steps:
      1. Run: curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:4522/api/deploy -H "Content-Type: application/json" -d '{"agent_id":"test","agent_name":"Test","flow_code":"print(1)","agents_yaml":"agents: []","output_format":"pdf"}'
    Expected Result: HTTP 422 (validation error)
    Failure Indicators: HTTP 200 or 201
    Evidence: .sisyphus/evidence/task-9-invalid-format.txt
  ```

  **Commit**: YES (groups with Tasks 10, 11, 12)
  - Message: `feat(deploy): output config through full deploy chain with format conversion`
  - Files: `services/docker-orchestrator/app/models/requests.py`, `services/docker-orchestrator/app/models/responses.py`, `services/docker-orchestrator/app/services/docker_service.py`
  - Pre-commit: `cd services/docker-orchestrator && ruff check app/`

- [ ] 10. Extend agent-generator proxy + orchestrator client with output fields

  **What to do**:
  - In `services/agent-generator/app/api/routes/generate.py`, update `DeployProxyRequest` (line 228-236):
    - Add `output_path: str | None = None`
    - Add `output_format: str = "markdown"`
    - Pass both to `get_orchestrator_client().deploy_agent()` call (line 251-260)
  - In `services/agent-generator/app/services/orchestrator_client.py`, update `deploy_agent()` method:
    - Add `output_path: str | None = None` and `output_format: str = "markdown"` parameters
    - Include them in the request payload sent to orchestrator
  - Also update `generate_and_deploy()` in `generate.py` (line 125-225) to accept and forward output config if provided in the generation request

  **Must NOT do**:
  - Do not change the GenerateAgentRequest model
  - Do not modify the code generation logic
  - Do not change the orchestrator client's error handling

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 7, 8 in Wave 2)
  - **Parallel Group**: Wave 2 (with Tasks 7, 8, 9)
  - **Blocks**: Task 11
  - **Blocked By**: Task 9

  **References**:

  **Pattern References**:
  - `services/agent-generator/app/api/routes/generate.py:228-236` — `DeployProxyRequest` model to extend
  - `services/agent-generator/app/api/routes/generate.py:250-260` — `deploy_agent()` call to update with new params
  - `services/agent-generator/app/services/orchestrator_client.py` — `deploy_agent()` method to extend

  **WHY Each Reference Matters**:
  - `generate.py:228-236`: Exact model to add fields to
  - `generate.py:250-260`: Exact call site where new fields must be forwarded
  - `orchestrator_client.py`: HTTP client that builds the request payload to orchestrator

  **Acceptance Criteria**:
  - [ ] `DeployProxyRequest` has `output_path` and `output_format` fields
  - [ ] `orchestrator_client.deploy_agent()` accepts and forwards `output_path` and `output_format`
  - [ ] `ruff check app/` passes for agent-generator

  **QA Scenarios**:

  ```
  Scenario: Deploy proxy forwards output config
    Tool: Bash (curl)
    Preconditions: Agent generator and orchestrator both running
    Steps:
      1. Run: curl -s -X POST http://localhost:4521/api/deploy -H "Content-Type: application/json" -d '{"agent_id":"proxy-test","agent_name":"Proxy Test","flow_code":"print(1)","agents_yaml":"agents: []","output_path":"/var/laias/outputs/proxy-test","output_format":"html"}'
      2. Parse response JSON
    Expected Result: Response contains output_path and output_format fields matching input
    Failure Indicators: HTTP 502 (orchestrator error), missing fields
    Evidence: .sisyphus/evidence/task-10-proxy-forwards.txt
  ```

  **Commit**: YES (groups with Tasks 9, 11, 12)
  - Message: `feat(deploy): output config through full deploy chain with format conversion`
  - Files: `services/agent-generator/app/api/routes/generate.py`, `services/agent-generator/app/services/orchestrator_client.py`
  - Pre-commit: `cd services/agent-generator && ruff check app/`

- [ ] 11. Wire Studio UI deploy flow with output config

  **What to do**:
  - In `frontend/studio-ui/lib/api.ts`, update `deployAgent()` function (line 198-228):
    - Add `output_config?: { postgres: boolean; files: boolean }` to options parameter
    - Add `output_path?: string` to options parameter
    - Add `output_format?: string` to options parameter
    - Include these in the request body sent to `AGENT_API_URL/api/deploy`
  - In `frontend/studio-ui/app/create/page.tsx`, update `handleDeploy()` function (line 368-406):
    - Read `outputConfig` from the builder store using `useBuilderStore`
    - Pass `output_config: outputConfig.output_destinations`, `output_path: outputConfig.output_path`, `output_format: outputConfig.output_format` to `studioApi.deployAgent()`
  - Update the `studioApi` export object to include any new functions

  **Must NOT do**:
  - Do not modify the generation flow (handleGenerate) — output config only affects deploy
  - Do not make output config required — deploy should work without it (uses defaults)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Requires understanding the full deploy chain and wiring store state to API calls
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 12 in Wave 3)
  - **Parallel Group**: Wave 3 (with Tasks 12, 13)
  - **Blocks**: Task 13
  - **Blocked By**: Tasks 8, 10

  **References**:

  **Pattern References**:
  - `frontend/studio-ui/lib/api.ts:198-228` — `deployAgent()` function to extend
  - `frontend/studio-ui/app/create/page.tsx:368-406` — `handleDeploy()` function to update
  - `frontend/studio-ui/app/create/page.tsx:71-85` — Store destructuring pattern at top of component

  **WHY Each Reference Matters**:
  - `api.ts:198-228`: Exact function to modify — must add new fields to request body
  - `create/page.tsx:368-406`: Exact handler where store state must be read and passed to API
  - `create/page.tsx:71-85`: Shows how to destructure store values — add outputConfig here

  **Acceptance Criteria**:
  - [ ] `deployAgent()` accepts and sends output_config, output_path, output_format
  - [ ] `handleDeploy()` reads outputConfig from store and passes to deployAgent
  - [ ] `cd frontend/studio-ui && npm run build && npm run type-check` passes

  **QA Scenarios**:

  ```
  Scenario: Deploy sends output config in request body
    Tool: Playwright (with network interception)
    Preconditions: Studio UI running, agent generated
    Steps:
      1. Navigate to http://localhost:4527/create
      2. Fill description with "Test agent for output config"
      3. Scroll to Output Configuration section
      4. Select output format "HTML"
      5. Uncheck "Save to Database" (leave "Save to Files" checked)
      6. Click "Generate Agent" and wait for completion
      7. Intercept network request to /api/deploy
      8. Click "Deploy" button
      9. Assert: intercepted request body contains output_format: "html"
      10. Assert: intercepted request body contains output_config.postgres: false
      11. Assert: intercepted request body contains output_config.files: true
    Expected Result: Deploy request includes all output configuration fields
    Failure Indicators: Missing fields in request body, default values sent instead of user selections
    Evidence: .sisyphus/evidence/task-11-deploy-request.png
  ```

  **Commit**: YES (groups with Tasks 9, 10, 12)
  - Message: `feat(deploy): output config through full deploy chain with format conversion`
  - Files: `frontend/studio-ui/lib/api.ts`, `frontend/studio-ui/app/create/page.tsx`
  - Pre-commit: `cd frontend/studio-ui && npm run build && npm run type-check`

- [ ] 12. Conversion endpoint + post-run hook

  **What to do**:
  - In `services/docker-orchestrator/app/services/output_persistence.py`, update `_write_files()` method:
    - After writing `summary.md`, check if the deployment's `output_format` is not "markdown"
    - If format is "html", use `FormatConverter` to convert the summary markdown to HTML and write `summary.html` alongside `summary.md`
    - The `output_format` should be passed through the event payload or looked up from container labels
  - In `services/docker-orchestrator/app/api/routes/outputs.py`, update `ingest_output_event()`:
    - When event_type is "run_completed", trigger format conversion for the run's summary if output_format != "markdown"
  - Add `output_format` to the container labels in `docker_service.py` so it can be looked up later

  **Must NOT do**:
  - Do not convert events.jsonl or metrics.json — only convert summary.md
  - Do not add async background workers — conversion is fast enough to do inline
  - Do not modify the agent runner or how agents produce output

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Requires understanding the event flow and integrating conversion at the right point
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 11 in Wave 3)
  - **Parallel Group**: Wave 3 (with Tasks 11, 13)
  - **Blocks**: Task 13
  - **Blocked By**: Tasks 6, 9

  **References**:

  **Pattern References**:
  - `services/docker-orchestrator/app/services/output_persistence.py:168-221` — `_write_files()` method where conversion should be added
  - `services/docker-orchestrator/app/services/output_persistence.py:197-199` — Where `run_completed` events trigger metrics write — add conversion here
  - `services/docker-orchestrator/app/services/docker_service.py:149-156` — Container labels — add `output_format` label here

  **WHY Each Reference Matters**:
  - `output_persistence.py:168-221`: Exact method where file writing happens — conversion goes after summary.md write
  - `output_persistence.py:197-199`: Shows the `run_completed` event check pattern — conversion triggers on same event
  - `docker_service.py:149-156`: Container labels are used to store deployment metadata — add output_format here

  **Acceptance Criteria**:
  - [ ] When output_format is "html", summary.html is written alongside summary.md
  - [ ] Container labels include `output_format`
  - [ ] `ruff check app/` passes

  **QA Scenarios**:

  ```
  Scenario: HTML summary generated on run_completed event
    Tool: Bash (curl + docker exec)
    Preconditions: Orchestrator running with format converter
    Steps:
      1. Deploy an agent with output_format="html": curl -s -X POST http://localhost:4522/api/deploy -H "Content-Type: application/json" -d '{"agent_id":"fmt-test","agent_name":"Format Test","flow_code":"print(1)","agents_yaml":"agents: []","output_format":"html","output_config":{"postgres":true,"files":true}}'
      2. Get deployment_id from response
      3. Send run_completed event: curl -s -X POST http://localhost:4522/api/deployments/{deployment_id}/outputs/events -H "Content-Type: application/json" -d '{"run_id":"run-fmt-test","event_type":"run_completed","message":"Run completed","payload":{"tokens_used":100}}'
      4. Check for summary.html: docker-compose exec docker-orchestrator ls /var/laias/outputs/{deployment_id}/run-fmt-test/
    Expected Result: Both summary.md and summary.html exist in the run directory
    Failure Indicators: Only summary.md exists, summary.html missing
    Evidence: .sisyphus/evidence/task-12-html-summary.txt
  ```

  **Commit**: YES (groups with Tasks 9, 10, 11)
  - Message: `feat(deploy): output config through full deploy chain with format conversion`
  - Files: `services/docker-orchestrator/app/services/output_persistence.py`, `services/docker-orchestrator/app/services/docker_service.py`
  - Pre-commit: `cd services/docker-orchestrator && ruff check app/`

- [ ] 13. Docker rebuild + integration smoke test

  **What to do**:
  - Rebuild ALL Docker services: `docker-compose up -d --build`
  - Wait for all health checks to pass
  - Run integration smoke tests:
    1. Verify volume mount: `docker volume ls | grep laias-agent-outputs`
    2. Verify dev user: `docker exec laias-postgres psql -U laias -d laias -c "SELECT id FROM users WHERE id='00000000-0000-0000-0000-000000000000';"`
    3. Verify file browser API: `curl -s http://localhost:4522/api/filesystem/browse | jq '.entries'`
    4. Verify convert API: `curl -s -X POST http://localhost:4522/api/convert -H "Content-Type: application/json" -d '{"content":"# Test","format":"html"}' | jq '.converted'`
    5. Verify teams create: `curl -s -X POST http://localhost:4521/api/teams -H "Content-Type: application/json" -H "X-User-Id: 00000000-0000-0000-0000-000000000000" -d '{"name":"Integration Test Team"}' | jq '.id'`
    6. Verify Studio UI builds: check http://localhost:4527 loads
    7. Verify output persistence: deploy test agent, send event, restart orchestrator, verify data persists

  **Must NOT do**:
  - Do not modify any source code in this task
  - Do not skip any smoke test — all must pass

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO (depends on all previous tasks)
  - **Parallel Group**: Wave 3 (sequential after Tasks 11, 12)
  - **Blocks**: Task 14
  - **Blocked By**: Tasks 1, 11, 12

  **References**:
  - All previous task QA scenarios serve as the smoke test checklist

  **Acceptance Criteria**:
  - [ ] All 4 Docker services healthy (agent-generator, docker-orchestrator, studio-ui, control-room)
  - [ ] All 7 smoke tests pass
  - [ ] No container restart loops

  **QA Scenarios**:

  ```
  Scenario: Full integration smoke test
    Tool: Bash (docker + curl)
    Preconditions: docker-compose up -d --build completed
    Steps:
      1. Run: docker-compose ps --format "{{.Name}} {{.Status}}" | grep -c "healthy"
      2. Assert: count is 4 (all services healthy)
      3. Run all 7 smoke test commands listed above
      4. Assert: all return expected results
    Expected Result: All services healthy, all smoke tests pass
    Failure Indicators: Any service unhealthy, any smoke test fails
    Evidence: .sisyphus/evidence/task-13-integration-smoke.txt
  ```

  **Commit**: YES
  - Message: `chore(docker): rebuild all services and verify integration`
  - Files: none (rebuild only)
  - Pre-commit: none

- [ ] 14. Control Room rebuild + output panel verify

  **What to do**:
  - Rebuild control-room: `docker-compose up -d --build control-room`
  - Verify the existing `OutputArtifactsPanel` component works with the new volume-backed output data
  - Verify that output runs are visible in the Control Room container detail page
  - The OutputArtifactsPanel was built in a previous session but the control-room container was never rebuilt — this task ensures it's live

  **Must NOT do**:
  - Do not modify the OutputArtifactsPanel component
  - Do not modify the Control Room API client or types

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4 (after Task 13)
  - **Blocks**: F1-F4
  - **Blocked By**: Tasks 1, 13

  **References**:
  - `frontend/control-room/components/containers/output-artifacts-panel.tsx` — Existing component to verify
  - `frontend/control-room/lib/api.ts` — `getDeploymentOutputRuns()` and `getDeploymentOutputRunDetail()` functions

  **Acceptance Criteria**:
  - [ ] Control Room container is healthy
  - [ ] `npm run build && npm run type-check` passes for control-room
  - [ ] Output panel renders in container detail page

  **QA Scenarios**:

  ```
  Scenario: Control Room loads and shows output panel
    Tool: Playwright
    Preconditions: Control Room rebuilt and running, at least one deployment with output data
    Steps:
      1. Navigate to http://localhost:4528
      2. Click on a container card to open detail view
      3. Scroll to Output Artifacts section
      4. Assert: OutputArtifactsPanel component is visible
      5. If runs exist: assert run list is populated
    Expected Result: Output panel renders without errors
    Failure Indicators: Component not visible, JavaScript errors in console
    Evidence: .sisyphus/evidence/task-14-control-room-output.png
  ```

  **Commit**: NO (rebuild only, no code changes)

---

## Final Verification Wave

> 4 review agents run in PARALLEL. ALL must APPROVE. Rejection → fix → re-run.

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, curl endpoint, run command). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in .sisyphus/evidence/. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `tsc --noEmit` in both frontends + `ruff check app/ tests/` in both Python services + `pytest -v` in both Python services. Review all changed files for: `as any`/`@ts-ignore`, empty catches, console.log in prod, commented-out code, unused imports. Check AI slop: excessive comments, over-abstraction, generic names (data/result/item/temp). Verify no hardcoded URLs in frontend.
  Output: `Build [PASS/FAIL] | Lint [PASS/FAIL] | Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Real Manual QA** — `unspecified-high` (+ `playwright` skill for UI, + `dev-browser` skill)
  Start from clean state. Execute EVERY QA scenario from EVERY task — follow exact steps, capture evidence. Test cross-task integration: create team → configure output → deploy agent → verify output persists. Test edge cases: empty state, invalid paths, path traversal, rapid clicks. Save to `.sisyphus/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff (git log/diff). Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance. Detect cross-task contamination: Task N touching Task M's files. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **Commit A** (after Tasks 1-3): `fix(infra): add output volume mount, seed dev user, fix teams page URLs`
  - Files: `docker-compose.yml`, `infrastructure/init.sql`, `frontend/studio-ui/app/settings/team/page.tsx`
  - Pre-commit: `cd frontend/studio-ui && npm run type-check`

- **Commit B** (after Tasks 4-6): `feat(orchestrator): file browser API and format converter service`
  - Files: `services/docker-orchestrator/app/api/routes/filesystem.py`, `services/docker-orchestrator/app/services/format_converter.py`, `services/docker-orchestrator/app/api/routes/convert.py`, `services/docker-orchestrator/app/main.py`
  - Pre-commit: `cd services/docker-orchestrator && ruff check app/`

- **Commit C** (after Tasks 7-8): `feat(studio-ui): output config panel with file browser tree`
  - Files: `frontend/studio-ui/components/agent-builder/output-config-panel.tsx`, `frontend/studio-ui/components/agent-builder/file-browser.tsx`, `frontend/studio-ui/components/agent-builder/index.ts`, `frontend/studio-ui/app/create/page.tsx`, `frontend/studio-ui/types/index.ts`, `frontend/studio-ui/store/builder-store.ts`
  - Pre-commit: `cd frontend/studio-ui && npm run build && npm run type-check`

- **Commit D** (after Tasks 9-12): `feat(deploy): output config through full deploy chain with format conversion`
  - Files: `services/docker-orchestrator/app/models/requests.py`, `services/docker-orchestrator/app/models/responses.py`, `services/docker-orchestrator/app/services/docker_service.py`, `services/agent-generator/app/api/routes/generate.py`, `services/agent-generator/app/services/orchestrator_client.py`, `frontend/studio-ui/lib/api.ts`
  - Pre-commit: `cd services/docker-orchestrator && ruff check app/ && pytest -v`

- **Commit E** (after Tasks 13-14): `chore(docker): rebuild all services and verify integration`
  - Files: none (rebuild only)
  - Pre-commit: `docker-compose up -d --build`

---

## Success Criteria

### Verification Commands
```bash
# Volume persistence
docker-compose restart docker-orchestrator
docker exec laias-docker-orchestrator ls /var/laias/outputs  # Expected: directory exists

# Teams fix
curl -s -X POST http://localhost:4521/api/teams \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 00000000-0000-0000-0000-000000000000" \
  -d '{"name":"Test Team"}' | jq '.id'  # Expected: UUID string

# File browser API
curl -s http://localhost:4522/api/filesystem/browse | jq '.entries | length'  # Expected: > 0
curl -s -o /dev/null -w "%{http_code}" "http://localhost:4522/api/filesystem/browse?path=/../etc/passwd"  # Expected: 403

# Format conversion
curl -s -X POST http://localhost:4522/api/convert \
  -H "Content-Type: application/json" \
  -d '{"content":"# Hello\n\nWorld","format":"html"}' | jq '.converted'  # Expected: contains <h1>

# Frontend builds
cd frontend/studio-ui && npm run build && npm run type-check  # Expected: 0 exit code
cd frontend/control-room && npm run build && npm run type-check  # Expected: 0 exit code

# Python lint
cd services/docker-orchestrator && ruff check app/  # Expected: 0 exit code
cd services/agent-generator && ruff check app/  # Expected: 0 exit code
```

### Final Checklist
- [ ] All "Must Have" items present and verified
- [ ] All "Must NOT Have" items absent (grep confirms)
- [ ] All tests pass
- [ ] No hardcoded URLs in frontend code
- [ ] No `as any` or `@ts-ignore` in new code
- [ ] Output config visible in Studio UI create page
- [ ] Teams create button works end-to-end
- [ ] Outputs persist across container restarts
