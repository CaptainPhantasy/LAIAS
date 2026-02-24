# LAIAS Port Assignments

**Locked:** 2026-02-24
**Author:** FLOYD v4.0.0

---

## Official Port Assignments

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAIAS PORT ALLOCATION - DO NOT CHANGE                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  SERVICE              PORT    PURPOSE                                       │
│  ────────────────────────────────────────────────────────────────────────   │
│  Studio UI             4527    Agent builder chat interface                 │
│  Control Room          4528    Monitoring dashboard                         │
│  Agent Generator       4521    Backend API for code generation              │
│  Docker Orchestrator   4522    Container deployment service                 │
│  PostgreSQL            5432    Database (standard port)                     │
│  Redis                 6379    Cache/queue (standard port)                  │
│                                                                              │
│  WHY THESE PORTS:                                                           │
│  - 3000/3001/5173 are too common (used by every other dev project)         │
│  - 45xx range is obscure and unlikely to conflict                          │
│  - Numbered sequentially for easy recall                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## URLs

| Service | URL |
|---------|-----|
| Studio UI | http://localhost:4527 |
| Control Room | http://localhost:4528 |
| Agent Generator API | http://localhost:4521 |
| Agent Generator Health | http://localhost:4521/health |
| Docker Orchestrator API | http://localhost:4522 |
| Docker Orchestrator Health | http://localhost:4522/health |

---

## Quick Commands

```bash
# Start all services
cd /Volumes/Storage/LAIAS && docker compose up -d

# Check status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Stop all services
docker compose down

# View logs
docker logs laias-agent-generator --tail 50
```

---

## Files Modified

- `/Volumes/Storage/LAIAS/docker-compose.yml` - Port mappings
