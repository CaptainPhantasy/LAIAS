# Control Room UI

## Overview

The Control Room is a NextJS-based operations dashboard for monitoring and managing deployed AI agent containers in the LAIAS system.

| Attribute | Value |
|-----------|-------|
| **Location** | `frontend/control-room/` |
| **Port** | 3001 |
| **URL** | http://localhost:3001 |
| **Framework** | NextJS 15 + TypeScript |
| **Styling** | Tailwind CSS |

---

## Purpose

The Control Room serves as the central operations hub for:
- Real-time monitoring of deployed AI agent containers
- Managing the full lifecycle of agent containers (start, stop, restart, remove)
- Viewing live logs and execution traces
- Monitoring resource utilization metrics

---

## Key Features

### 1. Container Grid View
- Visual card-based display of all deployed agents
- Status indicators (running, stopped, error states)
- Quick actions on each container

### 2. Real-time Status Updates
- Live container state synchronization
- WebSocket or polling-based updates
- Immediate visibility of state changes

### 3. Log Streaming
- Real-time log viewer via WebSocket
- Filterable by log level (info, warning, error)
- Search and export capabilities

### 4. Resource Metrics
- CPU utilization charts
- Memory consumption graphs
- Network I/O statistics
- Historical trending

### 5. Lifecycle Management
- Start containers
- Stop containers
- Restart containers
- Remove/delete containers

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Control Room UI                          │
│                    (NextJS - Port 3001)                     │
├─────────────────────────────────────────────────────────────┤
│  Pages                                                      │
│  ├── /              → Dashboard home                        │
│  ├── /containers    → Container list                        │
│  ├── /containers/[id]    → Container detail             │
│  ├── /containers/[id]/logs → Log viewer                 │
│  └── /metrics       → System metrics                       │
├─────────────────────────────────────────────────────────────┤
│  Components                                                 │
│  ├── dashboard/    → Dashboard widgets                     │
│  ├── logs/         → Log streaming components              │
│  ├── metrics/     → Charts and metrics display            │
│  └── actions/     → Lifecycle action buttons              │
├─────────────────────────────────────────────────────────────┤
│  Hooks                                                      │
│  ├── useContainers.ts → Container state management         │
│  ├── useLogStream.ts → WebSocket log streaming            │
│  └── useMetrics.ts   → Resource metrics polling            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │   Docker Orchestrator API     │
              │        (Port 8002)            │
              └───────────────────────────────┘
```

---

## Project Structure

```
frontend/control-room/
├── app/
│   ├── page.tsx                # Dashboard home
│   ├── layout.tsx              # Root layout
│   ├── containers/
│   │   ├── page.tsx            # Container list
│   │   └── [id]/
│   │       ├── page.tsx        # Container detail
│   │       └── logs/
│   │           └── page.tsx    # Log viewer
│   └── metrics/
│       └── page.tsx            # System metrics
├── components/
│   ├── dashboard/              # Dashboard widgets
│   ├── logs/                   # Log components
│   ├── metrics/                # Metrics charts
│   └── actions/                # Action buttons
├── hooks/
│   ├── useContainers.ts        # Container state
│   ├── useLogStream.ts         # Log streaming
│   └── useMetrics.ts           # Metrics polling
├── Dockerfile
└── package.json
```

---

## API Integration

### REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/containers` | GET | List all containers |
| `/api/containers/{id}` | GET | Get container details |
| `/api/containers/{id}/start` | POST | Start container |
| `/api/containers/{id}/stop` | POST | Stop container |
| `/api/containers/{id}/restart` | POST | Restart container |
| `/api/containers/{id}` | DELETE | Remove container |
| `/api/containers/{id}/metrics` | GET | Get resource metrics |

### WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/containers/{id}/logs/stream` | Real-time log streaming |

---

## Requirements

### Functional Requirements

- [ ] Display all deployed agent containers in a grid layout
- [ ] Show real-time container status (running/stopped/error)
- [ ] Stream logs via WebSocket connection
- [ ] Display CPU, memory, and network metrics
- [ ] Provide lifecycle action buttons (start/stop/restart/remove)
- [ ] Support container search and filtering
- [ ] Enable log export functionality

### Non-Functional Requirements

- [ ] Response time < 200ms for UI interactions
- [ ] Support for 100+ concurrent container monitoring
- [ ] WebSocket reconnection with automatic retry
- [ ] Responsive design for desktop and tablet
- [ ] Dark mode support

### Technical Requirements

- [ ] NextJS 15 with App Router
- [ ] TypeScript strict mode
- [ ] Tailwind CSS for styling
- [ ] WebSocket client implementation
- [ ] Error boundary components
- [ ] Loading state skeletons

---

## Dependencies

### Backend Services

| Service | Port | Purpose |
|---------|------|---------|
| Docker Orchestrator | 8002 | Container management API |

### NPM Packages

```json
{
  "dependencies": {
    "next": "^15.x",
    "react": "^19.x",
    "react-dom": "^19.x",
    "tailwindcss": "^4.x"
  }
}
```

---

## Current Status

| Status | Notes |
|--------|-------|
| **Phase** | Planning/Design |
| **Implementation** | Blocked |
| **Blocker** | Requires Phase 2 (Core Services) completion |

The Control Room UI implementation will begin after the core backend services (Agent Generator and Docker Orchestrator) are fully operational and tested.

---

## Related Documentation

- [Studio UI](./studio-ui.md)
- [Docker Orchestrator](../services/docker-orchestrator/)
- [Architecture Overview](../README.md)
