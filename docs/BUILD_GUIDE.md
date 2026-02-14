# LAIAS Build Guide
## Legacy AI Agent Studio - Complete Technical Specification

> **Version**: 2.0  
> **Last Updated**: February 13, 2026  
> **Status**: Production-Ready Specification

---

## Table of Contents

1. [Build Order & Dependencies](#build-order--dependencies)
2. [Phase 1: Foundation & Infrastructure](#phase-1-foundation--infrastructure)
3. [Phase 2: Core Services](#phase-2-core-services)
4. [Phase 3: User Interfaces](#phase-3-user-interfaces)
5. [Phase 4: Integration & Deployment](#phase-4-integration--deployment)
6. [Phase 5: Advanced Features](#phase-5-advanced-features)
7. [API Reference](#api-reference)
8. [Testing Requirements](#testing-requirements)

---

## Build Order & Dependencies

### Dependency Graph

```mermaid
graph TD
    subgraph "Phase 1: Foundation"
        A[1.1 Database Schema]
        B[1.2 Docker Compose Base]
        C[1.3 Agent Runner Image]
        D[1.4 Redis Configuration]
    end
    
    subgraph "Phase 2: Core Services"
        E[2.1 Agent Generator API]
        F[2.2 Docker Orchestrator]
    end
    
    subgraph "Phase 3: User Interfaces"
        G[3.1 Studio UI]
        H[3.2 Control Room Dashboard]
    end
    
    subgraph "Phase 4: Integration"
        I[4.1 Integration Layer]
        J[4.2 E2E Testing]
    end
    
    A --> E
    A --> F
    B --> E
    B --> F
    C --> F
    D --> E
    D --> F
    E --> G
    E --> I
    F --> G
    F --> H
    F --> I
    G --> J
    H --> J
    I --> J
```

### Build Sequence

| Order | Component | Dependencies | Est. Time |
|-------|-----------|--------------|-----------|
| 1.1 | Database Schema | None | 2 hours |
| 1.2 | Docker Compose Base | None | 1 hour |
| 1.3 | Agent Runner Image | Docker Compose | 1 hour |
| 1.4 | Redis Configuration | Docker Compose | 30 min |
| 2.1 | Agent Generator API | Database, Redis | 8 hours |
| 2.2 | Docker Orchestrator | Database, Agent Runner | 6 hours |
| 3.1 | Studio UI | Agent Generator API | 8 hours |
| 3.2 | Control Room | Docker Orchestrator | 6 hours |
| 4.1 | Integration Layer | All APIs | 4 hours |
| 4.2 | E2E Testing | All Components | 4 hours |

---

## Phase 1: Foundation & Infrastructure

### 1.1 Database Schema

**WHAT**: PostgreSQL database schema for storing agents, deployments, and execution logs.

**WHY**: Persistent storage is required for agent definitions, deployment state, and historical data. PostgreSQL provides ACID compliance and JSON support for flexible metadata storage.

**DEPENDENCIES**: None (foundational component)

**INTEGRATION POINTS**:
- Agent Generator API reads/writes agent definitions
- Docker Orchestrator reads/writes deployment records
- Control Room Dashboard queries logs and metrics

#### Technical Specification

**File**: `/home/ubuntu/laias/infrastructure/init.sql`

```sql
-- =============================================================================
-- LAIAS Database Schema
-- =============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- AGENTS TABLE
-- Stores generated agent definitions and code
-- =============================================================================
CREATE TABLE agents (
    id VARCHAR(50) PRIMARY KEY DEFAULT 'gen_' || substr(md5(random()::text), 1, 12),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Generated code (Godzilla pattern)
    flow_code TEXT NOT NULL,
    agents_yaml TEXT,
    state_class TEXT,
    
    -- Configuration
    complexity VARCHAR(20) CHECK (complexity IN ('simple', 'moderate', 'complex')),
    task_type VARCHAR(50) CHECK (task_type IN ('research', 'development', 'analysis', 'automation', 'general')),
    tools JSONB DEFAULT '[]'::jsonb,
    requirements JSONB DEFAULT '[]'::jsonb,
    
    -- Metadata
    llm_provider VARCHAR(20) DEFAULT 'openai',
    model VARCHAR(50) DEFAULT 'gpt-4o',
    estimated_cost_per_run DECIMAL(10, 4),
    complexity_score INTEGER CHECK (complexity_score BETWEEN 1 AND 10),
    
    -- Validation
    validation_status JSONB DEFAULT '{}'::jsonb,
    flow_diagram TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- DEPLOYMENTS TABLE
-- Tracks container deployments for each agent
-- =============================================================================
CREATE TABLE deployments (
    id VARCHAR(50) PRIMARY KEY DEFAULT 'deploy_' || substr(md5(random()::text), 1, 12),
    agent_id VARCHAR(50) NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    
    -- Container info
    container_id VARCHAR(100),
    container_name VARCHAR(100),
    
    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'creating', 'starting', 'running', 'stopped', 'error', 'terminated')),
    
    -- Resource limits
    cpu_limit DECIMAL(4, 2) DEFAULT 1.0,
    memory_limit VARCHAR(20) DEFAULT '512m',
    
    -- Environment
    environment_vars JSONB DEFAULT '{}'::jsonb,
    
    -- Lifecycle timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    stopped_at TIMESTAMP WITH TIME ZONE,
    
    -- Error tracking
    last_error TEXT,
    error_count INTEGER DEFAULT 0
);

-- =============================================================================
-- EXECUTION LOGS TABLE
-- Stores logs from agent executions
-- =============================================================================
CREATE TABLE execution_logs (
    id BIGSERIAL PRIMARY KEY,
    deployment_id VARCHAR(50) NOT NULL REFERENCES deployments(id) ON DELETE CASCADE,
    
    -- Log data
    level VARCHAR(20) NOT NULL CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    message TEXT NOT NULL,
    source VARCHAR(100),
    
    -- Structured data
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamp
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- EXECUTION METRICS TABLE
-- Stores performance metrics per execution
-- =============================================================================
CREATE TABLE execution_metrics (
    id BIGSERIAL PRIMARY KEY,
    deployment_id VARCHAR(50) NOT NULL REFERENCES deployments(id) ON DELETE CASCADE,
    
    -- Resource usage
    cpu_percent DECIMAL(5, 2),
    memory_usage_mb DECIMAL(10, 2),
    
    -- Execution stats
    tokens_used INTEGER DEFAULT 0,
    api_calls INTEGER DEFAULT 0,
    estimated_cost DECIMAL(10, 4) DEFAULT 0,
    
    -- Duration
    execution_duration_seconds INTEGER,
    
    -- Timestamp
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- INDEXES
-- =============================================================================
CREATE INDEX idx_agents_created_at ON agents(created_at DESC);
CREATE INDEX idx_agents_task_type ON agents(task_type);
CREATE INDEX idx_deployments_agent_id ON deployments(agent_id);
CREATE INDEX idx_deployments_status ON deployments(status);
CREATE INDEX idx_deployments_created_at ON deployments(created_at DESC);
CREATE INDEX idx_execution_logs_deployment_id ON execution_logs(deployment_id);
CREATE INDEX idx_execution_logs_timestamp ON execution_logs(timestamp DESC);
CREATE INDEX idx_execution_logs_level ON execution_logs(level);
CREATE INDEX idx_execution_metrics_deployment_id ON execution_metrics(deployment_id);

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Update updated_at timestamp on agents
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_agents_updated_at
    BEFORE UPDATE ON agents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

---

### 1.2 Docker Compose Base

**WHAT**: Docker Compose configuration orchestrating all LAIAS services.

**WHY**: Containerization ensures consistent environments, easy scaling, and simplified deployment. Docker Compose manages service dependencies and networking.

**DEPENDENCIES**: None (foundational component)

**INTEGRATION POINTS**:
- All services connect via `laias-network`
- Shared volume for agent code storage
- PostgreSQL and Redis available to all backend services

#### Technical Specification

**File**: `/home/ubuntu/laias/docker-compose.yml`

```yaml
version: '3.8'

services:
  # ===========================================================================
  # INFRASTRUCTURE SERVICES
  # ===========================================================================
  
  postgres:
    image: postgres:15-alpine
    container_name: laias-postgres
    environment:
      POSTGRES_USER: laias
      POSTGRES_PASSWORD: laias_secure_password
      POSTGRES_DB: laias
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infrastructure/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U laias"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - laias-network

  redis:
    image: redis:7-alpine
    container_name: laias-redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - laias-network

  # ===========================================================================
  # AGENT RUNNER BASE IMAGE
  # Build once, used for all agent deployments
  # ===========================================================================
  
  agent-runner:
    build:
      context: .
      dockerfile: Dockerfile.agent-runner
    image: laias/agent-runner:latest
    profiles:
      - build-only  # Only used for building, not running
    networks:
      - laias-network

  # ===========================================================================
  # BACKEND SERVICES
  # ===========================================================================
  
  agent-generator:
    build:
      context: ./services/agent-generator
      dockerfile: Dockerfile
    image: laias/agent-generator:latest
    container_name: laias-agent-generator
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql+asyncpg://laias:laias_secure_password@postgres:5432/laias
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DEFAULT_LLM_PROVIDER=${DEFAULT_LLM_PROVIDER:-openai}
      - DEFAULT_MODEL=${DEFAULT_MODEL:-gpt-4o}
      - SERVICE_PORT=8001
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - laias-network

  docker-orchestrator:
    build:
      context: ./services/docker-orchestrator
      dockerfile: Dockerfile
    image: laias/docker-orchestrator:latest
    container_name: laias-docker-orchestrator
    ports:
      - "8002:8002"
    environment:
      - DATABASE_URL=postgresql+asyncpg://laias:laias_secure_password@postgres:5432/laias
      - REDIS_URL=redis://redis:6379/1
      - DOCKER_HOST=unix:///var/run/docker.sock
      - AGENT_IMAGE_BASE=laias/agent-runner:latest
      - AGENT_CODE_PATH=/var/laias/agents
      - SERVICE_PORT=8002
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      # CRITICAL: Access host Docker socket for sibling container spawning
      - /var/run/docker.sock:/var/run/docker.sock
      # Store generated agent code (mounted into spawned containers)
      - agent_code:/var/laias/agents
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - laias-network

  # ===========================================================================
  # FRONTEND SERVICES
  # ===========================================================================
  
  studio-ui:
    build:
      context: ./frontend/studio-ui
      dockerfile: Dockerfile
    image: laias/studio-ui:latest
    container_name: laias-studio-ui
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_AGENT_GENERATOR_URL=http://localhost:8001
      - NEXT_PUBLIC_DOCKER_ORCHESTRATOR_URL=http://localhost:8002
    depends_on:
      - agent-generator
      - docker-orchestrator
    networks:
      - laias-network

  control-room:
    build:
      context: ./frontend/control-room
      dockerfile: Dockerfile
    image: laias/control-room:latest
    container_name: laias-control-room
    ports:
      - "3001:3001"
    environment:
      - NEXT_PUBLIC_DOCKER_ORCHESTRATOR_URL=http://localhost:8002
    depends_on:
      - docker-orchestrator
    networks:
      - laias-network

networks:
  laias-network:
    driver: bridge
    name: laias-network

volumes:
  postgres_data:
    name: laias-postgres-data
  redis_data:
    name: laias-redis-data
  agent_code:
    name: laias-agent-code
```

---

### 1.3 Agent Runner Base Image

**WHAT**: Pre-built Docker image containing all dependencies for running generated agents.

**WHY**: The "No-Build" strategy requires a single base image with all CrewAI dependencies pre-installed. Agent code is mounted as a volume, enabling instant (<1 second) deployments.

**DEPENDENCIES**: Docker Compose Base

**INTEGRATION POINTS**:
- Docker Orchestrator spawns containers using this image
- Generated agent code mounted at `/app/agent/`
- Environment variables passed for configuration

#### Technical Specification

**File**: `/home/ubuntu/laias/Dockerfile.agent-runner`

```dockerfile
# =============================================================================
# LAIAS Agent Runner - Pre-Built Base Image
# =============================================================================
# 
# This image is built ONCE and reused for ALL agent deployments.
# Generated agent code is mounted as volumes - NOT baked into the image.
#
# Build command:
#   docker build -f Dockerfile.agent-runner -t laias/agent-runner:latest .
#
# Usage (by Docker Orchestrator):
#   docker run -v /var/laias/agents/deploy_xyz:/app/agent:ro \
#              -e TASK_ID=task_123 \
#              -e OPENAI_API_KEY=sk-... \
#              laias/agent-runner:latest
#
# =============================================================================

FROM python:3.11-slim

LABEL maintainer="LAIAS Platform"
LABEL description="Pre-built agent runner with CrewAI and dependencies"
LABEL version="1.0"

# ---------------------------------------------------------------------------
# System Dependencies
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ---------------------------------------------------------------------------
# Python Dependencies
# All packages needed by any generated agent are pre-installed here
# ---------------------------------------------------------------------------
WORKDIR /app

# Core CrewAI and agent dependencies
RUN pip install --no-cache-dir \
    # CrewAI framework
    "crewai[tools]>=0.80.0" \
    # Data processing
    "pandas>=2.0.0" \
    "numpy>=1.24.0" \
    # API and web
    "fastapi>=0.109.0" \
    "uvicorn>=0.27.0" \
    "httpx>=0.26.0" \
    "aiohttp>=3.9.0" \
    "aiofiles>=23.0.0" \
    # Data validation
    "pydantic>=2.5.0" \
    "pydantic-settings>=2.1.0" \
    # Logging and monitoring
    "structlog>=24.0.0" \
    "python-json-logger>=2.0.0" \
    # Utilities
    "python-dotenv>=1.0.0" \
    "tenacity>=8.2.0" \
    "PyYAML>=6.0.0" \
    # Visualization (for data agents)
    "plotly>=5.18.0" \
    "matplotlib>=3.8.0" \
    # Web scraping tools
    "beautifulsoup4>=4.12.0" \
    "lxml>=5.0.0" \
    "selenium>=4.15.0" \
    # LLM providers
    "openai>=1.12.0" \
    "anthropic>=0.18.0"

# ---------------------------------------------------------------------------
# Directory Structure
# ---------------------------------------------------------------------------
# /app/agent/ is where generated code gets mounted
RUN mkdir -p /app/agent /app/outputs /app/logs

# ---------------------------------------------------------------------------
# Runtime Configuration
# ---------------------------------------------------------------------------
WORKDIR /app/agent

# Default environment variables (can be overridden at runtime)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV LOG_LEVEL=INFO
ENV VERBOSE=true
ENV MEMORY_ENABLED=true

# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import crewai; print('healthy')" || exit 1

# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------
# Default: run flow.py that gets mounted at /app/agent/flow.py
CMD ["python", "flow.py"]
```

---

### 1.4 Redis Configuration

**WHAT**: Redis instance for task queuing, caching, and real-time pub/sub.

**WHY**: Redis provides fast in-memory data storage for:
- Task queues (agent generation requests, deployment requests)
- Caching (generated code, validation results)
- Pub/sub (real-time log streaming, status updates)

**DEPENDENCIES**: Docker Compose Base

**INTEGRATION POINTS**:
- Agent Generator API: queues generation requests, caches results
- Docker Orchestrator: queues deployment requests, publishes status updates
- Control Room: subscribes to real-time updates

#### Technical Specification

Redis configuration is included in Docker Compose. Additional configuration for production:

**File**: `/home/ubuntu/laias/infrastructure/redis.conf`

```conf
# =============================================================================
# LAIAS Redis Configuration
# =============================================================================

# Memory management
maxmemory 256mb
maxmemory-policy allkeys-lru

# Persistence
appendonly yes
appendfsync everysec
save 900 1
save 300 10
save 60 10000

# Security (set in production)
# requirepass your_secure_password

# Logging
loglevel notice
logfile ""

# Performance
tcp-keepalive 300
timeout 0

# Pub/Sub for real-time updates
notify-keyspace-events Ex
```

---

## Phase 2: Core Services

### 2.1 Agent Generator API

**WHAT**: FastAPI service that uses LLMs to generate production-ready CrewAI agent code from natural language descriptions.

**WHY**: This is the core intelligence of LAIAS—transforming user intent into executable agent code that follows the Godzilla architectural pattern.

**DEPENDENCIES**:
- Database Schema (stores generated agents)
- Redis (caches responses, queues requests)

**INTEGRATION POINTS**:
- Studio UI calls `/api/generate-agent` and `/api/validate-code`
- Integration Layer provides typed client for API access
- Generated code deployed via Docker Orchestrator

#### Project Structure

```
services/agent-generator/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry
│   ├── config.py               # Environment configuration
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── generate.py     # POST /api/generate-agent
│   │   │   ├── validate.py     # POST /api/validate-code
│   │   │   ├── agents.py       # CRUD for saved agents
│   │   │   └── health.py       # GET /health
│   │   └── dependencies.py     # Shared dependencies
│   ├── services/
│   │   ├── __init__.py
│   │   ├── llm_service.py      # OpenAI/Anthropic integration
│   │   ├── code_generator.py   # Code generation logic
│   │   ├── template_service.py # Godzilla template management
│   │   └── validator.py        # Code validation
│   ├── models/
│   │   ├── __init__.py
│   │   ├── requests.py         # Pydantic request schemas
│   │   ├── responses.py        # Pydantic response schemas
│   │   └── database.py         # SQLAlchemy models
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── system_prompts.py   # LLM system prompts
│   │   ├── few_shot_examples.py # Example generations
│   │   └── godzilla_template.py # Reference pattern
│   └── utils/
│       ├── __init__.py
│       ├── code_parser.py      # AST parsing
│       └── exceptions.py       # Custom exceptions
├── tests/
│   ├── __init__.py
│   ├── test_generate.py
│   ├── test_validate.py
│   └── conftest.py
├── requirements.txt
├── Dockerfile
└── .env.example
```

#### API Specifications

##### POST /api/generate-agent

Generates CrewAI agent code from natural language description.

**Request Schema:**
```python
class GenerateAgentRequest(BaseModel):
    description: str = Field(
        ..., 
        min_length=10, 
        max_length=5000, 
        description="Natural language description of the agent"
    )
    agent_name: str = Field(
        ..., 
        pattern="^[a-zA-Z][a-zA-Z0-9_]*$", 
        description="Valid Python class name for the flow"
    )
    complexity: Literal["simple", "moderate", "complex"] = Field(
        default="moderate",
        description="Complexity level affecting agent count and flow structure"
    )
    task_type: Literal["research", "development", "analysis", "automation", "general"] = Field(
        default="general",
        description="Primary task category for optimized generation"
    )
    tools_requested: Optional[List[str]] = Field(
        default=None, 
        description="Specific tools to include (SerperDevTool, ScrapeWebsiteTool, etc.)"
    )
    llm_provider: Literal["openai", "anthropic"] = Field(
        default="openai"
    )
    model: Optional[str] = Field(
        default=None, 
        description="Specific model override (gpt-4o, claude-3-5-sonnet, etc.)"
    )
    include_memory: bool = Field(
        default=True,
        description="Enable agent memory for context retention"
    )
    include_analytics: bool = Field(
        default=True,
        description="Include AnalyticsService for monitoring"
    )
    max_agents: int = Field(
        default=4, 
        ge=1, 
        le=10,
        description="Maximum number of specialized agents to create"
    )
```

**Response Schema:**
```python
class GeneratedAgentResponse(BaseModel):
    agent_id: str = Field(description="Unique identifier for this generation")
    agent_name: str
    
    # Generated code (Godzilla pattern)
    flow_code: str = Field(description="Complete flow.py content")
    agents_yaml: str = Field(description="agents.yaml configuration")
    state_class: str = Field(description="AgentState class definition")
    
    # Dependencies
    requirements: List[str] = Field(description="Python packages needed")
    
    # Metadata
    estimated_cost_per_run: float = Field(description="Estimated LLM cost in USD")
    complexity_score: int = Field(ge=1, le=10)
    
    # Agent details
    agents_created: List[AgentInfo]
    tools_included: List[str]
    
    # Visualization
    flow_diagram: Optional[str] = Field(description="Mermaid diagram of the flow")
    
    # Validation
    validation_status: ValidationResult
    
    created_at: datetime

class AgentInfo(BaseModel):
    role: str
    goal: str
    tools: List[str]
    llm_config: Dict[str, Any]

class ValidationResult(BaseModel):
    is_valid: bool
    syntax_errors: List[str]
    pattern_compliance: float  # 0.0 to 1.0
    warnings: List[str]
```

##### POST /api/validate-code

Validates Python code against the Godzilla pattern.

**Request:**
```python
class ValidateCodeRequest(BaseModel):
    code: str = Field(..., description="Python code to validate")
    check_pattern_compliance: bool = Field(default=True)
```

**Response:**
```python
class ValidateCodeResponse(BaseModel):
    is_valid: bool
    syntax_errors: List[str]
    pattern_compliance_score: float
    missing_patterns: List[str]
    suggestions: List[str]
```

##### GET /health

Returns service health status.

**Response:**
```python
class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    llm_status: Dict[str, str]  # {"openai": "ok", "anthropic": "ok"}
    database_status: str
    uptime_seconds: float
```

#### Core Implementation

**File**: `app/services/llm_service.py`

```python
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog
from typing import Optional, Dict, Any

from app.config import settings
from app.prompts.system_prompts import SYSTEM_PROMPT
from app.prompts.few_shot_examples import FEW_SHOT_SELECTOR

logger = structlog.get_logger()


class LLMService:
    """Service for LLM-powered code generation."""
    
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_agent_code(
        self,
        description: str,
        agent_name: str,
        complexity: str,
        task_type: str,
        tools_requested: Optional[list] = None,
        provider: str = "openai",
        model: Optional[str] = None,
        include_memory: bool = True,
        include_analytics: bool = True,
        max_agents: int = 4
    ) -> Dict[str, Any]:
        """
        Generate agent code using LLM with few-shot prompting.
        
        Returns dict with:
        - flow_code: Complete Python code
        - state_class: Pydantic state definition
        - agents_yaml: YAML configuration
        - requirements: List of pip packages
        - flow_diagram: Mermaid diagram
        - agents_info: List of agent details
        """
        
        # Build prompts
        system_prompt = SYSTEM_PROMPT
        few_shot_examples = FEW_SHOT_SELECTOR.get_examples(complexity, task_type)
        user_prompt = self._build_user_prompt(
            description=description,
            agent_name=agent_name,
            complexity=complexity,
            task_type=task_type,
            tools_requested=tools_requested,
            include_memory=include_memory,
            include_analytics=include_analytics,
            max_agents=max_agents
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            *few_shot_examples,
            {"role": "user", "content": user_prompt}
        ]
        
        logger.info(
            "Generating agent code",
            provider=provider,
            complexity=complexity,
            task_type=task_type
        )
        
        if provider == "openai":
            return await self._call_openai(messages, model or "gpt-4o")
        else:
            return await self._call_anthropic(messages, model or "claude-3-5-sonnet-20241022")
    
    async def _call_openai(self, messages: list, model: str) -> Dict[str, Any]:
        """Call OpenAI API with structured output."""
        response = await self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=8000,
            response_format={"type": "json_object"}
        )
        return self._parse_response(response.choices[0].message.content)
    
    async def _call_anthropic(self, messages: list, model: str) -> Dict[str, Any]:
        """Call Anthropic API with structured output."""
        system = messages[0]["content"]
        conversation = messages[1:]
        
        response = await self.anthropic_client.messages.create(
            model=model,
            max_tokens=8000,
            system=system,
            messages=conversation
        )
        return self._parse_response(response.content[0].text)
    
    def _build_user_prompt(
        self,
        description: str,
        agent_name: str,
        complexity: str,
        task_type: str,
        tools_requested: Optional[list],
        include_memory: bool,
        include_analytics: bool,
        max_agents: int
    ) -> str:
        """Build the user prompt for code generation."""
        tools_str = ", ".join(tools_requested) if tools_requested else "auto-select based on task"
        
        return f"""
Generate a production-ready CrewAI agent flow based on this specification:

**Agent Name:** {agent_name}
**Description:** {description}
**Complexity Level:** {complexity}
**Task Type:** {task_type}
**Requested Tools:** {tools_str}
**Max Agents:** {max_agents}
**Include Memory:** {include_memory}
**Include Analytics:** {include_analytics}

Generate the complete implementation following the Godzilla architectural pattern EXACTLY.

Return a JSON object with these keys:
- flow_code: Complete, runnable Python code for the flow class
- state_class: The AgentState class definition (Pydantic BaseModel)
- agents_yaml: YAML configuration for all agents
- requirements: List of pip packages needed (crewai[tools], pydantic, structlog, etc.)
- flow_diagram: Mermaid diagram showing the flow transitions
- agents_info: List of objects with role, goal, tools, llm_config for each agent
"""
    
    def _parse_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM response into structured data."""
        import json
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            raise ValueError(f"Invalid JSON response from LLM: {e}")
```

**File**: `app/services/validator.py`

```python
import ast
import re
from typing import Tuple, List

import structlog

logger = structlog.get_logger()


class CodeValidator:
    """Validate generated code against the Godzilla pattern."""
    
    REQUIRED_PATTERNS = [
        (r"class \w+\(Flow\[", "Must use Flow[AgentState] base class"),
        (r"@start\(\)", "Must have @start() decorated entry point"),
        (r"@listen\(", "Must have @listen() event-driven methods"),
        (r"class \w+State\(BaseModel\)", "Must define typed state class with BaseModel"),
        (r"def _create_\w+_agent\(self\)", "Must have agent factory methods"),
        (r"try:", "Must include error handling (try/except)"),
        (r"logger\.", "Must use structlog logging"),
        (r"self\.state\.", "Must use typed state management"),
    ]
    
    RECOMMENDED_PATTERNS = [
        (r"@router\(", "Consider adding @router for conditional branching"),
        (r"@persist", "Consider adding @persist for state persistence"),
        (r"AnalyticsService", "Consider adding analytics for monitoring"),
        (r"async def", "Consider using async methods for better performance"),
    ]
    
    def validate(self, code: str) -> Tuple[bool, List[str], float, List[str]]:
        """
        Validate code against Godzilla pattern.
        
        Returns:
            Tuple of (is_valid, errors, compliance_score, warnings)
        """
        errors = []
        warnings = []
        
        # Step 1: Syntax validation
        try:
            ast.parse(code)
        except SyntaxError as e:
            return False, [f"Syntax error at line {e.lineno}: {e.msg}"], 0.0, []
        
        # Step 2: Required pattern compliance
        patterns_found = 0
        for pattern, error_msg in self.REQUIRED_PATTERNS:
            if re.search(pattern, code):
                patterns_found += 1
            else:
                errors.append(f"Missing required pattern: {error_msg}")
        
        # Step 3: Recommended patterns (warnings only)
        for pattern, warning_msg in self.RECOMMENDED_PATTERNS:
            if not re.search(pattern, code):
                warnings.append(warning_msg)
        
        # Calculate compliance score
        compliance_score = patterns_found / len(self.REQUIRED_PATTERNS)
        
        # Valid if no critical errors and compliance >= 80%
        is_valid = len(errors) == 0 or compliance_score >= 0.8
        
        logger.info(
            "Code validation complete",
            is_valid=is_valid,
            compliance_score=compliance_score,
            error_count=len(errors),
            warning_count=len(warnings)
        )
        
        return is_valid, errors, compliance_score, warnings
```

**File**: `app/prompts/system_prompts.py`

```python
SYSTEM_PROMPT = """You are an expert AI agent architect for the LAIAS (Legacy AI Agent Studio) platform.

Your role is to generate production-ready CrewAI agent code that EXACTLY follows the "Godzilla" architectural pattern.

## CRITICAL REQUIREMENTS - ALL code MUST include:

1. **Flow Architecture**: 
   - Use `Flow[AgentState]` with typed Pydantic state
   - Import from: `from crewai.flow.flow import Flow, listen, start, router, or_`

2. **Decorators** (REQUIRED):
   - `@start()` - Entry point method
   - `@listen("event_name")` - Event-driven transitions
   - `@router(method_name)` - Conditional branching
   - `@persist` - State persistence (from crewai.flow.persistence)

3. **State Class** (REQUIRED):
   - Extend `pydantic.BaseModel`
   - Include: task_id, status, error_count, progress, confidence
   - Add task-specific fields as needed

4. **Error Handling** (REQUIRED):
   - Wrap all operations in try/except
   - Track error_count in state
   - Include recovery paths via router

5. **Agent Factory Methods** (REQUIRED):
   - Create agents via `_create_[role]_agent(self) -> Agent`
   - Configure role, goal, backstory, tools, llm

6. **Logging** (REQUIRED):
   - Use structlog: `logger = structlog.get_logger()`
   - Log at key execution points

## OUTPUT FORMAT

Return a JSON object with these exact keys:
- flow_code: Complete, runnable Python code (no placeholders)
- state_class: The AgentState Pydantic model definition
- agents_yaml: YAML configuration for agents
- requirements: List of pip packages (e.g., ["crewai[tools]>=0.80.0", "pydantic>=2.5.0"])
- flow_diagram: Mermaid diagram showing flow transitions
- agents_info: Array of {role, goal, tools, llm_config} objects

## FLOW METHOD PATTERN

```python
@start()
async def initialize(self, inputs: Dict[str, Any]) -> AgentState:
    # Setup, validation, state initialization
    return self.state

@listen("initialize")
async def process(self, state: AgentState) -> AgentState:
    # Main processing with agents and crews
    return self.state

@router(process)
def decide_next(self) -> str:
    # Return event name based on state
    if self.state.error_count > 3:
        return "handle_errors"
    return "finalize"

@listen("finalize")
async def complete(self, state: AgentState) -> AgentState:
    # Final output generation
    return self.state

@listen(or_("handle_errors", "retry"))
async def recovery(self, state: AgentState) -> AgentState:
    # Error recovery logic
    return self.state
```

Generate code that is immediately runnable with zero modifications needed."""
```

#### Dockerfile

**File**: `services/agent-generator/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

**File**: `services/agent-generator/requirements.txt`

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0
openai==1.12.0
anthropic==0.18.0
sqlalchemy==2.0.25
asyncpg==0.29.0
redis==5.0.1
python-dotenv==1.0.0
httpx==0.26.0
tenacity==8.2.3
structlog==24.1.0
```

---

### 2.2 Docker Orchestrator Service

**WHAT**: FastAPI service managing Docker containers for deployed agents—lifecycle management, log streaming, and resource monitoring.

**WHY**: Provides the runtime environment for generated agents, abstracting Docker complexity from the user interface.

**DEPENDENCIES**:
- Database Schema (stores deployment records)
- Agent Runner Base Image (used for all containers)
- Redis (task queues, pub/sub for logs)

**INTEGRATION POINTS**:
- Studio UI triggers deployments via `/api/deploy`
- Control Room monitors via `/api/containers`, `/api/containers/{id}/logs`
- Agent containers are spawned as siblings via host Docker socket

#### Project Structure

```
services/docker-orchestrator/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── deploy.py       # POST /api/deploy
│   │   │   ├── containers.py   # Container CRUD
│   │   │   ├── logs.py         # Log streaming
│   │   │   └── health.py       # Health check
│   │   └── dependencies.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── docker_service.py   # Docker SDK wrapper
│   │   ├── container_manager.py # Lifecycle management
│   │   ├── log_streamer.py     # Real-time log streaming
│   │   └── resource_monitor.py # CPU/Memory monitoring
│   ├── models/
│   │   ├── __init__.py
│   │   ├── requests.py
│   │   ├── responses.py
│   │   └── database.py
│   └── utils/
│       ├── __init__.py
│       └── exceptions.py
├── tests/
├── requirements.txt
└── Dockerfile
```

#### API Specifications

##### POST /api/deploy

Deploy generated agent code to a new container.

**Request:**
```python
class DeployAgentRequest(BaseModel):
    agent_id: str = Field(..., description="ID from agent generator")
    agent_name: str = Field(..., description="Human-readable name")
    flow_code: str = Field(..., description="Generated Python code")
    agents_yaml: str = Field(..., description="Agent YAML configuration")
    requirements: List[str] = Field(default_factory=list)
    environment_vars: Dict[str, str] = Field(default_factory=dict)
    cpu_limit: float = Field(default=1.0, ge=0.1, le=4.0)
    memory_limit: str = Field(default="512m", pattern="^[0-9]+[mg]$")
    auto_start: bool = Field(default=True)
```

**Response:**
```python
class DeploymentResponse(BaseModel):
    deployment_id: str
    agent_id: str
    container_id: str
    container_name: str
    status: Literal["created", "starting", "running", "stopped", "error"]
    ports: Dict[str, int]
    created_at: datetime
    started_at: Optional[datetime]
    logs_endpoint: str  # WebSocket URL
    metrics_endpoint: str  # REST URL
```

##### GET /api/containers

List all agent containers.

**Response:**
```python
class ContainerListResponse(BaseModel):
    containers: List[ContainerInfo]
    total: int
    running: int
    stopped: int

class ContainerInfo(BaseModel):
    container_id: str
    deployment_id: str
    agent_id: str
    agent_name: str
    status: str
    cpu_usage: float
    memory_usage: str
    uptime_seconds: Optional[int]
    created_at: datetime
    last_activity: Optional[datetime]
```

##### POST /api/containers/{container_id}/start
##### POST /api/containers/{container_id}/stop
##### DELETE /api/containers/{container_id}

Container lifecycle operations.

##### GET /api/containers/{container_id}/logs

**Query Parameters:**
- `tail`: int (default 100)
- `since`: ISO datetime
- `level`: DEBUG|INFO|WARNING|ERROR

**Response:**
```python
class LogsResponse(BaseModel):
    container_id: str
    logs: List[LogEntry]
    has_more: bool

class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    message: str
    source: str
```

##### WebSocket /api/containers/{container_id}/logs/stream

Real-time log streaming via WebSocket.

##### GET /api/containers/{container_id}/metrics

**Response:**
```python
class MetricsResponse(BaseModel):
    container_id: str
    cpu_percent: float
    memory_usage_mb: float
    memory_limit_mb: float
    network_rx_bytes: int
    network_tx_bytes: int
    uptime_seconds: int
    timestamp: datetime
```

#### Core Implementation

**File**: `app/services/docker_service.py`

```python
import docker
from docker.models.containers import Container
from typing import Dict, Any, Optional, List
import structlog
import os
import aiofiles

from app.config import settings

logger = structlog.get_logger()


class DockerService:
    """
    Docker SDK wrapper implementing the No-Build deployment strategy.
    
    Key architecture:
    - Uses pre-built laias/agent-runner:latest image
    - Mounts generated code as volumes
    - Spawns containers as siblings via host socket
    """
    
    def __init__(self):
        self.client = docker.from_env()
        self.base_image = settings.AGENT_IMAGE_BASE
        self.code_path = settings.AGENT_CODE_PATH
        self.network = settings.DOCKER_NETWORK
    
    async def deploy_agent(
        self,
        deployment_id: str,
        agent_id: str,
        flow_code: str,
        agents_yaml: str,
        environment_vars: Dict[str, str],
        cpu_limit: float = 1.0,
        memory_limit: str = "512m"
    ) -> Container:
        """
        Deploy agent using volume mounting strategy.
        
        Steps:
        1. Write generated code to host filesystem
        2. Create container with code mounted as volume
        3. Start container
        """
        
        # Step 1: Write code to deployment directory
        deploy_dir = os.path.join(self.code_path, deployment_id)
        await self._write_agent_code(deploy_dir, flow_code, agents_yaml)
        
        # Step 2: Create container with volume mount
        container_name = f"laias-agent-{deployment_id[:12]}"
        
        container = self.client.containers.create(
            image=self.base_image,
            name=container_name,
            volumes={
                deploy_dir: {
                    'bind': '/app/agent',
                    'mode': 'ro'  # Read-only mount
                }
            },
            environment={
                'DEPLOYMENT_ID': deployment_id,
                'AGENT_ID': agent_id,
                **environment_vars
            },
            cpu_period=100000,
            cpu_quota=int(cpu_limit * 100000),
            mem_limit=memory_limit,
            network=self.network,
            detach=True,
            auto_remove=False
        )
        
        logger.info(
            "Container created",
            deployment_id=deployment_id,
            container_id=container.id,
            container_name=container_name
        )
        
        return container
    
    async def _write_agent_code(
        self,
        deploy_dir: str,
        flow_code: str,
        agents_yaml: str
    ) -> None:
        """Write generated code to deployment directory."""
        os.makedirs(deploy_dir, exist_ok=True)
        
        async with aiofiles.open(os.path.join(deploy_dir, 'flow.py'), 'w') as f:
            await f.write(flow_code)
        
        async with aiofiles.open(os.path.join(deploy_dir, 'agents.yaml'), 'w') as f:
            await f.write(agents_yaml)
        
        logger.info("Agent code written", deploy_dir=deploy_dir)
    
    def start_container(self, container_id: str) -> None:
        """Start a stopped container."""
        container = self.client.containers.get(container_id)
        container.start()
        logger.info("Container started", container_id=container_id)
    
    def stop_container(self, container_id: str, timeout: int = 10) -> None:
        """Stop a running container."""
        container = self.client.containers.get(container_id)
        container.stop(timeout=timeout)
        logger.info("Container stopped", container_id=container_id)
    
    def remove_container(self, container_id: str, force: bool = False) -> None:
        """Remove a container and its code directory."""
        container = self.client.containers.get(container_id)
        
        # Get deployment ID from container labels/env
        deployment_id = container.labels.get('deployment_id')
        
        container.remove(force=force)
        
        # Clean up code directory
        if deployment_id:
            deploy_dir = os.path.join(self.code_path, deployment_id)
            if os.path.exists(deploy_dir):
                import shutil
                shutil.rmtree(deploy_dir)
        
        logger.info("Container removed", container_id=container_id)
    
    def get_container_logs(
        self,
        container_id: str,
        tail: int = 100,
        since: Optional[str] = None
    ) -> List[str]:
        """Get container logs."""
        container = self.client.containers.get(container_id)
        logs = container.logs(
            tail=tail,
            since=since,
            timestamps=True
        )
        return logs.decode('utf-8').split('\n')
    
    def get_container_stats(self, container_id: str) -> Dict[str, Any]:
        """Get container resource statistics."""
        container = self.client.containers.get(container_id)
        stats = container.stats(stream=False)
        
        # Calculate CPU percentage
        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                   stats['precpu_stats']['cpu_usage']['total_usage']
        system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                      stats['precpu_stats']['system_cpu_usage']
        cpu_percent = (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0.0
        
        # Memory usage
        memory_usage = stats['memory_stats'].get('usage', 0)
        memory_limit = stats['memory_stats'].get('limit', 0)
        
        return {
            'cpu_percent': round(cpu_percent, 2),
            'memory_usage_mb': round(memory_usage / (1024 * 1024), 2),
            'memory_limit_mb': round(memory_limit / (1024 * 1024), 2),
            'network_rx_bytes': stats.get('networks', {}).get('eth0', {}).get('rx_bytes', 0),
            'network_tx_bytes': stats.get('networks', {}).get('eth0', {}).get('tx_bytes', 0)
        }
    
    def list_containers(self, all: bool = True) -> List[Dict[str, Any]]:
        """List all LAIAS agent containers."""
        containers = self.client.containers.list(
            all=all,
            filters={'name': 'laias-agent-'}
        )
        
        return [
            {
                'container_id': c.id,
                'name': c.name,
                'status': c.status,
                'created': c.attrs['Created']
            }
            for c in containers
        ]
```

**File**: `app/services/log_streamer.py`

```python
import asyncio
from typing import AsyncGenerator
import docker
import structlog
import json
from datetime import datetime

logger = structlog.get_logger()


class LogStreamer:
    """Real-time log streaming for containers."""
    
    def __init__(self):
        self.client = docker.from_env()
    
    async def stream_logs(
        self,
        container_id: str
    ) -> AsyncGenerator[dict, None]:
        """
        Stream logs from container as async generator.
        
        Yields log entries as dictionaries:
        {
            "timestamp": "2026-02-13T10:30:00Z",
            "level": "INFO",
            "message": "Starting execution...",
            "source": "flow"
        }
        """
        container = self.client.containers.get(container_id)
        
        # Stream logs with timestamps
        for line in container.logs(stream=True, follow=True, timestamps=True):
            try:
                decoded = line.decode('utf-8').strip()
                if decoded:
                    yield self._parse_log_line(decoded)
            except Exception as e:
                logger.warning(f"Failed to parse log line: {e}")
                continue
    
    def _parse_log_line(self, line: str) -> dict:
        """Parse a log line into structured format."""
        # Format: timestamp message
        parts = line.split(' ', 1)
        
        timestamp = parts[0] if len(parts) > 0 else datetime.utcnow().isoformat()
        message = parts[1] if len(parts) > 1 else line
        
        # Try to detect log level
        level = "INFO"
        for lvl in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            if lvl in message.upper():
                level = lvl
                break
        
        return {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "source": "container"
        }
```

---

## Phase 3: User Interfaces

### 3.1 Studio UI

**WHAT**: NextJS application providing the agent builder interface—form inputs, code editor, preview, and export functionality.

**WHY**: Users need an intuitive interface to describe agents, view generated code, make edits, and deploy. The Studio UI abstracts the complexity of code generation.

**DEPENDENCIES**:
- Agent Generator API (for code generation)
- Docker Orchestrator (for deployment)

**INTEGRATION POINTS**:
- Calls Agent Generator API `/api/generate-agent`
- Calls Docker Orchestrator `/api/deploy`
- Integration Layer provides typed API client

#### Project Structure

```
frontend/studio-ui/
├── app/
│   ├── page.tsx                # Home/landing
│   ├── layout.tsx              # Root layout
│   ├── globals.css             # Tailwind styles
│   ├── create/
│   │   └── page.tsx            # Agent builder
│   ├── agents/
│   │   ├── page.tsx            # Agent list
│   │   └── [id]/
│   │       └── page.tsx        # Agent detail/edit
│   └── api/
│       └── generate/
│           └── route.ts        # API proxy (optional)
├── components/
│   ├── ui/                     # Base components
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── select.tsx
│   │   ├── checkbox.tsx
│   │   ├── textarea.tsx
│   │   ├── card.tsx
│   │   └── tabs.tsx
│   ├── agent-builder/
│   │   ├── AgentForm.tsx       # Main form
│   │   ├── AgentTypeSelector.tsx
│   │   ├── ToolSelector.tsx
│   │   ├── AdvancedOptions.tsx
│   │   └── GenerateButton.tsx
│   ├── code-editor/
│   │   ├── CodeEditor.tsx      # Monaco wrapper
│   │   ├── CodeTabs.tsx
│   │   └── ValidationStatus.tsx
│   └── export/
│       ├── ExportPanel.tsx
│       └── DeployDialog.tsx
├── lib/
│   ├── api-client.ts           # API client
│   ├── types.ts                # TypeScript types
│   ├── schemas.ts              # Zod schemas
│   └── utils.ts
├── hooks/
│   ├── useAgentGenerator.ts
│   └── useDeployment.ts
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── Dockerfile
```

#### Key Components

**Agent Builder Form Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│                    CREATE NEW AGENT                          │
├─────────────────────────────────────────────────────────────┤
│ Agent Name: [________________________]                       │
│                                                              │
│ Agent Type: ○ Solo Agent  ○ Multi-Agent  ○ Swarm            │
│             ○ Research    ○ Assistant                        │
│                                                              │
│ Description:                                                 │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Describe what you want your agent to do...              │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                              │
│ Complexity: [Simple ▼]    Task Type: [Research ▼]           │
│                                                              │
│ Tools: ☑ Web Search  ☑ Web Scraper  ☐ Code Interpreter     │
│        ☐ File Reader ☐ Data Viz                              │
│                                                              │
│ ▼ Advanced Options                                           │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Max Agents: [4]  Memory: ☑  Analytics: ☑                │ │
│ │ LLM: [OpenAI ▼]  Model: [gpt-4o ▼]                      │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                              │
│              [Generate Agent Code]                           │
└─────────────────────────────────────────────────────────────┘
```

**Code Preview Panel Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ [flow.py] [agents.yaml] [requirements.txt]                   │
├─────────────────────────────────────────────────────────────┤
│ from crewai import Agent, Task, Crew                        │
│ from crewai.flow.flow import Flow, listen, start            │
│ ...                                                         │
├─────────────────────────────────────────────────────────────┤
│ ✅ Valid  │ Pattern Compliance: 95%                         │
│                                                              │
│ [Copy Code] [Download ZIP] [Deploy →]                       │
└─────────────────────────────────────────────────────────────┘
```

#### Implementation Example

**File**: `components/agent-builder/AgentForm.tsx`

```tsx
'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { AgentTypeSelector } from './AgentTypeSelector';
import { ToolSelector } from './ToolSelector';
import { AdvancedOptions } from './AdvancedOptions';
import { GenerateButton } from './GenerateButton';
import { useAgentGenerator } from '@/hooks/useAgentGenerator';

const agentFormSchema = z.object({
  agent_name: z.string()
    .min(1, 'Agent name is required')
    .regex(/^[a-zA-Z][a-zA-Z0-9_]*$/, 'Must be a valid Python identifier'),
  description: z.string()
    .min(10, 'Description must be at least 10 characters')
    .max(5000, 'Description must be less than 5000 characters'),
  complexity: z.enum(['simple', 'moderate', 'complex']),
  task_type: z.enum(['research', 'development', 'analysis', 'automation', 'general']),
  tools_requested: z.array(z.string()).optional(),
  llm_provider: z.enum(['openai', 'anthropic']),
  model: z.string().optional(),
  include_memory: z.boolean(),
  include_analytics: z.boolean(),
  max_agents: z.number().min(1).max(10),
});

type AgentFormData = z.infer<typeof agentFormSchema>;

interface AgentFormProps {
  onGenerated: (result: GeneratedAgent) => void;
}

export function AgentForm({ onGenerated }: AgentFormProps) {
  const { generate, isLoading, error } = useAgentGenerator();
  
  const form = useForm<AgentFormData>({
    resolver: zodResolver(agentFormSchema),
    defaultValues: {
      complexity: 'moderate',
      task_type: 'general',
      llm_provider: 'openai',
      include_memory: true,
      include_analytics: true,
      max_agents: 4,
    },
  });

  const onSubmit = async (data: AgentFormData) => {
    const result = await generate(data);
    if (result) {
      onGenerated(result);
    }
  };

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
      {/* Agent Name */}
      <div>
        <label className="block text-sm font-medium text-gray-700">
          Agent Name
        </label>
        <input
          {...form.register('agent_name')}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
          placeholder="MarketResearchFlow"
        />
        {form.formState.errors.agent_name && (
          <p className="mt-1 text-sm text-red-600">
            {form.formState.errors.agent_name.message}
          </p>
        )}
      </div>

      {/* Agent Type */}
      <AgentTypeSelector
        value={form.watch('task_type')}
        onChange={(value) => form.setValue('task_type', value)}
      />

      {/* Description */}
      <div>
        <label className="block text-sm font-medium text-gray-700">
          Description
        </label>
        <textarea
          {...form.register('description')}
          rows={4}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
          placeholder="Describe what you want your agent to do in natural language..."
        />
        {form.formState.errors.description && (
          <p className="mt-1 text-sm text-red-600">
            {form.formState.errors.description.message}
          </p>
        )}
      </div>

      {/* Complexity & Task Type */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Complexity
          </label>
          <select
            {...form.register('complexity')}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
          >
            <option value="simple">Simple (1-2 agents)</option>
            <option value="moderate">Moderate (2-4 agents)</option>
            <option value="complex">Complex (4+ agents)</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Task Type
          </label>
          <select
            {...form.register('task_type')}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
          >
            <option value="research">Research</option>
            <option value="development">Development</option>
            <option value="analysis">Analysis</option>
            <option value="automation">Automation</option>
            <option value="general">General</option>
          </select>
        </div>
      </div>

      {/* Tool Selection */}
      <ToolSelector
        selected={form.watch('tools_requested') || []}
        onChange={(tools) => form.setValue('tools_requested', tools)}
      />

      {/* Advanced Options */}
      <AdvancedOptions form={form} />

      {/* Error Display */}
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Generate Button */}
      <GenerateButton isLoading={isLoading} />
    </form>
  );
}
```

**File**: `lib/api-client.ts`

```typescript
import { GenerateAgentRequest, GeneratedAgent, DeployRequest, DeploymentResponse } from './types';

const AGENT_GENERATOR_URL = process.env.NEXT_PUBLIC_AGENT_GENERATOR_URL || 'http://localhost:8001';
const DOCKER_ORCHESTRATOR_URL = process.env.NEXT_PUBLIC_DOCKER_ORCHESTRATOR_URL || 'http://localhost:8002';

export const apiClient = {
  async generateAgent(request: GenerateAgentRequest): Promise<GeneratedAgent> {
    const response = await fetch(`${AGENT_GENERATOR_URL}/api/generate-agent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Generation failed');
    }
    
    return response.json();
  },

  async validateCode(code: string): Promise<ValidationResult> {
    const response = await fetch(`${AGENT_GENERATOR_URL}/api/validate-code`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, check_pattern_compliance: true }),
    });
    
    if (!response.ok) {
      throw new Error('Validation failed');
    }
    
    return response.json();
  },

  async deployAgent(request: DeployRequest): Promise<DeploymentResponse> {
    const response = await fetch(`${DOCKER_ORCHESTRATOR_URL}/api/deploy`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Deployment failed');
    }
    
    return response.json();
  },

  async getContainers(): Promise<ContainerListResponse> {
    const response = await fetch(`${DOCKER_ORCHESTRATOR_URL}/api/containers`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch containers');
    }
    
    return response.json();
  },
};
```

---

### 3.2 Control Room Dashboard

**WHAT**: NextJS application for monitoring deployed agents—real-time status, log streaming, and resource metrics.

**WHY**: Operations teams need visibility into running agents, the ability to view logs in real-time, and tools to manage container lifecycle.

**DEPENDENCIES**:
- Docker Orchestrator (all monitoring APIs)

**INTEGRATION POINTS**:
- REST API for container status and metrics
- WebSocket for real-time log streaming
- Container lifecycle actions (start/stop/remove)

#### Project Structure

```
frontend/control-room/
├── app/
│   ├── page.tsx                # Dashboard home
│   ├── layout.tsx
│   ├── globals.css
│   ├── containers/
│   │   ├── page.tsx            # Container list
│   │   └── [id]/
│   │       ├── page.tsx        # Container detail
│   │       └── logs/
│   │           └── page.tsx    # Log viewer
│   └── metrics/
│       └── page.tsx            # System metrics
├── components/
│   ├── dashboard/
│   │   ├── ContainerGrid.tsx
│   │   ├── ContainerCard.tsx
│   │   ├── StatusBadge.tsx
│   │   └── QuickStats.tsx
│   ├── logs/
│   │   ├── LogViewer.tsx
│   │   ├── LogEntry.tsx
│   │   └── LogFilters.tsx
│   ├── metrics/
│   │   ├── ResourceChart.tsx
│   │   └── MetricsPanel.tsx
│   └── actions/
│       ├── ContainerActions.tsx
│       └── ConfirmDialog.tsx
├── lib/
│   ├── api-client.ts
│   ├── websocket.ts
│   └── types.ts
├── hooks/
│   ├── useContainers.ts
│   ├── useLogStream.ts
│   └── useMetrics.ts
└── Dockerfile
```

#### Key Features

1. **Container Grid View**: Visual cards showing all deployed agents
2. **Real-time Status**: Live updates via polling or WebSocket
3. **Log Streaming**: WebSocket-based real-time log viewer
4. **Resource Metrics**: CPU, memory, network usage charts
5. **Lifecycle Actions**: Start, stop, restart, remove containers

---

## Phase 4: Integration & Deployment

### 4.1 Integration Layer

**WHAT**: Shared TypeScript library providing type-safe API clients and common utilities.

**WHY**: Ensures consistency between frontend applications and provides a single source of truth for API contracts.

**DEPENDENCIES**: All APIs

**INTEGRATION POINTS**: Used by Studio UI and Control Room

#### Structure

```
packages/integration/
├── src/
│   ├── index.ts
│   ├── clients/
│   │   ├── agent-generator.ts
│   │   └── docker-orchestrator.ts
│   ├── types/
│   │   ├── agent.ts
│   │   ├── deployment.ts
│   │   └── common.ts
│   └── utils/
│       ├── errors.ts
│       └── validators.ts
├── package.json
└── tsconfig.json
```

### 4.2 End-to-End Testing

**WHAT**: Comprehensive test suite validating the complete workflow.

**WHY**: Ensures all components work together correctly before deployment.

**Test Scenarios:**

1. **Generation Flow**
   - Submit description → Receive valid code
   - Validation returns compliance score ≥ 0.9
   
2. **Deployment Flow**
   - Deploy generated code → Container starts
   - Logs accessible via WebSocket
   
3. **Lifecycle Management**
   - Stop/start/remove containers
   - State persists correctly

---

## Phase 5: Advanced Features

### Future Enhancements

| Feature | Description | Priority |
|---------|-------------|----------|
| Agent Templates | Pre-built configurations for common use cases | High |
| Team Collaboration | Multi-user access with roles | Medium |
| Version Control | Track changes to agent definitions | Medium |
| Cost Analytics | Detailed usage and billing reports | High |
| Custom Tools | User-defined tool integration | Low |
| Agent Marketplace | Share and discover agents | Low |

---

## API Reference

### Agent Generator API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/generate-agent` | POST | Generate agent code from description |
| `/api/validate-code` | POST | Validate code against Godzilla pattern |
| `/api/agents` | GET | List saved agents |
| `/api/agents/{id}` | GET | Get agent by ID |
| `/api/agents/{id}` | PUT | Update agent |
| `/api/agents/{id}` | DELETE | Delete agent |
| `/health` | GET | Service health check |

### Docker Orchestrator API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/deploy` | POST | Deploy agent to container |
| `/api/containers` | GET | List all containers |
| `/api/containers/{id}` | GET | Get container details |
| `/api/containers/{id}` | DELETE | Remove container |
| `/api/containers/{id}/start` | POST | Start container |
| `/api/containers/{id}/stop` | POST | Stop container |
| `/api/containers/{id}/logs` | GET | Get container logs |
| `/api/containers/{id}/logs/stream` | WS | Stream logs real-time |
| `/api/containers/{id}/metrics` | GET | Get resource metrics |
| `/health` | GET | Service health check |

---

## Testing Requirements

### Unit Tests

Each service must have ≥80% code coverage.

### Integration Tests

```python
# Example: Test generation and deployment flow
async def test_generate_and_deploy():
    # 1. Generate agent
    gen_response = await client.post("/api/generate-agent", json={
        "description": "Research AI trends",
        "agent_name": "AITrendsFlow",
        "complexity": "simple"
    })
    assert gen_response.status_code == 200
    agent = gen_response.json()
    assert agent["validation_status"]["is_valid"] == True
    
    # 2. Deploy agent
    deploy_response = await client.post("/api/deploy", json={
        "agent_id": agent["agent_id"],
        "agent_name": agent["agent_name"],
        "flow_code": agent["flow_code"],
        "agents_yaml": agent["agents_yaml"]
    })
    assert deploy_response.status_code == 200
    deployment = deploy_response.json()
    assert deployment["status"] in ["starting", "running"]
```

### Performance Benchmarks

| Operation | Target |
|-----------|--------|
| Code Generation | < 30 seconds |
| Container Deployment | < 2 seconds |
| Log Streaming Latency | < 500ms |
| API Response Time | < 200ms |

---

## Reference Documents

| Document | Purpose |
|----------|---------|
| `/home/ubuntu/LAIAS_MASTER_PLAN.md` | Project overview and architecture |
| `/home/ubuntu/GODZILLA_TEMPLATE.py` | Gold standard agent implementation |
| `/home/ubuntu/LAIAS_BUILD_GUIDE.md` | This document - technical specifications |

---

*This document provides complete technical specifications. For project overview, see LAIAS_MASTER_PLAN.md.*
