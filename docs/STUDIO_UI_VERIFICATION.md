# LAIAS Studio UI - Verification Checklist

**Author:** FLOYD v4.0.0
**Date:** 2026-02-24
**Status:** IN PROGRESS

---

## What This Document Is

This document enables programmatic verification of the Studio UI.
Every UI feature must have a corresponding API endpoint that can be tested without a browser.

---

## API Verification Matrix

### Agent Generator API (Port 4521)

| Feature | Endpoint | Method | Status | Notes |
|---------|----------|--------|--------|-------|
| Health Check | `/health` | GET | ✅ WORKING | |
| Generate Agent | `/api/generate-agent` | POST | ✅ WORKING | Needs all required fields |
| List Agents | `/api/agents` | GET | ✅ WORKING | |
| Get Agent | `/api/agents/{id}` | GET | ? | Not tested |
| Update Agent | `/api/agents/{id}` | PUT | ? | Not tested |
| Delete Agent | `/api/agents/{id}` | DELETE | ? | Not tested |
| Regenerate | `/api/regenerate` | POST | ? | Not tested |
| Validate Code | `/api/validate-code` | POST | ✅ WORKING | |
| Validation Rules | `/api/validation-rules` | GET | ✅ WORKING | |
| List Templates | `/api/templates` | GET | ✅ WORKING | |

### Docker Orchestrator API (Port 4522)

| Feature | Endpoint | Method | Status | Notes |
|---------|----------|--------|--------|-------|
| Health Check | `/health` | GET | ✅ WORKING | |
| List Containers | `/api/containers` | GET | ✅ WORKING | Fixed Pydantic v2 compatibility |
| Deploy Agent | `/api/deploy` | POST | ✅ WORKING | Requires: agent_id, agent_name, flow_code, agents_yaml |
| Get Container Logs | `/api/containers/{id}/logs` | GET | ? | Not tested |
| Stop Container | `/api/containers/{id}/stop` | POST | ? | Not tested |

---

## Test Commands

```bash
# Agent Generator Health
curl http://localhost:4521/health

# Generate Agent (minimal)
curl -X POST http://localhost:4521/api/generate-agent \
  -H 'Content-Type: application/json' \
  -d '{"description":"A greeter","agent_name":"Greeter","complexity":"simple","task_type":"general"}'

# List Agents
curl http://localhost:4521/api/agents

# Docker Orchestrator Health
curl http://localhost:4522/health

# List Containers (currently broken)
curl http://localhost:4522/api/containers
```

---

## Known Issues

| Issue | Severity | Status | Details |
|-------|----------|--------|---------|
| `/api/containers` 500 error | HIGH | ✅ FIXED | Pydantic v2 model syntax updated |
| Deploy validation 422 | MEDIUM | ✅ FIXED | Documented required fields, tested working |
| Studio UI ports hardcoded | LOW | ✅ FIXED | Updated to 4527/4528/4521/4522 |

---

## Studio UI Pages

| Page | URL | API Dependencies | Status |
|------|-----|------------------|--------|
| Home | `/` | healthCheck | ? |
| Create Agent | `/create` | generateAgent, validateCode, listTemplates | ? |
| Agent List | `/agents` | listAgents | ? |
| Templates | `/templates` | listTemplates | ? |
| Settings | `/settings` | None? | ? |

---

## Next Steps

1. Fix `/api/containers` 500 error
2. Test and document deploy endpoint
3. Verify each Studio UI page loads
4. Add missing API endpoints for any UI features without them
