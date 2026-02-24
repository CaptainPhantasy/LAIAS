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

| Model | Concurrency | Notes |
|-------|-------------|-------|
| `GLM-4-Plus` | 20 concurrent | BEST - Use for LAIAS generation |
| `GLM-4.7` | 5 concurrent | Good for complex reasoning |
| `GLM-4.5` | Lower | Cheaper for simple tasks |

---

## Critical Requirements

1. **Endpoint:** `https://api.z.ai/api/paas/v4` (NOT `/api/coding/paas/v4`)
2. **Model Name:** `GLM-4-Plus` - exact case matters
3. **Temperature:** Max 0.2
4. **Thinking Disabled:** MUST include `"thinking": {"type": "disabled"}` or response content will be empty (goes to `reasoning_content` instead)

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

- Use `GLM-4.5` for simple/routine tasks (cheaper)
- Use `GLM-4-Plus` for complex generation (better concurrency)
- Always use `temperature: 0.2` max
- Monitor token usage in `usage` field of response
