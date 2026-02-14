# LAIAS Frontend Architecture

## Overview

The LAIAS frontend consists of two independent Next.js applications that can be developed in parallel by separate teams.

```
frontend/
├── shared/              # Shared types and utilities (DO NOT MODIFY directly)
│   ├── types/
│   │   ├── agent-generator.ts      # Auto-generated from OpenAPI
│   │   ├── docker-orchestrator.ts  # Auto-generated from OpenAPI
│   │   └── index.ts                # Re-exports and utilities
│   └── lib/
│       └── api-client.ts           # Base API client
│
├── studio-ui/           # Agent Builder Interface (Port 3000)
│   ├── app/             # Next.js pages
│   ├── components/      # React components
│   ├── hooks/           # Custom hooks
│   ├── lib/             # Utilities
│   │   └── api.ts       # Studio-specific API client ✓ PROVIDED
│   ├── types/
│   │   └── index.ts     # Studio-specific types ✓ PROVIDED
│   ├── store/           # State management
│   └── SCAFFOLDING.md   # Team guide ✓ PROVIDED
│
└── control-room/        # Container Dashboard (Port 3001)
    ├── app/             # Next.js pages
    ├── components/      # React components
    ├── hooks/           # Custom hooks
    ├── lib/             # Utilities
    │   └── api.ts       # Control Room-specific API client ✓ PROVIDED
    ├── types/
    │   └── index.ts     # Control Room-specific types ✓ PROVIDED
    ├── store/           # State management
    └── SCAFFOLDING.md   # Team guide ✓ PROVIDED
```

## Team Separation

### Studio UI Team (Port 3000)

**Focus:** Agent creation workflow

| Responsibility | Files |
|---------------|-------|
| Agent builder form | `components/agent-builder/` |
| Code editor (Monaco) | `components/code-editor/` |
| Validation UI | `components/code-editor/validation-panel.tsx` |
| Agent list/management | `components/agents/` |
| Page routing | `app/create/`, `app/agents/` |

**API Endpoints:**
- Agent Generator API: `http://localhost:8001`
- Deploy endpoint: `http://localhost:8002/api/deploy`

### Control Room Team (Port 3001)

**Focus:** Container monitoring and operations

| Responsibility | Files |
|---------------|-------|
| Container cards/grid | `components/containers/` |
| Log viewer | `components/logs/` |
| Metrics charts | `components/metrics/` |
| Dashboard KPIs | `components/dashboard/` |
| Page routing | `app/containers/`, `app/logs/`, `app/metrics/` |

**API Endpoints:**
- Docker Orchestrator API: `http://localhost:8002`

## Shared Resources

Both teams import from `../shared/`:

```typescript
// Types
import type { GenerateAgentRequest, ContainerInfo } from '../shared/types';

// API Client (base functions)
import { agentGeneratorApi, dockerOrchestratorApi } from '../shared/lib/api-client';
```

**Rules:**
1. **Never modify `shared/` directly** — it's auto-generated from OpenAPI specs
2. Each team has its own `lib/api.ts` with domain-specific helpers
3. Each team has its own `types/index.ts` with domain-specific types

## Provided Files Summary

| File | Status | Team |
|------|--------|------|
| `shared/types/agent-generator.ts` | Auto-generated | Shared |
| `shared/types/docker-orchestrator.ts` | Auto-generated | Shared |
| `shared/types/index.ts` | Created | Shared |
| `shared/lib/api-client.ts` | Created | Shared |
| `studio-ui/types/index.ts` | Created | Studio UI |
| `studio-ui/lib/api.ts` | Created | Studio UI |
| `studio-ui/SCAFFOLDING.md` | Created | Studio UI |
| `control-room/types/index.ts` | Created | Control Room |
| `control-room/lib/api.ts` | Created | Control Room |
| `control-room/SCAFFOLDING.md` | Created | Control Room |

## API Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                            │
├────────────────────────────┬────────────────────────────────────┤
│       Studio UI            │         Control Room               │
│       (Port 3000)          │         (Port 3001)                │
│                            │                                    │
│  studio-ui/lib/api.ts      │  control-room/lib/api.ts          │
│  - generateAgent()         │  - listContainers()               │
│  - validateCode()          │  - startContainer()               │
│  - listAgents()            │  - stopContainer()                │
│  - deployAgent()           │  - getContainerLogs()             │
│                            │  - streamContainerLogs()          │
│                            │  - getContainerMetrics()          │
├────────────────────────────┴────────────────────────────────────┤
│                      shared/lib/api-client.ts                    │
│              (Base fetch wrappers, error handling)               │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND LAYER                             │
├────────────────────────────┬────────────────────────────────────┤
│   Agent Generator API      │     Docker Orchestrator API        │
│       (Port 8001)          │         (Port 8002)                │
│                            │                                    │
│  /api/generate-agent       │  /api/deploy                       │
│  /api/validate-code        │  /api/containers                   │
│  /api/agents               │  /api/containers/{id}/*            │
│                            │  /api/logs/{id}                    │
└────────────────────────────┴────────────────────────────────────┘
```

## Getting Started

### Studio UI Team

```bash
cd frontend/studio-ui
npm install
npm run dev  # Starts on http://localhost:3000
```

Read: `frontend/studio-ui/SCAFFOLDING.md`

### Control Room Team

```bash
cd frontend/control-room
npm install
npm run dev  # Starts on http://localhost:3001
```

Read: `frontend/control-room/SCAFFOLDING.md`

## Regenerating Types

When OpenAPI specs change, regenerate types:

```bash
# From project root
npx openapi-typescript ./docs/openapi-agent-generator.yaml -o ./frontend/shared/types/agent-generator.ts
npx openapi-typescript ./docs/openapi-docker-orchestrator.yaml -o ./frontend/shared/types/docker-orchestrator.ts
```

## Design System

Both apps use the same design system documented in:
- `/docs/design.md` — Original visual specification
- `/docs/design-system-ultra-grade-blueprint.md` — Enhanced 2026 blueprint

Key design principles:
- Cyber-ops control room aesthetic
- Deep space backgrounds with neon accents (cyan primary, purple secondary)
- WCAG 2.2 AA compliance
- Theme support (dark/light)
