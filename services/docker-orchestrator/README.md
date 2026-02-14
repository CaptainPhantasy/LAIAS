# LAIS Docker Orchestrator

FastAPI service for managing Docker containers for deployed agents.

## Architecture

This service implements the **No-Build deployment strategy**:
- Uses a pre-built `laias/agent-runner:latest` image
- Mounts generated agent code as read-only volumes at `/app/agent`
- Spawns containers as siblings via the host Docker socket

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Host                               │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐                                    │
│  │ Orchestrator       │                                    │
│  │ (Container)        │                                    │
│  │  - FastAPI         │                                    │
│  │  - Docker SDK  │◄────┐                               │
│  └─────────────────────┘    │                               │
│         │                   │                               │
│         │ /var/run/         │                               │
│         │   docker.sock     │                               │
│         ▼                   │                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Agent Containers                          │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐    │  │
│  │  │ Agent #1   │  │ Agent #2   │  │ Agent #3   │    │  │
│  │  │ /app/agent │  │ /app/agent │  │ /app/agent │    │  │
│  │  │   (ro)     │  │   (ro)     │  │   (ro)     │    │  │
│  │  └────────────┘  └────────────┘  └────────────┘    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## API Endpoints

### Deploy
- `POST /api/deploy` - Deploy a new agent container

### Containers
- `GET /api/containers` - List all agent containers
- `GET /api/containers/{id}` - Get container details
- `POST /api/containers/{id}/start` - Start container
- `POST /api/containers/{id}/stop` - Stop container
- `DELETE /api/containers/{id}` - Remove container
- `GET /api/containers/{id}/metrics` - Get resource metrics

### Logs
- `GET /api/containers/{id}/logs` - Get container logs
- `WS /api/containers/{id}/logs/stream` - Real-time log streaming

### Health
- `GET /api/health` - Service health check
- `GET /api/health/docker` - Docker connection status
- `GET /api/health/containers` - Container status summary

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run with uvicorn
uvicorn app.main:app --reload --port 8000

# Or with Docker
docker build -t laias/docker-orchestrator .
docker run -d \
  -p 8000:8000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /var/laias/agents:/var/laias/agents \
  laias/docker-orchestrator
```

## Environment Variables

See `.env.example` for all configurable options.

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app tests/
```
