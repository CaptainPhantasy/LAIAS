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
│ Agent Generator        │ Healthy │ http://localhost:8001       │
│ Docker Orchestrator    │ Healthy │ http://localhost:8002       │
│ PostgreSQL             │ Healthy │ localhost:5432              │
│ Redis                  │ Healthy │ localhost:6379              │
│ Studio UI              │ WIP     │ http://localhost:3000       │
│ Control Room           │ WIP     │ http://localhost:3001       │
└────────────────────────┴─────────┴─────────────────────────────┘
```

## Architecture

```
LAIAS/
├── services/
│   ├── agent-generator/     # FastAPI service for code generation (8001)
│   └── docker-orchestrator/ # FastAPI service for container management (8002)
├── frontend/                # Phase 3 - In Development
│   ├── studio-ui/           # Chat-to-agent interface
│   └── control-room/        # Agent monitoring dashboard
├── infrastructure/
│   ├── init.sql             # PostgreSQL schema
│   └── redis.conf           # Redis configuration
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
# Edit .env with your API keys:
# - ZAI_API_KEY (default provider)
# - OPENAI_API_KEY
# - ANTHROPIC_API_KEY
# - COMPOSIO_API_KEY (for MCP tools)
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

### 4. Access API Documentation
- Agent Generator: http://localhost:8001/api/docs
- Docker Orchestrator: http://localhost:8002/api/docs

## API Endpoints

### Agent Generator (Port 8001)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/generate-agent` | POST | Generate agent code from description |
| `/api/validate-code` | POST | Validate generated code |
| `/api/agents` | GET | List saved agents |
| `/api/agents/{id}` | GET/PUT/DELETE | Manage individual agents |
| `/health` | GET | Service health check |

### Docker Orchestrator (Port 8002)
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
