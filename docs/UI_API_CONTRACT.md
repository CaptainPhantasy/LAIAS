# UI-API Contract

**Author:** FLOYD v4.0.0
**Date:** 2026-02-24
**Version:** 1.0.0

---

## Studio UI Pages

| Page | Path | Status |
|------|------|--------|
| Home | `/app/page.tsx` | ✅ Inventoried |
| Create Agent | `/app/create/page.tsx` | ✅ Inventoried |
| Agents List | `/app/agents/page.tsx` | ✅ Inventoried |
| Templates | `/app/templates/page.tsx` | ✅ Inventoried |
| Settings | `/app/settings/page.tsx` | ✅ Inventoried |
| Team Settings | `/app/settings/team/page.tsx` | ✅ Inventoried |

## Control Room Pages

| Page | Path | Status |
|------|------|--------|
| Dashboard | `/app/page.tsx` | ✅ Inventoried |
| Container List | `/app/containers/page.tsx` | ✅ Inventoried |
| Container Detail | `/app/containers/[id]/page.tsx` | ✅ Inventoried |
| Container Logs | `/app/containers/[id]/logs/page.tsx` | ✅ Inventoried |
| Metrics | `/app/metrics/page.tsx` | ✅ Inventoried |

---

## API Endpoints

### Agent Generator (Port 4521)

| UI Element | Page | Endpoint | Method | Verified |
|------------|------|----------|--------|----------|
| Generate Button | /create | /api/generate-agent | POST | ✅ Yes |
| Validate Code | /create | /api/validate-code | POST | ✅ Yes |
| List Templates | /create, /templates | /api/templates | GET | ✅ Yes |
| List Agents | /agents | /api/agents | GET | ✅ Yes |
| Get Agent | /agents | /api/agents/{id} | GET | Pending |
| Delete Agent | /agents | /api/agents/{id} | DELETE | Pending |

### Docker Orchestrator (Port 4522)

| UI Element | Page | Endpoint | Method | Verified |
|------------|------|----------|--------|----------|
| Deploy Button | /create | /api/deploy | POST | ✅ Yes |
| List Containers | /containers | /api/containers | GET | ✅ Yes |
| Get Container | /containers/[id] | /api/containers/{id} | GET | Pending |
| Start Container | /containers/[id] | /api/containers/{id}/start | POST | Pending |
| Stop Container | /containers/[id] | /api/containers/{id}/stop | POST | Pending |
| Container Logs | /containers/[id]/logs | /api/containers/{id}/logs | GET | Pending |

---

## Form Fields (Create Page)

| Field | Type | Options | Required |
|-------|------|---------|----------|
| description | string | - | Yes (min 10 chars) |
| agent_name | string | - | No (auto-generated) |
| complexity | enum | simple, moderate, complex | Yes |
| task_type | enum | research, development, automation, analysis, general | Yes |
| max_agents | number | 1-10 | Yes |
| tools_requested | array | - | No |
| provider | enum | zai, openai, anthropic, openrouter | Yes |
| model | string | - | No |

---

## Verification Log

(Entries added as each item is verified)
