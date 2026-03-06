# Draft: Agent Output Persistence & Routing

## Research Findings

### CrewAI Native Output Mechanisms (LAIAS currently ignores ALL of these)

| Feature | What It Does | LAIAS Uses? |
|---------|-------------|-------------|
| `CrewOutput` | Returned by `crew.kickoff()` — `raw`, `pydantic`, `json_dict`, `tasks_output`, `token_usage` | ❌ Calls `str(result)` and loses structure |
| `TaskOutput` | Per-task results — `raw`, `pydantic`, `json_dict`, `agent`, `output_format`, `messages` | ❌ Never captured |
| `output_log_file` | Crew parameter for automatic file logging (JSON or text) | ❌ Not used |
| `task_callback` | Crew-level callback fired after each task with `TaskOutput` | ❌ Not used |
| `step_callback` | Crew-level callback fired after each agent step | ❌ Not used |
| `output_file` | Task-level file output for individual task results | ❌ Not used |
| `output_json` / `output_pydantic` | Task-level structured output | ❌ Not used |
| `crewai_event_bus` | 40+ typed events (CrewStarted/Completed, TaskStarted/Completed, LLMCall*, ToolUsage*) | ❌ Not used |
| `BaseEventListener` | Custom listener class for all events | ❌ Not used |
| `FileHandler` | Built-in file handler for JSON/text logging | ❌ Not used |
| `TaskOutputStorageHandler` | Built-in SQLite storage for task outputs (replay/audit) | ❌ Not used |
| `@persist` decorator | Flow state persistence across restarts | ✅ Used in godzilla_reference.py |
| `CrewStreamingOutput` | Real-time streaming chunks with task/agent context | ❌ Not used |

### What LAIAS Currently Does Instead

1. Agent code runs in Docker container, outputs to stdout/stderr
2. Docker daemon captures raw text with timestamps
3. LogStreamer parses raw lines with regex to guess level/source
4. WebSocket streams unstructured text to frontend
5. Frontend displays in log viewer, loses data when component unmounts
6. Nothing is persisted

### How the Industry Does It (Universal Pattern)

```
Agent Code
    ↓ (callbacks / event bus / decorators)
Structured Event Collector (in-process)
    ↓ (async batch flush)
Multi-Destination Router
    ├─ Database (structured query)
    ├─ Files (markdown/JSON archive)
    ├─ Cloud (S3, etc.)
    └─ Webhooks (Slack, etc.)
    ↓ (query API)
UI / Analytics
```

**Key principles all platforms share:**
1. Structured events, not raw logs (typed: TaskResult, LLMCall, ToolUse, Error)
2. Push from agent code via callbacks, not pull from stdout
3. Async batching to storage
4. Results separated from debug logs
5. Pluggable storage backends

### Platform-Specific Patterns

- **LangSmith**: Callback-based `_persist_run(Run)` with hierarchical parent-child traces
- **AutoGen**: JSONL file logging with typed events (LLM, ACTION, TOOL, ERROR)
- **Prefect**: `ResultStore` + `Artifact` system — typed outputs alongside task results
- **Dagster**: IOManager `handle_output()` / `load_input()` — automatic persistence of op returns
- **LangFuse**: Observation types (SPAN, GENERATION, EVENT, AGENT, TOOL) with trace hierarchy
- **AgentOps**: `@track_agent` decorator with event batching
- **Helicone**: Request/response logging with stream chunk capture

## The Critical Insight

LAIAS is **scraping stdout from opaque containers** when CrewAI already provides:
- Structured `CrewOutput` / `TaskOutput` objects
- A 40+ event type event bus
- Built-in file logging
- Callback hooks for every lifecycle event
- Streaming output with per-chunk metadata

## Open Questions

- [ ] Which approach: Modify generated agent code to use CrewAI callbacks? Or keep stdout capture and add persistence?
- [ ] Should we use CrewAI's event bus or task_callback (or both)?
- [ ] Which destinations are required: DB? Files? Webhooks? All?
- [ ] Should we modify the godzilla template to instrument agents with output capture?
- [ ] Per-deployment output config, or global?

## Decisions Made

1. **Core Approach**: Instrument agent code — modify Godzilla template + code generator to use CrewAI's native callbacks/event bus. Agents self-report structured output.
2. **Storage Destinations**: PostgreSQL (existing tables) + Markdown/JSON files on disk. No Redis streams or webhooks for now.
3. **Configuration Scope**: Per-deployment — each deployment specifies its output destinations.
4. **Note**: User mentioned "maybe MySQL" — LAIAS uses PostgreSQL (init.sql, docker-compose). Sticking with PostgreSQL.
5. **Instrumentation Depth**: Full event bus — use CrewAI's `crewai_event_bus` + `BaseEventListener` to capture ALL events (task lifecycle, LLM calls, tool usage, errors, crew lifecycle).
6. **File Output Format**: Structured directory — `/var/laias/outputs/{deployment_id}/{run_timestamp}/` with `summary.md`, `tasks.json`, `events.jsonl`, `metrics.json`.
7. **DB Schema**: Extend — add proper relational tables for task_results, llm_calls, tool_usage, crew_runs instead of stuffing into JSONB.
