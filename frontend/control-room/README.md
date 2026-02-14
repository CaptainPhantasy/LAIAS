# LAIAS Control Room

Container monitoring dashboard for the LAIAS (Legacy AI Agent Studio) platform.

## Overview

The Control Room provides a real-time operations hub for monitoring and managing deployed AI agent containers.

## Features

- **Container Grid View** - Visual card-based display of all deployed agents
- **Real-time Status Updates** - Live container state synchronization via polling
- **Log Streaming** - Real-time log viewer via Server-Sent Events (SSE)
- **Resource Metrics** - CPU, memory, and network I/O visualization
- **Lifecycle Management** - Start, stop, restart, and remove containers

## Tech Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS
- **State**: Zustand
- **Charts**: Recharts
- **Icons**: Lucide React
- **Virtualization**: @tanstack/react-virtual

## Development

### Prerequisites

- Node.js 20+
- Docker & Docker Compose (for backend services)

### Setup

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env.local

# Start development server
npm run dev
```

The app will be available at http://localhost:3001

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_DOCKER_ORCHESTRATOR_URL` | Docker Orchestrator API URL | `http://localhost:8002` |

## Project Structure

```
frontend/control-room/
├── app/                    # Next.js App Router pages
│   ├── layout.tsx         # Root layout with AppShell
│   ├── page.tsx           # Dashboard overview
│   ├── containers/        # Container pages
│   └── metrics/           # System metrics page
├── components/
│   ├── ui/                # Base UI primitives
│   ├── layout/            # App shell, sidebar, topbar
│   ├── dashboard/         # Dashboard widgets
│   ├── containers/        # Container components
│   ├── logs/              # Log viewer components
│   ├── metrics/           # Chart components
│   └── status/            # Status indicators
├── hooks/                 # Custom React hooks
├── store/                 # Zustand state stores
├── lib/                   # Utilities and API client
├── types/                 # TypeScript types
└── styles/                # Global styles
```

## API Integration

The Control Room communicates with the Docker Orchestrator API (port 8002):

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/containers` | GET | List all containers |
| `/api/containers/{id}` | GET | Get container details |
| `/api/containers/{id}/start` | POST | Start container |
| `/api/containers/{id}/stop` | POST | Stop container |
| `/api/containers/{id}/restart` | POST | Restart container |
| `/api/containers/{id}/remove` | DELETE | Remove container |
| `/api/containers/{id}/metrics` | GET | Get resource metrics |
| `/api/logs/{id}` | GET | Get paginated logs |
| `/api/logs/{id}/stream` | GET | Stream logs via SSE |

## Building for Production

```bash
# Build the application
npm run build

# Start production server
npm run start

# Docker build
docker build -t laias-control-room .
docker run -p 3001:3001 laias-control-room
```

## Related

- [Studio UI](../studio-ui/) - Agent builder interface
- [Docker Orchestrator](../../services/docker-orchestrator/) - Backend API
- [Shared Types](../shared/types/) - Type definitions

## License

MIT
