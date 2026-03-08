# LAIAS Happy Path - From Cold Start to Working

**Author:** FLOYD v4.0.0
**Date:** 2026-02-24

---

## What Changed Today

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  BEFORE (BROKEN)                          AFTER (WORKING)                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PORTS:                                   PORTS:                             │
│  • Studio UI: 3000 (conflict)            • Studio UI: 4527 ✓                │
│  • Control Room: 3001 (conflict)         • Control Room: 4528 ✓             │
│  • Agent Generator: 8001                 • Agent Generator: 4521 ✓          │
│  • Docker Orchestrator: 8002             • Docker Orchestrator: 4522 ✓       │
│                                                                              │
│  ZAI API:                                 ZAI API:                           │
│  • Endpoint: /api/coding/paas/v4 (wrong) • Endpoint: /api/paas/v4 ✓         │
│  • Model: glm-5 (low concurrency)        • Model: GLM-4-Plus (worker) ✓     │
│  • thinking: not disabled (double layer!) • thinking: disabled ✓             │
│                                                                              │
│  DOCKER ORCHESTRATOR:                     DOCKER ORCHESTRATOR:               │
│  • /api/containers → 500 error           • /api/containers → 200 ✓          │
│  • Pydantic v1 syntax                    • Pydantic v2 syntax ✓             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Files Modified

| File | Change |
|------|--------|
| `docker-compose.yml` | Ports changed from 3000/3001/8001/8002 to 4527/4528/4521/4522 |
| `services/agent-generator/app/services/llm_provider.py` | ZAI endpoint and model fixed |
| `services/agent-generator/app/services/llm_service.py` | Default model mapping updated |
| `services/docker-orchestrator/app/models/responses.py` | Pydantic v2 syntax fix |

---

## Happy Path: Cold Start to Working

### Step 1: Start Docker

```bash
cd /Volumes/Storage/LAIAS && docker compose up -d
```

Wait for all services to show `(healthy)`:
```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### Step 2: Verify Services

```bash
# Agent Generator
curl http://localhost:4521/health

# Docker Orchestrator
curl http://localhost:4522/health
```

Both should return `{"status": "healthy", ...}`

### Step 3: Generate an Agent

```bash
curl -X POST http://localhost:4521/api/generate-agent \
  -H 'Content-Type: application/json' \
  -d '{
    "description": "A marketing team for Legacy AI",
    "agent_name": "MarketingTeam",
    "complexity": "moderate",
    "task_type": "automation",
    "llm_provider": "openai"
  }'
```

### Step 4: Deploy the Agent

```bash
curl -X POST http://localhost:4522/api/deploy \
  -H 'Content-Type: application/json' \
  -d '{
    "agent_id": "gen_...",
    "agent_name": "MarketingTeam",
    "flow_code": "...",
    "agents_yaml": "marketing:\n  role: Creator"
  }'
```

### Step 5: View in UI

- Studio UI: http://localhost:4527
- Control Room: http://localhost:4528

---

## Key Documentation

| Doc | Purpose |
|-----|---------|
| `LAIAS_PORTS.md` | Port assignments (memorize 4527, 4528, 4521, 4522) |
| `ZAI_API_VERIFIED.md` | ZAI API configuration that works |
| `STUDIO_UI_VERIFICATION.md` | API endpoint status matrix |
| `STUDIO_UI_TODO.md` | Remaining tasks |
| `LAIAS_COLD_START_GUIDE.md` | Full operational guide |

---

## Gotchas to Avoid

1. **Port 3000/3001** - Don't use these. Other projects use them.
2. **ZAI thinking mode on GLM-5 = CATASTROPHIC** - GLM-5 already has a reasoning layer
   injected at the ZAI endpoint. Enabling thinking mode adds a **second reasoning layer**
   that overwhelms the model into total paralysis — it produces empty/unusable output 100%
   of the time. Always set `"thinking": {"type": "disabled"}`.
3. **GLM-4-Plus is worker-only** - Lacks reasoning depth to be a primary builder or
   orchestrator. The 20 concurrent limit is **plan-wide** — using all 20 starves GLM-5
   and any other sessions on the same ZAI plan. Never run more than 3–5 workers per
   session. Each must be headless, single-task, and isolated to avoid race conditions.
   For orchestration/building, use GLM-5 (thinking disabled) or external providers.
4. **ZAI endpoint** - Use `/api/paas/v4` — NOT `/api/coding/paas/v4`.
5. **Rate limits** - Don't hammer the API or you'll block other projects.

See `ZAI_API_VERIFIED.md` for the full model capability matrix.

---

## Quick Reference

```
Studio UI:        http://localhost:4527
Control Room:     http://localhost:4528
Agent Generator:  http://localhost:4521/health
Docker Orch:      http://localhost:4522/health
```

```
# Start
cd /Volumes/Storage/LAIAS && docker compose up -d

# Stop
docker compose down

# Logs
docker logs laias-agent-generator --tail 50
```
