# ZAI API Configuration - Verified Working

**Date:** 2026-02-24
**Author:** FLOYD v4.0.0
**Status:** VERIFIED WORKING

---

## Working Configuration

```python
url = "https://api.z.ai/api/paas/v4/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}
payload = {
    "model": "GLM-4-Plus",  # Exact case required
    "messages": [{"role": "user", "content": "Your message"}],
    "temperature": 0.2,  # Max 0.2 as per user requirement
    "max_tokens": 4096,
    "thinking": {"type": "disabled"}  # REQUIRED - otherwise content is empty
}
```

---

## Model Options

### Complete ZAI Model Inventory (Plan-Wide Concurrency)

All concurrency limits are **plan-wide** — shared across every session, agent, and tool
using the same ZAI account. Over-subscribing any model starves all other callers.

**Language Models:**

| Model | Concurrency | Role | Notes |
|-------|-------------|------|-------|
| `GLM-5` | 5 | **Primary orchestrator / builder** | Highest reasoning. MUST disable thinking mode (see warning below). |
| `GLM-4-Plus` | 20 | **Worker only** | Fast but lacks reasoning depth. Cannot orchestrate. See concurrency warning below. |
| `GLM-4.7` | 3 | Complex reasoning | Strong reasoning, low concurrency. |
| `GLM-4.7-Flash` | 1 | Fast inference | Single concurrent only — do not use for parallel workloads. |
| `GLM-4.7-FlashX` | 3 | Fast inference (extended) | Slightly better concurrency than Flash. |
| `GLM-4.6` | 3 | General purpose | Mid-tier. |
| `GLM-4.6V` | 10 | Vision (multimodal) | Language + image input. |
| `GLM-4.6V-Flash` | 1 | Vision (fast, light) | Single concurrent only. |
| `GLM-4.6V-FlashX` | 3 | Vision (fast) | Faster vision variant. |
| `GLM-4.5` | 10 | Simple/routine tasks | Higher concurrency, cheap for low-complexity work. |
| `GLM-4.5V` | 10 | Vision (4.5 generation) | Multimodal, higher concurrency. |
| `GLM-4.5-Air` | 5 | Lightweight general | Mid-concurrency, lighter than 4.5. |
| `GLM-4.5-AirX` | 5 | Lightweight general (extended) | Same concurrency as Air. |
| `GLM-4.5-Flash` | 2 | Fast 4.5 variant | Low concurrency — minimal parallel use. |
| `AutoGLM-Phone-Multilingual` | 5 | Phone/multilingual automation | Specialized agent model. |

**Image Generation Models:**

| Model | Concurrency | Notes |
|-------|-------------|-------|
| `GLM-Image` | 1 | Single concurrent only. |

---

## ⚠️ CRITICAL: GLM-5 Thinking Mode = Catastrophic Failure

**GLM-5 already has a reasoning/thinking layer injected at the ZAI endpoint level.** The model
arrives pre-loaded with chain-of-thought reasoning built into the API layer itself.

If you enable `"thinking": {"type": "enabled"}` on top of this, you are adding a **second
reasoning layer on top of the first**. This creates a double-thinking loop that overwhelms
the model with so much internal deliberation that it becomes unable to produce any actionable
output. The model effectively paralyzes itself.

**This is not a degradation — it is a total failure mode. The model will return empty or
unusable responses 100% of the time.**

```python
# CORRECT — GLM-5
"thinking": {"type": "disabled"}  # Let the endpoint's built-in reasoning layer work alone

# CATASTROPHIC — GLM-5 (NEVER DO THIS)
"thinking": {"type": "enabled"}   # Double reasoning layer → model paralysis → empty output
```

This applies to ALL GLM-5 calls through the ZAI `/api/paas/v4` endpoint. No exceptions.

---

## ⚠️ GLM-4-Plus: Worker Only — Not an Orchestrator

GLM-4-Plus is fast but **does not have sufficient reasoning capability** to serve as a
primary builder or orchestrator.

**Use GLM-4-Plus for:**
- Well-defined, directed tasks with clear instructions
- Headless worker roles where each worker handles one specific, isolated task
- Simple generation, formatting, and transformation tasks

**Do NOT use GLM-4-Plus for:**
- Primary code generation / agent building
- Orchestrating multi-step workflows
- Tasks requiring significant reasoning or architectural decisions
- Any role where the model needs to "figure out" what to do

If you need orchestration-level reasoning, use GLM-5 (with thinking disabled) or an
external provider (OpenAI GPT-4o, Anthropic Claude).

---

## ⚠️ CRITICAL: ZAI Concurrency is Plan-Wide — Not Free

The 20 concurrent limit on GLM-4-Plus is the **maximum capacity across the entire ZAI
plan**, not a per-session resource. Every concurrent call counts against the same pool.

**This means:**
- GLM-5 only has **5 concurrent slots**. If other sessions or agents are using GLM-5,
  your orchestrator calls will queue or fail.
- Running 20 GLM-4-Plus workers consumes every slot on that model and competes for
  plan-wide resources. GLM-5 has its own pool of 5, but resource contention at the
  platform level still degrades everything.
- Other sessions using ZAI models (development, testing, other agents) share the same
  pools. Over-subscribing in one session crashes others.
- High concurrency causes **race conditions** unless each worker is headless, isolated,
  and directed at one specific non-overlapping task.

**Safe concurrency guidelines:**
- **GLM-5**: 5 slots total. Assume at least 1–2 are in use by other sessions.
  Realistically you have 2–3 available for any single workflow.
- **GLM-4-Plus**: 20 slots total, but **never deploy anywhere near 20.** Race conditions,
  cross-session starvation, and platform-level contention make this catastrophic.
  **Recommended maximum: 3–5 workers per session**, depending on what else is running.
- Each worker must be **headless** (no interactive output), **single-task** (one specific
  job), and **isolated** (operating in its own scope, away from other workers).
- Monitor plan usage before scaling — always assume other sessions are active.

---

## Critical Requirements

1. **Endpoint:** `https://api.z.ai/api/paas/v4` (NOT `/api/coding/paas/v4`)
2. **Model Name:** Exact case required — `GLM-5`, `GLM-4-Plus`, etc.
3. **Temperature:** Max 0.2
4. **Thinking MUST be disabled:** `"thinking": {"type": "disabled"}` — especially for GLM-5 which already has endpoint-level reasoning (see warning above)
5. **GLM-4-Plus is worker-only:** Do not use as primary orchestrator or builder

---

## Response Format

```json
{
  "choices": [
    {
      "finish_reason": "stop",
      "index": 0,
      "message": {
        "content": "The actual response text",
        "role": "assistant"
      }
    }
  ],
  "model": "GLM-4-Plus",
  "usage": {
    "completion_tokens": 5,
    "prompt_tokens": 10,
    "total_tokens": 15
  }
}
```

---

## Files Modified

- `/Volumes/Storage/LAIAS/services/agent-generator/app/services/llm_provider.py`
  - Changed `base_url` from `/api/coding/paas/v4` to `/api/paas/v4`
  - Changed `default_model` from `glm-5` to `GLM-4-Plus`
  
- `/Volumes/Storage/LAIAS/services/agent-generator/app/services/llm_service.py`
  - Changed default model mapping for ZAI from `glm-5` to `glm-4-plus`

---

## Test Command

```python
import httpx

api_key = "your-api-key"
url = "https://api.z.ai/api/paas/v4/chat/completions"
payload = {
    "model": "GLM-4-Plus",
    "messages": [{"role": "user", "content": "Say hello"}],
    "temperature": 0.2,
    "max_tokens": 20,
    "thinking": {"type": "disabled"}
}
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

with httpx.Client(timeout=30) as client:
    response = client.post(url, json=payload, headers=headers)
    print(response.json()["choices"][0]["message"]["content"])
```

---

## Cost Management

- Use `GLM-5` for orchestration and primary code generation (highest reasoning, thinking MUST be disabled)
- Use `GLM-4-Plus` for directed worker tasks only (high concurrency, low reasoning)
- Use `GLM-4.5` for simple/routine tasks (cheapest)
- Always use `temperature: 0.2` max
- Monitor token usage in `usage` field of response
