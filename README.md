# LAIAS - Legacy AI Agent Studio

A Dockerized platform for generating, deploying, and monitoring AI agents using natural language descriptions.

## What LAIAS Does

1. **Describe an agent idea** in natural language (e.g., "Make a market research swarm")
2. **Generate Python code** using an LLM that follows the "Gold Standard" CrewAI architecture
3. **Deploy and run** agents in isolated Docker containers
4. **Monitor execution** via a dashboard

## Current Status

```
┌────────────────────────┬─────────┬─────────────────────────────┐
│ Service                │ Status  │ URL                         │
├────────────────────────┼─────────┼─────────────────────────────┤
│ Studio UI              │ Healthy │ http://localhost:4527       │
│ Control Room           │ Healthy │ http://localhost:4528       │
│ Agent Generator        │ Healthy │ http://localhost:4521       │
│ Docker Orchestrator    │ Healthy │ http://localhost:4522       │
│ PostgreSQL             │ Healthy │ localhost:5432 (local only) │
│ Redis                  │ Healthy │ localhost:6379 (local only) │
└────────────────────────┴─────────┴─────────────────────────────┘
```

## Architecture

```
LAIAS/
├── services/
│   ├── agent-generator/     # FastAPI service for code generation (8001)
│   └── docker-orchestrator/ # FastAPI service for container management (8002)
├── frontend/
│   ├── studio-ui/           # Chat-to-agent interface (port 3000)
│   ├── control-room/        # Agent monitoring dashboard (port 3001)
│   └── shared/              # Shared types and utilities
├── infrastructure/
│   ├── init.sql             # PostgreSQL schema
│   ├── redis.conf           # Redis configuration
│   ├── backup.sh            # Database backup script
│   └── restore.sh           # Database restore script
├── templates/
│   ├── godzilla_reference.py # Gold standard agent template
│   └── agents/              # 126 production-ready agent configs
│       ├── development/      # 30 agents
│       ├── project_management/ # 20 agents
│       ├── quality_assurance/ # 20 agents
│       └── ...               # 7 more categories
├── docs/
│   ├── openapi-agent-generator.yaml  # API spec for Studio UI
│   └── openapi-docker-orchestrator.yaml # API spec for Control Room
└── docker-compose.yml       # Root orchestration
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)

### 1. Configure Environment
```bash
cp .env.example .env

# Generate required security secrets:
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
# Run this 3 times and paste the values into .env for:
#   JWT_SECRET_KEY=<generated>
#   POSTGRES_PASSWORD=<generated>
#   ORCHESTRATOR_SECRET_KEY=<generated>

# Set a Redis password:
#   REDIS_PASSWORD=<generated>

# Add at least one LLM provider API key:
#   ZAI_API_KEY=<your-key>       (default provider)
#   OPENAI_API_KEY=<your-key>
#   ANTHROPIC_API_KEY=<your-key>
#   COMPOSIO_API_KEY=<your-key>  (optional, for MCP tools)

# Stack Auth (frontend authentication):
#   Create a project at https://app.stack-auth.com
#   NEXT_PUBLIC_STACK_PROJECT_ID=<your-project-id>
#   STACK_SECRET_SERVER_KEY=<your-server-key>
```

> **Security note:** Without `JWT_SECRET_KEY`, the auth system generates an ephemeral
> key on each restart (sessions won't survive restarts). `POSTGRES_PASSWORD` and
> `REDIS_PASSWORD` secure the data stores. All three are strongly recommended for any
> non-throwaway deployment.
>
> **Authentication:** Both frontend apps require Stack Auth for login. Create a free
> project at [app.stack-auth.com](https://app.stack-auth.com), enable your preferred
> OAuth providers (GitHub, Google, etc.), and add the project ID and secret server key
> to `.env`. Without these, the frontends will not build.

### 2. Build Agent Runner Image

Before deploying agents, you must build the base agent runner image. This image contains
all CrewAI dependencies and is reused for all agent deployments:

```bash
docker-compose build agent-runner
```

> **Why is this required?** The agent-runner is defined with `profiles: [build-only]` 
> because it's a base image, not a running service. It's used as the template for 
> spawning agent containers on demand.

### 3. Start Services
```bash
docker-compose up -d
```

### 4. Verify Health
```bash
# Backend services
curl http://localhost:4521/health  # Agent Generator
curl http://localhost:4522/health  # Docker Orchestrator

# Frontend apps (login required — you'll be redirected to Stack Auth sign-in)
# Studio UI:    http://localhost:4527
# Control Room: http://localhost:4528
```

### 5. Access API Documentation
- Agent Generator: http://localhost:4521/api/docs
- Docker Orchestrator: http://localhost:4522/api/docs

## API Endpoints

### Agent Generator (Port 4521)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/generate-agent` | POST | Generate agent code from description |
| `/api/validate-code` | POST | Validate generated code |
| `/api/agents` | GET | List saved agents |
| `/api/agents/{id}` | GET/PUT/DELETE | Manage individual agents |
| `/health` | GET | Service health check |

### Docker Orchestrator (Port 4522)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/deploy` | POST | Deploy agent to container |
| `/api/containers` | GET | List running containers |
| `/api/containers/{id}/start` | POST | Start container |
| `/api/containers/{id}/stop` | POST | Stop container |
| `/api/logs/{id}` | GET | Get container logs |
| `/health` | GET | Service health check |

## Agent Library

126 production-ready CrewAI agent configurations organized by function:

| Category | Count | Purpose |
|----------|-------|---------|
| `development/` | 30 | Code, APIs, implementation |
| `project_management/` | 20 | Coordination, planning |
| `quality_assurance/` | 20 | Testing, auditing |
| `research_analysis/` | 12 | Intelligence, investigation |
| `tools_integration/` | 11 | MCP, integrations |
| `design_experience/` | 8 | UX/UI |
| `data_analytics/` | 7 | Data analysis |
| `documentation_knowledge/` | 7 | Knowledge management |
| `business_strategy/` | 6 | Growth, support |
| `security_compliance/` | 5 | Security, policy |

## Documentation

- [Implementation Status](IMPLEMENTATION_STATUS.md) - Current progress tracker
- [Master Plan](docs/MASTER_PLAN.md) - Project roadmap and phases
- [Build Guide](docs/BUILD_GUIDE.md) - Detailed implementation guide
- [OpenAPI - Agent Generator](docs/openapi-agent-generator.yaml) - Studio UI API spec
- [OpenAPI - Docker Orchestrator](docs/openapi-docker-orchestrator.yaml) - Control Room API spec

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

## LLM Providers

LAIAS supports multiple LLM providers with ZAI GLM-5 as default:

| Provider | Models | Status |
|----------|--------|--------|
| ZAI | GLM-5 | Default |
| OpenAI | GPT-4o, GPT-4 | Verified |
| Anthropic | Claude 3.5 | Verified |
| OpenRouter | Multi-model | Supported |
| Google | Gemini | Supported |
| Mistral | Mistral | Supported |

## License

MIT
