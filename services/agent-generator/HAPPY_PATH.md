# Agent Generator Service - Happy Path & Failure Map

**Last Updated:** 2026-02-14
**Status:** Phase 3.3 - CrewAI Tools Integration

## Current Happy Path

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WHAT WORKS                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ ✓ Config Loading       .env resolved via absolute path                      │
│ ✓ Pydantic Settings    All API keys loaded into Settings model              │
│ ✓ Service Startup      uvicorn starts, routes registered                    │
│ ✓ Root Endpoint        GET / returns service info                           │
│ ✓ Health Endpoint      GET /health returns (degraded status)                │
│ ✓ Unit Tests           7/7 tests pass                                       │
│ ✓ Tools Registry       80 tools across 8 categories                         │
│ ✓ MCP Server Config    10 MCP servers configured                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Current Failure Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WHAT FAILS                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ ✗ LLM Generation       POST /api/generate-agent fails                       │
│ ✗ LLM Health Check     All providers report "API key not found"             │
│ ✗ Database             PostgreSQL connection error                           │
│ ✗ Redis                Redis connection error                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Root Cause Analysis

### Issue #1: Environment Variables Not Exported (CRITICAL)

**Symptom:** `LLMServiceException: API key not found for {provider}`

**Root Cause:**
```
pydantic-settings loads .env → Settings model fields (WORKS)
pydantic-settings does NOT → os.environ (PROBLEM)

LLMProvider._validate_config() calls os.getenv() → None
```

**Evidence:**
```python
# settings has the key
settings.ZAI_API_KEY  # "sk-..." ✓

# but os.environ doesn't
os.getenv("ZAI_API_KEY")  # None ✗
```

**Fix:** Load .env into os.environ at startup using python-dotenv

### Issue #2: Database Not Running

**Symptom:** `database_status: "error"` in health check

**Root Cause:** PostgreSQL service not started

**Fix:** Start PostgreSQL or use SQLite for development

### Issue #3: Redis Not Running

**Symptom:** `redis_status: "error"` in health check

**Root Cause:** Redis service not started

**Fix:** Start Redis or disable caching for development

## Provider Status Matrix

```
┌──────────────┬─────────────┬───────────────────┬──────────────┐
│ PROVIDER     │ KEY IN ENV  │ KEY IN SETTINGS   │ CAN CALL API │
├──────────────┼─────────────┼───────────────────┼──────────────┤
│ ZAI          │ ✗ NO        │ ✓ YES             │ ✗ NO         │
│ OpenAI       │ ✗ NO        │ ✓ YES             │ ✗ NO         │
│ Anthropic    │ ✗ NO        │ ✓ YES             │ ✗ NO         │
│ Portkey      │ ✗ NO        │ ✓ YES             │ ✗ NO         │
└──────────────┴─────────────┴───────────────────┴──────────────┘
```

## Fix Priority

1. **CRITICAL:** Export .env to os.environ at startup
2. **HIGH:** Start PostgreSQL or configure SQLite fallback
3. **MEDIUM:** Start Redis or disable caching
4. **LOW:** Enable docs in production (currently disabled)

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         REQUEST FLOW                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  POST /api/generate-agent                                                   │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐      ┌─────────────────┐                              │
│  │ generate.py     │ ───▶ │ llm_service.py  │                              │
│  │ (route handler) │      │ (orchestrator)  │                              │
│  └─────────────────┘      └────────┬────────┘                              │
│                                    │                                        │
│                                    ▼                                        │
│                           ┌─────────────────┐                              │
│                           │ llm_provider.py │ ◀── os.getenv() FAILS        │
│                           │ (HTTP client)   │                              │
│                           └─────────────────┘                              │
│                                    │                                        │
│                                    ▼                                        │
│                           ┌─────────────────┐                              │
│                           │ ZAI / OpenAI /  │                              │
│                           │ Anthropic API   │                              │
│                           └─────────────────┘                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```
