# LAIAS - Legacy AI Agent Studio

A Dockerized platform for generating, deploying, and monitoring AI agents using natural language descriptions.

## What LAIAS Does

1. **Describe an agent idea** in natural language (e.g., "Make a market research swarm")
2. **Generate Python code** using an LLM that follows the "Gold Standard" CrewAI architecture
3. **Deploy and run** agents in isolated Docker containers
4. **Monitor execution** via a dashboard

## Architecture

```
LAIAS/
├── services/
│   ├── agent-generator/     # FastAPI service for code generation
│   └── docker-orchestrator/ # FastAPI service for container management
├── frontend/
│   ├── studio-ui/           # Chat-to-agent interface (Phase 3)
│   └── control-room/        # Agent monitoring dashboard (Phase 3)
├── infrastructure/
│   ├── init.sql             # PostgreSQL schema
│   └── redis.conf           # Redis configuration
├── templates/
│   └── godzilla_reference.py # Gold standard agent template
└── docker-compose.yml       # Root orchestration
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)

### 1. Configure Environment
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

### 2. Start Services
```bash
docker-compose up -d
```

### 3. Verify Health
```bash
curl http://localhost:8001/health  # Agent Generator
curl http://localhost:8002/health  # Docker Orchestrator
```

## API Endpoints

### Agent Generator (Port 8001)
- `POST /api/generate` - Generate agent code from description
- `POST /api/validate` - Validate generated code
- `GET /api/agents` - List generated agents
- `GET /health` - Service health check

### Docker Orchestrator (Port 8002)
- `POST /api/deploy` - Deploy an agent container
- `GET /api/containers` - List running containers
- `GET /api/logs/{id}` - Get container logs
- `GET /health` - Service health check

## Documentation

- [Master Plan](docs/MASTER_PLAN.md) - Project roadmap and phases
- [Build Guide](docs/BUILD_GUIDE.md) - Detailed implementation guide
- [Implementation Status](IMPLEMENTATION_STATUS.md) - Current progress tracker

## Development

### Running Tests
```bash
# Agent Generator
cd services/agent-generator && pytest

# Docker Orchestrator
cd services/docker-orchestrator && pytest
```

### Local Development
Each service has its own `requirements.txt` and can run independently:

```bash
# Agent Generator
cd services/agent-generator
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Docker Orchestrator
cd services/docker-orchestrator
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002
```

## License

MIT
