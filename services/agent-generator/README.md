# LAIAS Agent Generator Service

FastAPI service that uses LLMs to generate production-ready CrewAI agent code from natural language descriptions.

## Features

- LLM-powered code generation (OpenAI, Anthropic)
- Godzilla architectural pattern enforcement
- Code validation against best practices
- Agent CRUD operations
- Health and readiness checks

## Quick Start

### Local Development

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Run the service:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Docker

Build the image:
```bash
docker build -t laias/agent-generator:latest .
```

Run the container:
```bash
docker run -p 8001:8001 --env-file .env laias/agent-generator:latest
```

## API Endpoints

### POST /api/generate-agent

Generate a CrewAI agent from natural language.

**Request:**
```json
{
  "description": "Create a research agent that searches the web",
  "agent_name": "WebResearchFlow",
  "complexity": "moderate",
  "task_type": "research",
  "tools_requested": ["SerperDevTool", "ScrapeWebsiteTool"],
  "include_memory": true,
  "max_agents": 3
}
```

**Response:**
```json
{
  "agent_id": "gen_20260214_042255_abc123",
  "agent_name": "WebResearchFlow",
  "flow_code": "class WebResearchFlow(Flow[AgentState]): ...",
  "agents_yaml": "agents:\n  researcher:",
  "state_class": "class AgentState(BaseModel): ...",
  "requirements": ["crewai[tools]>=0.80.0", ...],
  "estimated_cost_per_run": 0.15,
  "complexity_score": 5,
  "agents_created": [...],
  "tools_included": ["SerperDevTool", "ScrapeWebsiteTool"],
  "flow_diagram": "graph TD\n    A[Start]",
  "validation_status": {
    "is_valid": true,
    "pattern_compliance": 0.95
  }
}
```

### POST /api/validate-code

Validate Python code against Godzilla pattern.

**Request:**
```json
{
  "code": "class MyFlow(Flow[AgentState]): ...",
  "check_pattern_compliance": true,
  "check_syntax": true
}
```

**Response:**
```json
{
  "is_valid": true,
  "syntax_errors": [],
  "pattern_compliance_score": 0.9,
  "missing_patterns": [],
  "suggestions": ["Consider adding @router() for conditional branching"]
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 123.45,
  "llm_status": {
    "openai": "ok",
    "anthropic": "ok"
  },
  "database_status": "ok",
  "redis_status": "ok"
}
```

## Testing

Run tests:
```bash
pytest tests/ -v
```

## License

MIT
