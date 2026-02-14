# Control Room — Scaffolding Guide

## Directory Structure

```
frontend/control-room/
├── app/                          # Next.js App Router pages
│   ├── layout.tsx                # Root layout with theme provider
│   ├── page.tsx                  # Dashboard overview (home)
│   ├── containers/
│   │   ├── page.tsx              # Container grid/list page
│   │   └── [id]/
│   │       ├── page.tsx          # Container detail page
│   │       └── logs/
│   │           └── page.tsx      # Log viewer page
│   ├── metrics/
│   │   └── page.tsx              # System metrics page
│   └── api/
│       └── proxy/
│           └── route.ts          # API proxy route (optional)
│
├── components/
│   ├── ui/                       # Base UI primitives (shared with Studio)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── badge.tsx
│   │   ├── modal.tsx
│   │   ├── tabs.tsx
│   │   ├── toast.tsx
│   │   ├── tooltip.tsx
│   │   ├── dropdown.tsx
│   │   ├── search-input.tsx
│   │   └── index.ts
│   │
│   ├── layout/                   # Layout components
│   │   ├── app-shell.tsx         # Main app shell with sidebar
│   │   ├── sidebar.tsx           # Navigation sidebar
│   │   ├── top-bar.tsx           # Header with logo/theme/user
│   │   └── index.ts
│   │
│   ├── dashboard/                # Dashboard-specific components
│   │   ├── kpi-card.tsx          # Single KPI metric card
│   │   ├── kpi-grid.tsx          # Grid of KPI cards
│   │   ├── recent-deployments.tsx
│   │   ├── system-status.tsx
│   │   └── index.ts
│   │
│   ├── containers/               # Container components
│   │   ├── container-card.tsx    # Single container card
│   │   ├── container-grid.tsx    # Grid layout for containers
│   │   ├── container-list.tsx    # List layout for containers
│   │   ├── container-detail.tsx  # Detail view header
│   │   ├── container-filters.tsx # Filter/search bar
│   │   ├── quick-actions.tsx     # Action buttons (start/stop/etc)
│   │   └── index.ts
│   │
│   ├── logs/                     # Log viewer components
│   │   ├── log-viewer.tsx        # Main log viewer container
│   │   ├── log-line.tsx          # Single log line
│   │   ├── log-filters.tsx       # Log level/search filters
│   │   ├── log-stream-status.tsx # Connection status indicator
│   │   └── index.ts
│   │
│   ├── metrics/                  # Metrics/chart components
│   │   ├── metrics-panel.tsx     # Container metrics container
│   │   ├── cpu-chart.tsx         # CPU usage chart
│   │   ├── memory-chart.tsx      # Memory usage chart
│   │   ├── network-chart.tsx     # Network I/O chart
│   │   ├── sparkline.tsx         # Mini inline chart
│   │   └── index.ts
│   │
│   └── status/                   # Status components
│       ├── status-badge.tsx      # Running/stopped/error badge
│       ├── health-indicator.tsx  # Service health dot
│       └── index.ts
│
├── hooks/
│   ├── use-containers.ts         # Container list state
│   ├── use-container-actions.ts  # Start/stop/restart actions
│   ├── use-log-stream.ts         # WebSocket log streaming
│   ├── use-metrics.ts            # Metrics polling
│   ├── use-polling.ts            # Generic polling hook
│   └── index.ts
│
├── lib/
│   ├── api.ts                    # API client (PROVIDED)
│   ├── utils.ts                  # Utility functions
│   ├── formatters.ts             # Number/date formatters
│   └── constants.ts              # App constants
│
├── types/
│   └── index.ts                  # TypeScript types (PROVIDED)
│
├── store/                        # State management (Zustand/Jotai)
│   ├── containers-store.ts       # Container list state
│   ├── log-viewer-store.ts       # Log viewer state
│   ├── settings-store.ts         # User preferences
│   └── index.ts
│
├── styles/
│   ├── globals.css               # Global styles + Tailwind
│   ├── variables.css             # CSS custom properties
│   └── themes/
│       ├── dark.css
│       └── light.css
│
├── public/
│   ├── icons/
│   └── images/
│
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js
├── Dockerfile
└── README.md
```

## API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `http://localhost:8002/api/containers` | GET | List all containers |
| `http://localhost:8002/api/containers/{id}` | GET | Get container details |
| `http://localhost:8002/api/containers/{id}/start` | POST | Start container |
| `http://localhost:8002/api/containers/{id}/stop` | POST | Stop container |
| `http://localhost:8002/api/containers/{id}/restart` | POST | Restart container |
| `http://localhost:8002/api/containers/{id}/remove` | DELETE | Remove container |
| `http://localhost:8002/api/containers/{id}/metrics` | GET | Get resource metrics |
| `http://localhost:8002/api/logs/{id}` | GET | Get paginated logs |
| `http://localhost:8002/api/logs/{id}/stream` | GET | Stream logs via SSE |

## Key Dependencies

```json
{
  "dependencies": {
    "next": "^15.x",
    "react": "^19.x",
    "react-dom": "^19.x",
    "recharts": "^2.x",
    "zustand": "^4.x",
    "tailwindcss": "^4.x",
    "@tanstack/react-virtual": "^3.x"
  }
}
```

## Environment Variables

```env
# .env.local
NEXT_PUBLIC_DOCKER_ORCHESTRATOR_URL=http://localhost:8002
```

## Build Commands

```bash
# Development
npm run dev          # Start on port 3001

# Production
npm run build
npm run start

# Docker
docker build -t laias-control-room .
docker run -p 3001:3000 laias-control-room
```

## Port Assignment

**Control Room runs on port 3001**

## Provided Files (Already Created)

| File | Purpose |
|------|---------|
| `types/index.ts` | TypeScript types, status configs, quick actions |
| `lib/api.ts` | API client with all Control Room functions + polling utilities |

## Shared Dependencies (Do Not Modify)

| File | Purpose |
|------|---------|
| `../shared/types/agent-generator.ts` | Auto-generated from OpenAPI |
| `../shared/types/docker-orchestrator.ts` | Auto-generated from OpenAPI |
| `../shared/types/index.ts` | Type re-exports and utilities |
| `../shared/lib/api-client.ts` | Base API client |

## Team Responsibilities

| Component Area | Team Member Focus |
|----------------|-------------------|
| `components/ui/` | Base component library |
| `components/layout/` | App shell, navigation |
| `components/dashboard/` | KPI cards, overview widgets |
| `components/containers/` | Container cards, grid, actions |
| `components/logs/` | Log viewer, streaming, filtering |
| `components/metrics/` | Charts, resource visualization |
| `hooks/` | Custom React hooks |
| `store/` | State management |
| `app/` | Page routing and layouts |

## Real-Time Features

### WebSocket / SSE Log Streaming

```typescript
// Example usage in component
import { streamContainerLogs } from '@/lib/api';

useEffect(() => {
  const cleanup = streamContainerLogs(
    containerId,
    (entry) => setLogs(prev => [...prev, entry]),
    () => setIsConnected(true),
    () => setIsConnected(false),
    (err) => setError(err.message)
  );

  return cleanup;
}, [containerId]);
```

### Container Polling

```typescript
// Example usage in component
import { createContainerPoller } from '@/lib/api';

useEffect(() => {
  const cleanup = createContainerPoller(
    (result) => setContainers(result.containers || []),
    10000 // 10 second interval
  );

  return cleanup;
}, []);
```

## Chart Library Recommendation

Use **Recharts** for data visualization:
- Composable and React-friendly
- Good performance for real-time updates
- Supports responsive containers
- Easy to customize for dark theme
