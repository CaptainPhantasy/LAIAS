# PromptCacheManager

A prompt caching system that solves the "30% token waste" problem by implementing Anthropic-style ephemeral caching with 90% cost reduction.

## The Problem

Without prompt caching, long-running agentic projects face:
- **30% token waste** on re-reading context each session
- **Lossy summarization** that forgets project nuances
- **High latency** from re-processing 100k+ token contexts
- **Expensive restarts** after thinking pauses

## The Solution

Prompt caching "freezes" the state of project context so the model can pick up exactly where it left off for a **90% discount**.

## Three Core Patterns

### 1. Sliding Checkpoint Pattern

Place `cache_control` blocks on the **last Assistant message** at every turn:

```python
from prompt_cache_manager import PromptCacheManager

manager = PromptCacheManager()

messages = manager.build_messages_with_checkpoint(
    system_prompt="You are a coding assistant...",
    conversation_history=prior_messages,
    new_user_message="Continue fixing the auth bug",
)

# Result: All prior conversation cached at 10% cost
```

### 2. Static Prefix Rule

**CRITICAL**: Static content MUST come first. Dynamic content at the end.

```python
# ✅ CORRECT - Static first, dynamic last
request = manager.create_api_request(
    model="claude-sonnet-4-20250514",
    static_content={
        "codebase_structure": "...",  # Never changes
        "core_instructions": "...",   # Never changes
        "tool_definitions": "...",    # Never changes
    },
    dynamic_content={
        "current_time": "2026-02-17T09:00:00",  # Changes each request
        "task": "Fix auth bug",                   # Changes each request
    },
)

# ❌ WRONG - Would invalidate entire cache
# Don't put timestamps at the start of prompts!
```

If a **single character** changes at the start of the prompt, the entire 100k token cache is invalidated.

### 3. TTL Heartbeat Management

Anthropic's ephemeral cache expires after **5 minutes** of inactivity.

```python
# Heartbeat keeps cache alive automatically
manager = PromptCacheManager(
    enable_heartbeat=True,
    heartbeat_interval=240,  # 4 minutes (before 5-min TTL)
)

# Tiny heartbeat requests every 4 minutes prevent
# having to re-write the entire 100k+ token context
```

## Cost Comparison

| Feature | Summarization (Old) | Prompt Caching (New) |
|---------|---------------------|----------------------|
| Accuracy | Lossy (details vanish) | Perfect (raw data preserved) |
| Input Cost | 100% of tokens | 10% of tokens (after 1st write) |
| Latency | Slow (re-processing) | Up to 80% faster |
| Agent Behavior | "Forgets" nuances | Full "active memory" |

## Quick Start

```python
from prompt_cache_manager import PromptCacheManager, CacheTier

# Initialize with heartbeat
manager = PromptCacheManager(
    default_tier=CacheTier.EPHEMERAL,
    enable_heartbeat=True,
)

# Build cached request
request = manager.create_api_request(
    model="claude-sonnet-4-20250514",
    static_content={
        "project_context": "...",
        "instructions": "...",
    },
    dynamic_content={
        "task": "...",
        "timestamp": "...",
    },
    conversation_history=history,
)

# Send to API with caching enabled
response = client.messages.create(**request)

# View performance metrics
manager.print_dashboard()

# Cleanup when done
manager.shutdown()
```

## Cache Tiers

| Tier | TTL | Use Case |
|------|-----|----------|
| `EPHEMERAL` | 5 minutes | Active conversations, requires heartbeat |
| `SESSION` | 24 hours | Same-day project work |
| `PERSISTENT` | No expiry | Long-term project context |

## Dashboard Output

```
============================================================
          PROMPT CACHE MANAGER DASHBOARD
============================================================

  PERFORMANCE METRICS
  ─────────────────────────────────────
  Total Requests:      1,247
  Cache Hits:          1,180
  Cache Misses:        67
  Hit Rate:            94.63%

  TOKEN ECONOMICS
  ─────────────────────────────────────
  Tokens Cached:       523,400
  Tokens Read (10%):   489,200
  Tokens Written:      87,400
  Cost Saved:          $14.21
  Savings vs No-Cache: 87.3%

  CACHE HEALTH
  ─────────────────────────────────────
  Heartbeats Sent:     342
  Cache Invalidations: 3
  Last Heartbeat:      2026-02-17T08:55:42
============================================================
```

## API Reference

### `PromptCacheManager`

| Method | Description |
|--------|-------------|
| `build_messages_with_checkpoint()` | Build messages with cache_control blocks |
| `create_api_request()` | Create full API request following Static Prefix Rule |
| `get_or_create()` | Cache-aware content retrieval |
| `get_dashboard_data()` | Get metrics as dict |
| `print_dashboard()` | Print formatted dashboard |
| `shutdown()` | Clean shutdown (stops heartbeat) |

### `StaticPrefixManager`

Manages static content ordering for cache stability.

### `HeartbeatManager`

Automatic TTL refresh via periodic heartbeat requests.

## Files

```
prompt_cache_manager/
├── agent.py        # Main implementation
├── metadata.json   # Agent metadata
└── README.md       # This file
```

## Integration Tips

1. **For Claude/Anthropic**: Works directly with `cache_control` blocks
2. **For OpenAI**: Adapt to use their equivalent caching mechanisms
3. **For Custom Frameworks**: Apply the three patterns (checkpoint, prefix, heartbeat)
