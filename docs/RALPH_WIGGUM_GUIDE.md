# Ralph Wiggum Technique: Adapted for FLOYD Code

**Document Type:** Operational Guide
**Date Created:** February 21, 2026
**Author:** Claude (FLOYD Instance)
**Purpose:** How to use the Ralph Wiggum AI loop technique with FLOYD Code for overnight autonomous work

---

## What Ralph Wiggum Is

Ralph Wiggum is a technique for autonomous, iterative AI development. At its core, it's a bash loop that keeps feeding an AI agent a prompt until it completes a task.

**The Philosophy:**
- Iteration beats perfection
- Failures are data, not endpoints
- The loop handles retry logic automatically
- You set it up, walk away, come back to finished work

**The Original Pattern:**
```bash
while :; do cat PROMPT.md | claude ; done
```

---

## Why This Matters for You

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  THE PROBLEM RALPH SOLVES                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  CURRENT STATE:                                                              │
│  • You start a task with an agent                                           │
│  • Agent hits a blocker at 30 seconds                                       │
│  • You're making dinner / sleeping / away                                   │
│  • Task sits dead until you return                                          │
│                                                                              │
│  WITH RALPH:                                                                 │
│  • You start a task with a Ralph loop                                       │
│  • Agent hits a blocker                                                     │
│  • Loop feeds the same prompt back                                          │
│  • Agent tries again with error context                                     │
│  • Repeats until completion or max iterations                               │
│  • You return to finished work                                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Adapting Ralph for FLOYD Code

The original Ralph is designed for Claude Code CLI. Here's how to adapt it for FLOYD Code:

### The Core Loop Pattern

```bash
#!/bin/bash
# ralph.sh - Ralph Wiggum loop for FLOYD Code

PROMPT_FILE="$1"
MAX_ITERATIONS="${2:-20}"
COMPLETION_SIGNAL="${3:-RALPH_COMPLETE}"

ITERATION=0

while [ $ITERATION -lt $MAX_ITERATIONS ]; do
    echo "=== RALPH ITERATION $((ITERATION+1))/$MAX_ITERATIONS ==="
    
    # Run FLOYD Code with the prompt
    # This would need to be adapted based on how FLOYD Code is invoked
    cat "$PROMPT_FILE" | floyd-code
    
    # Check for completion signal
    if grep -q "$COMPLETION_SIGNAL" /tmp/ralph_output.txt 2>/dev/null; then
        echo "=== RALPH COMPLETE ==="
        break
    fi
    
    ITERATION=$((ITERATION+1))
    sleep 5  # Brief pause between iterations
done

echo "=== RALPH FINISHED AFTER $ITERATION ITERATIONS ==="
```

### The Prompt Structure

Every Ralph prompt needs:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  RALPH PROMPT ANATOMY                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. TASK DEFINITION                                                          │
│     Clearly state what needs to be done                                     │
│                                                                              │
│  2. SUCCESS CRITERIA                                                         │
│     How will the agent know it's done?                                      │
│     Must be VERIFIABLE (tests pass, files exist, etc.)                      │
│                                                                              │
│  3. COMPLETION SIGNAL                                                        │
│     Exact phrase to output when complete                                    │
│     Example: "RALPH_COMPLETE"                                                │
│                                                                              │
│  4. STUCK HANDLING                                                           │
│     What to do if blocked for N iterations                                  │
│     Example: "After 5 failures, document blockers and stop"                 │
│                                                                              │
│  5. CONTEXT PRESERVATION                                                     │
│     Instructions to maintain state between iterations                       │
│     Example: "Write progress to /tmp/ralph_progress.md"                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Practical Applications for Legacy AI

### Use Case 1: Research Workflow Overnight

```
RALPH PROMPT: Research LinkedIn Posting Strategy

TASK:
Research optimal LinkedIn posting strategies for AI/tech founders.

REQUIREMENTS:
1. Find studies on best posting times for B2B tech audience
2. Identify content types that get highest engagement
3. Analyze what works for similar solo founder profiles
4. Create a 2-week content calendar

SUCCESS CRITERIA:
- Document exists at /Volumes/Storage/Research/2026-02-22_LinkedIn_Strategy.md
- Contains: Executive Summary, Key Findings, Content Calendar
- Calendar has specific times, content types, and hashtags

STUCK HANDLING:
- After 3 failed searches, try alternative search terms
- After 5 failures, document what's blocking and output RALPH_BLOCKED

COMPLETION:
Output "RALPH_COMPLETE" when document meets all criteria.
```

### Use Case 2: Last 20% Agent

```
RALPH PROMPT: Complete the Sales Agent Project

TASK:
Take the Sales Agent project from 80% to 100% completion.

CURRENT STATE:
- Located at /Volumes/Storage/Sales Agent
- Frontend builds successfully
- Backend API functional
- Missing: tests, error handling, documentation

REQUIREMENTS:
1. Write tests for all API endpoints (coverage > 70%)
2. Add error handling with proper HTTP status codes
3. Create README.md with setup instructions
4. Ensure `docker compose up` works from clean clone

VERIFICATION:
- Run: npm test (must pass)
- Run: npm run lint (no errors)
- Run: docker compose up (must start without errors)

STUCK HANDLING:
- If test fails 3 times, skip it and document why
- If dependency issue, try alternative packages
- After 10 failures, output RALPH_BLOCKED with summary

COMPLETION:
Output "RALPH_COMPLETE" when all verification passes.
```

### Use Case 3: Marketing Content Batch

```
RALPH PROMPT: Generate Week of LinkedIn Content

TASK:
Create 5 LinkedIn posts for Legacy AI following the BALLS philosophy.

CONTEXT:
- Company: Legacy AI (solo founder, Douglas Talley, Indiana)
- Product: FLOYD ecosystem, LAIAS, SUPERCACHE
- Voice: Self-deprecating, funny, anti-corporate
- Must mention Bella (the cat) at least once per post

REQUIREMENTS:
1. Post 1: About building 23 things out of spite
2. Post 2: Hot take on AI industry
3. Post 3: "LinkedOut is boring" style
4. Post 4: Technical achievement with humor
5. Post 5: Weekend reflection as founder

OUTPUT:
- Create /Volumes/Storage/Marketing/LinkedIn/YYYY-MM-DD_week_batch.md
- Each post clearly separated
- Include suggested posting times

FORBIDDEN:
- Never use: "thrilled," "humbled," "excited to announce"
- Never sound like LinkedIn influencer
- Never be boring

COMPLETION:
Output "RALPH_COMPLETE" when all 5 posts are ready.
```

---

## Implementation Options

### Option A: Simple Bash Script

Create `/Volumes/Storage/LAIAS/scripts/ralph.sh`:

```bash
#!/bin/bash

PROMPT_FILE="$1"
MAX_ITER="${2:-20}"
SIGNAL="${3:-RALPH_COMPLETE}"
LOG_FILE="/tmp/ralph_$(date +%Y%m%d_%H%M%S).log"

echo "Starting Ralph loop..."
echo "Prompt: $PROMPT_FILE"
echo "Max iterations: $MAX_ITER"
echo "Completion signal: $SIGNAL"
echo "Log: $LOG_FILE"

for i in $(seq 1 $MAX_ITER); do
    echo "" | tee -a "$LOG_FILE"
    echo "=== ITERATION $i/$MAX_ITER ===" | tee -a "$LOG_FILE"
    echo "Time: $(date)" | tee -a "$LOG_FILE"
    
    # This is where you'd invoke your agent
    # The exact command depends on your setup
    echo "Would run: floyd-code with prompt from $PROMPT_FILE"
    
    # Check for completion
    if grep -q "$SIGNAL" "$LOG_FILE" 2>/dev/null; then
        echo "=== RALPH COMPLETE ===" | tee -a "$LOG_FILE"
        exit 0
    fi
    
    sleep 10
done

echo "=== RALPH EXHAUSTED (max iterations reached) ===" | tee -a "$LOG_FILE"
exit 1
```

### Option B: Python Orchestrator

Create `/Volumes/Storage/LAIAS/scripts/ralph_orchestrator.py`:

```python
#!/usr/bin/env python3
"""
Ralph Wiggum Orchestrator for LAIAS

Runs iterative agent loops until completion or exhaustion.
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime
from pathlib import Path

class RalphLoop:
    def __init__(self, prompt_file: str, max_iterations: int = 20, 
                 completion_signal: str = "RALPH_COMPLETE"):
        self.prompt_file = Path(prompt_file)
        self.max_iterations = max_iterations
        self.completion_signal = completion_signal
        self.iteration = 0
        self.log_file = Path(f"/tmp/ralph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        self.state_file = Path("/tmp/ralph_state.json")
        
    def load_prompt(self) -> str:
        """Load the prompt file."""
        with open(self.prompt_file) as f:
            return f.read()
    
    def load_state(self) -> dict:
        """Load previous state if exists."""
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {"iteration": 0, "attempts": [], "complete": False}
    
    def save_state(self, state: dict):
        """Save current state."""
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def run_iteration(self, prompt: str) -> tuple[bool, str]:
        """
        Run a single iteration.
        Returns (is_complete, output)
        """
        self.iteration += 1
        
        # Log start
        msg = f"\n=== ITERATION {self.iteration}/{self.max_iterations} ===\n"
        msg += f"Time: {datetime.now().isoformat()}\n"
        print(msg)
        
        # This is where you'd invoke your agent
        # Example: call LAIAS workflow
        # result = subprocess.run(
        #     ["docker", "exec", "laias-agent-generator", "python", "-c", prompt],
        #     capture_output=True, text=True
        # )
        # output = result.stdout
        
        # Placeholder for now
        output = "Agent would run here with the prompt"
        
        # Log output
        with open(self.log_file, 'a') as f:
            f.write(msg)
            f.write(output)
            f.write("\n")
        
        # Check for completion
        is_complete = self.completion_signal in output
        return is_complete, output
    
    def run(self):
        """Run the Ralph loop."""
        print(f"Starting Ralph loop...")
        print(f"Prompt: {self.prompt_file}")
        print(f"Max iterations: {self.max_iterations}")
        print(f"Log: {self.log_file}")
        
        prompt = self.load_prompt()
        state = self.load_state()
        self.iteration = state.get("iteration", 0)
        
        while self.iteration < self.max_iterations:
            is_complete, output = self.run_iteration(prompt)
            
            state["iteration"] = self.iteration
            state["attempts"].append({
                "iteration": self.iteration,
                "timestamp": datetime.now().isoformat(),
                "output_length": len(output)
            })
            self.save_state(state)
            
            if is_complete:
                print(f"\n=== RALPH COMPLETE after {self.iteration} iterations ===")
                state["complete"] = True
                self.save_state(state)
                return 0
            
            time.sleep(5)  # Brief pause
        
        print(f"\n=== RALPH EXHAUSTED after {self.iteration} iterations ===")
        return 1


def main():
    if len(sys.argv) < 2:
        print("Usage: ralph_orchestrator.py <prompt_file> [max_iterations] [completion_signal]")
        sys.exit(1)
    
    prompt_file = sys.argv[1]
    max_iter = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    signal = sys.argv[3] if len(sys.argv) > 3 else "RALPH_COMPLETE"
    
    ralph = RalphLoop(prompt_file, max_iter, signal)
    sys.exit(ralph.run())


if __name__ == "__main__":
    main()
```

### Option C: LAIAS Integration

Create a Ralph-enabled workflow in LAIAS:

```python
# /Volumes/Storage/LAIAS/agents/ralph_workflow.py

class RalphWorkflow(Flow[RalphState]):
    """
    Ralph Wiggum workflow that wraps other workflows with retry logic.
    """
    
    @start()
    async def load_task(self, inputs: Dict[str, Any]) -> RalphState:
        self.state.target_workflow = inputs.get("workflow")
        self.state.prompt = inputs.get("prompt")
        self.state.max_iterations = inputs.get("max_iterations", 20)
        self.state.completion_signal = inputs.get("completion_signal", "RALPH_COMPLETE")
        self.state.current_iteration = 0
        return self.state
    
    @listen("load_task")
    async def run_iteration(self, state: RalphState) -> RalphState:
        while self.state.current_iteration < self.state.max_iterations:
            self.state.current_iteration += 1
            
            # Run the target workflow
            result = await self.state.target_workflow.kickoff_async(
                inputs={"prompt": self.state.prompt}
            )
            
            # Check for completion
            if self.state.completion_signal in str(result):
                self.state.status = "complete"
                return self.state
            
            # Prepare for next iteration with context
            self.state.prompt = f"""
{self.state.prompt}

---
PREVIOUS ATTEMPT (iteration {self.state.current_iteration}) DID NOT COMPLETE.
OUTPUT SO FAR:
{result}

Please continue and output {self.state.completion_signal} when done.
"""
        
        self.state.status = "exhausted"
        return self.state
```

---

## Best Practices

### 1. Always Use Max Iterations

```bash
# Good
ralph.sh prompt.md 50

# Dangerous (could run forever)
ralph.sh prompt.md
```

### 2. Make Completion Verifiable

```
Bad:
"Make it good"

Good:
"All tests pass AND coverage > 80%"
"File exists at /path/to/output.md AND contains 'EXECUTIVE SUMMARY'"
```

### 3. Include Stuck Handling

```
After 5 failed iterations:
1. Stop trying the same approach
2. Document what failed
3. Try alternative approach
4. If still stuck after 10, output RALPH_BLOCKED
```

### 4. Preserve Context Between Iterations

```
After each iteration:
1. Write progress to /tmp/ralph_progress.md
2. Read that file at start of next iteration
3. Continue from where you left off
```

### 5. Start Small, Then Scale

```
Day 1: Test Ralph on a 30-minute task
Day 2: Run Ralph overnight on a multi-hour task
Day 3: Queue multiple Ralph tasks in sequence
```

---

## Integration with Your Existing Systems

### With SUPERCACHE

```python
# Store Ralph state in SUPERCACHE
cache_store(
    key="ralph:current_task",
    value={
        "prompt": prompt,
        "iteration": iteration,
        "status": status,
        "started_at": started_at
    },
    tier="project"
)
```

### With Shift Supervisor

```python
# The Shift Supervisor can queue Ralph tasks
def queue_ralph_task(prompt_file: str, schedule_time: str):
    task = {
        "type": "ralph",
        "prompt_file": prompt_file,
        "scheduled_for": schedule_time,
        "max_iterations": 30
    }
    cache_store(key="shift_supervisor:queue", value=task)
```

### With LAIAS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  RALPH + LAIAS INTEGRATION                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TRIGGER                                                                     │
│  • Webhook (Google Sheets via Zapier)                                       │
│  • Schedule (Shift Supervisor cron)                                         │
│  • Manual (Studio UI)                                                        │
│                                                                              │
│  LAIAS                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Ralph Workflow                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │  Iteration 1 → Target Workflow → Check Completion           │    │    │
│  │  │  Iteration 2 → Target Workflow (with context) → Check       │    │    │
│  │  │  Iteration 3 → Target Workflow (with context) → COMPLETE    │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  OUTPUT                                                                      │
│  • Result stored in SUPERCACHE                                              │
│  • Documentation generated                                                   │
│  • Notification sent                                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Reference

```bash
# Start a Ralph loop
./ralph.sh prompt.md 30 RALPH_COMPLETE

# Check Ralph status
cat /tmp/ralph_state.json

# View Ralph log
tail -f /tmp/ralph_*.log

# Cancel Ralph
pkill -f ralph

# Queue multiple tasks
echo "./ralph.sh task1.md 20" >> overnight_queue.sh
echo "./ralph.sh task2.md 30" >> overnight_queue.sh
chmod +x overnight_queue.sh
./overnight_queue.sh
```

---

## Summary

| Aspect | What It Does |
|--------|--------------|
| **Core Mechanism** | Loop that feeds same prompt until completion |
| **Key Parameters** | Prompt, max iterations, completion signal |
| **Best For** | Well-defined tasks with verifiable completion |
| **Not For** | Tasks needing human judgment or unclear goals |
| **Safety** | Always use max iterations to prevent infinite loops |
| **Integration** | Works with LAIAS, SUPERCACHE, Shift Supervisor |

---

**DOCUMENT ENDS**

*— Claude (FLOYD Instance)*
*"The loop doesn't get tired. You do."*
