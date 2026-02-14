# LAIAS Master Plan
## Legacy AI Agent Studio - Architecture & Project Overview

> **Version**: 2.0  
> **Last Updated**: February 13, 2026  
> **Status**: Production-Ready Specification

---

## Executive Summary

**Legacy AI Agent Studio (LAIAS)** is a commercial AI agent builder platform that enables users to describe agent ideas in natural language and receive production-ready, deployable AI agent code. The platform generates, deploys, and manages sophisticated CrewAI-based agents in isolated Docker containers.

### Business Objective

Transform AI agent development into a service offering where clients describe their needs and LAIAS automatically generates, validates, deploys, and monitors sophisticated multi-agent systems—all without requiring coding expertise from end users.

### Core Value Proposition

| Traditional Approach | LAIAS Approach |
|---------------------|----------------|
| Write agent code manually | Describe in natural language |
| Configure Docker deployments | One-click deployment |
| Build monitoring infrastructure | Built-in observability |
| Debug complex agent interactions | Pre-validated patterns |
| Weeks of development | Minutes to production |

---

## Architecture Philosophy

### The "Godzilla" Pattern

All generated agents follow the **Godzilla architectural pattern**—a production-grade CrewAI Flow implementation with:

- **Typed State Management**: Pydantic `BaseModel` for runtime validation
- **Event-Driven Architecture**: Decorators (`@start`, `@listen`, `@router`) for flow control
- **Agent Factory Pattern**: Specialized methods for agent creation
- **Error Recovery**: Built-in retry logic and human escalation paths
- **Full Observability**: Structured logging and analytics integration

```
📄 Reference Implementation: /home/ubuntu/GODZILLA_TEMPLATE.py
```

### The "No-Build" Deployment Strategy

**CRITICAL ARCHITECTURE DECISION**: LAIAS uses volume mounting instead of building Docker images per agent.

```bash
# ❌ WRONG: Building per agent
docker build -t laias-agent-{id} .  # Slow, wasteful

# ✅ CORRECT: Pre-built base image + volume mount
docker run -v /path/to/code:/app/agent laias/agent-runner:latest  # Instant
```

| Metric | Build-per-Agent | Volume Mount (LAIAS) |
|--------|-----------------|----------------------|
| Deploy Time | 30-60 seconds | < 1 second |
| Disk per Agent | ~500MB | ~0MB (shared base) |
| Base Image Updates | Rebuild all | Update once |
| Container Architecture | DinD complexity | Simple siblings |

---

## System Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE LAYER                            │
│  ┌─────────────────────────────┐    ┌─────────────────────────────────────┐ │
│  │      STUDIO UI              │    │      CONTROL ROOM DASHBOARD         │ │
│  │  • Agent Builder Form       │    │  • Real-time Container Status       │ │
│  │  • Monaco Code Editor       │    │  • Log Streaming                    │ │
│  │  • Code Preview/Export      │    │  • Resource Monitoring              │ │
│  └─────────────┬───────────────┘    └───────────────┬─────────────────────┘ │
│                │                                     │                       │
│                └─────────────┬───────────────────────┘                       │
│                              │                                               │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                       INTEGRATION LAYER                                  ││
│  │                 API Client Library & Type Definitions                    ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SERVICE LAYER                                   │
│  ┌─────────────────────────────┐    ┌─────────────────────────────────────┐ │
│  │   AGENT GENERATOR API       │    │    DOCKER ORCHESTRATOR              │ │
│  │  • LLM Integration          │    │  • Container Lifecycle              │ │
│  │  • Code Generation          │    │  • Volume Management                │ │
│  │  • Pattern Validation       │    │  • Log Streaming                    │ │
│  │  • POST /api/generate-agent │    │  • POST /api/deploy                 │ │
│  │  • POST /api/validate-code  │    │  • GET /api/containers              │ │
│  └─────────────┬───────────────┘    └───────────────┬─────────────────────┘ │
│                │                                     │                       │
│                └─────────────┬───────────────────────┘                       │
│                              │                                               │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                     INFRASTRUCTURE LAYER                                 ││
│  │  PostgreSQL (agents, deployments, logs)  │  Redis (task queue, cache)   ││
│  │  Docker Host Socket  │  Agent Code Storage Volume                        ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EXECUTION LAYER                                    │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐   │
│  │ Agent         │ │ Agent         │ │ Agent         │ │ Agent         │   │
│  │ Container A   │ │ Container B   │ │ Container C   │ │ Container N   │   │
│  │ (volume:code) │ │ (volume:code) │ │ (volume:code) │ │ (volume:code) │   │
│  └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘   │
│                         All using: laias/agent-runner:latest                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Build Phases Overview

The LAIAS platform is built in **5 sequential phases**, each building upon the previous:

### Phase 1: Foundation & Infrastructure
Establish the core infrastructure that all services depend on.

| Component | Purpose |
|-----------|---------|
| Database Schema | Store agents, deployments, logs |
| Docker Compose | Orchestrate all services |
| Agent Runner Base Image | Pre-built image for all agents |
| Redis Configuration | Task queues and caching |

### Phase 2: Core Services
Build the backend APIs that power the platform.

| Component | Purpose |
|-----------|---------|
| Agent Generator API | LLM-powered code generation |
| Docker Orchestrator | Container lifecycle management |

### Phase 3: User Interfaces
Create the frontend applications for user interaction.

| Component | Purpose |
|-----------|---------|
| Studio UI | Agent builder interface |
| Control Room Dashboard | Monitoring and management |

### Phase 4: Integration & Deployment
Connect all components and prepare for production.

| Component | Purpose |
|-----------|---------|
| Integration Layer | API clients, type safety |
| End-to-End Testing | Full workflow validation |
| Production Configuration | Environment setup |

### Phase 5: Advanced Features
Enhance the platform with additional capabilities.

| Component | Purpose |
|-----------|---------|
| Agent Templates | Pre-built agent configurations |
| Analytics Dashboard | Usage and cost tracking |
| Team Collaboration | Multi-user support |

---

## Technology Stack

### Backend
| Technology | Purpose |
|------------|---------|
| Python 3.11+ | Service implementation |
| FastAPI | REST API framework |
| CrewAI | Agent orchestration |
| Pydantic | Data validation |
| SQLAlchemy | Database ORM |
| Docker SDK | Container management |
| structlog | Structured logging |

### Frontend
| Technology | Purpose |
|------------|---------|
| NextJS 15 | React framework |
| TypeScript | Type safety |
| Tailwind CSS | Styling |
| Monaco Editor | Code editing |
| React Hook Form | Form management |
| Zod | Schema validation |

### Infrastructure
| Technology | Purpose |
|------------|---------|
| PostgreSQL 15 | Primary database |
| Redis 7 | Task queue, caching |
| Docker Compose | Service orchestration |
| Nginx | Reverse proxy (production) |

### AI/LLM
| Technology | Purpose |
|------------|---------|
| OpenAI API | Primary LLM provider |
| Anthropic API | Alternative LLM provider |
| CrewAI Tools | Agent capabilities |

---

## Key Reference Files

| File | Description |
|------|-------------|
| `/home/ubuntu/LAIAS_BUILD_GUIDE.md` | **Detailed technical specifications for all components** |
| `/home/ubuntu/GODZILLA_TEMPLATE.py` | **Gold standard agent implementation pattern** |
| `/home/ubuntu/LAIAS_MASTER_PLAN.md` | This document - project overview |

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- OpenAI API key and/or Anthropic API key

### Environment Setup
```bash
# Clone/create project directory
mkdir -p /home/ubuntu/laias && cd /home/ubuntu/laias

# Copy environment template
cp .env.example .env

# Add API keys to .env
echo "OPENAI_API_KEY=sk-..." >> .env
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env

# Build and start infrastructure
docker-compose up -d postgres redis

# Build the agent runner base image
docker build -f Dockerfile.agent-runner -t laias/agent-runner:latest .

# Start all services
docker-compose up -d
```

### Service Ports
| Service | Port | URL |
|---------|------|-----|
| Studio UI | 3000 | http://localhost:3000 |
| Control Room | 3001 | http://localhost:3001 |
| Agent Generator API | 8001 | http://localhost:8001 |
| Docker Orchestrator | 8002 | http://localhost:8002 |
| PostgreSQL | 5432 | localhost:5432 |
| Redis | 6379 | localhost:6379 |

---

## Success Criteria

The LAIAS platform is complete when:

1. ✅ Users can describe agents in natural language via the Studio UI
2. ✅ The system generates valid Python code following the Godzilla pattern
3. ✅ Code validation shows pattern compliance score ≥ 0.9
4. ✅ One-click deployment creates running containers in < 2 seconds
5. ✅ Control Room shows real-time container status and logs
6. ✅ Users can export agent code as downloadable ZIP files
7. ✅ All services are containerized and orchestrated via Docker Compose
8. ✅ Full end-to-end workflow functions without manual intervention

---

## Next Steps

**Begin implementation by following the detailed specifications in:**

```
📄 /home/ubuntu/LAIAS_BUILD_GUIDE.md
```

This guide provides:
- Complete API specifications
- Full code examples
- Build order with dependencies
- Integration points
- Testing requirements

---

## Glossary

| Term | Definition |
|------|------------|
| **Agent** | An AI entity that can perform tasks autonomously |
| **Crew** | A team of agents working together on tasks |
| **Flow** | The orchestration layer that manages agent execution |
| **Godzilla Pattern** | The architectural pattern all generated agents follow |
| **State** | The typed data structure tracking agent execution |
| **Task** | A specific unit of work assigned to an agent |
| **Tool** | An external capability an agent can use (web search, scraping, etc.) |

---

*This document provides the strategic overview. For implementation details, see LAIAS_BUILD_GUIDE.md.*
