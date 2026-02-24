#!/usr/bin/env python3
"""
Run Godzilla to generate the Website Construction Factory agent.

This script:
1. Loads Godzilla
2. Sends the comprehensive Website Factory request
3. Saves the generated code to the website_factory directory
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from pathlib import Path

# Set Z.AI API key - correct key for coding endpoint
os.environ["ZAI_API_KEY"] = "20773c266c7d4c26bfc7e9396dfc8d23.ASTs0f8m75Jg5fYJ"

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

from godzilla_flow import GodzillaFlow

# The comprehensive Website Factory request
WEBSITE_FACTORY_REQUEST = """
Create a WEBSITE CONSTRUCTION FACTORY agent - a production-grade multi-agent system for building launch-ready websites.

## CORE ARCHITECTURE

### Orchestrator (Does NOT build - only spawns workers)
- Monitors context window usage (check every task, checkpoint at 70%)
- Spawns fresh workers for each task
- Retires workers after task completion
- Coordinates between phases
- Enforces quality gates
- Uses Supercache for state persistence

### Worker Lifecycle
- Spawn → Task → Verify → Retire → Replace
- Fresh worker for nearly every task
- No worker carries baggage between tasks

## BUILD PHASES

### Phase 0: Planning & Documentation
- Read specification document
- Create Floyd.md (high-level build guidelines)
- Create document management system
- Define file tree structure

### Phase 1: Scaffold Builders
- Create file tree structure accurately
- Install dependencies with EXACT versions (NO ^ or ~)
- Lock all dependencies
- Configure tooling (ESLint, Prettier, TypeScript)
- Verify scaffold is correct before proceeding

### Phase 2: Design System Builders
- Implement color tokens
- Implement typography scale
- Implement spacing system (8px base)
- Create base components (Button, Input, Card, etc.)

### Phase 3: Layout Builders
- Header component (desktop + mobile)
- Footer component
- Container/wrapper components
- Navigation with mobile menu

### Phase 4: Page Builders (per page cycle)
- Build page structure
- Build page sections
- Apply design system
- CRITIC CYCLE: Build → Critic Review → Fix → Verify → Repeat
- Continue cycles until improvement < 3% between cycles

### Phase 5: Interaction Wirers
- Wire ALL buttons to their actions
- Wire ALL links to destinations
- Wire ALL forms with validation and submission
- Wire ALL dropdowns and selects
- Wire ALL modals, accordions, carousels
- Verify every interactive element works

### Phase 6: Verification
- Vision-based screenshot analysis (98%+ confidence)
- Accessibility audit (WCAG 2.1 AA - 100% required)
- Performance audit (Lighthouse ≥95 all categories)
- Interaction testing (every element)
- Dual-critic sign-off

### Phase 7: Final Sign-Off
- Critic #1 independent review (≥95%)
- Critic #2 independent review (≥95%)
- Consensus required for completion
- Generate final build receipt

## QUALITY AGENTS

### Harsh Critic
- Finds EVERY defect
- Grades harshly (95% still means issues found)
- Checks alignment, spacing, typography, colors, interactions
- Compares against spec relentlessly
- Assigns severity (Critical, High, Medium, Low)
- Documents all issues with specific fixes

### Fixer
- Receives issues from critic
- Fixes every single one
- No approximations

### Verifier
- Confirms all fixes are complete and correct
- Compares against spec

### Vision Analyzer
- Uses GLM-4.6v for screenshot analysis
- Must achieve 98%+ confidence
- Verifies layout, colors, typography, spacing, alignment
- Checks responsive at all breakpoints

### Accessibility Auditor
- WCAG 2.1 AA compliance (100% pass required)
- Color contrast ratio: ≥4.5:1 for text
- Keyboard navigation on all elements
- ARIA labels on all interactive elements
- Focus indicators visible

### Performance Auditor
- Lighthouse Performance: ≥95
- Lighthouse Accessibility: 100
- Lighthouse Best Practices: 100
- Lighthouse SEO: 100
- Core Web Vitals: All green

### Final Sign-Off Critics (2 independent)
- Critic #1: Independent review
- Critic #2: Independent review
- Both must agree page is complete
- Any disagreement → another cycle

## QUALITY THRESHOLDS

| Metric | Minimum | Target |
|--------|---------|--------|
| Lighthouse Performance | 95 | 100 |
| Lighthouse Accessibility | 100 | 100 |
| Lighthouse Best Practices | 100 | 100 |
| Lighthouse SEO | 100 | 100 |
| Vision Verification Confidence | 98% | 99%+ |
| UI Improvement Threshold | 3% | N/A (stopping condition) |
| WCAG Compliance | AA | AAA (where feasible) |
| Color Contrast Ratio | 4.5:1 | 7:1 |

## IMPROVEMENT CYCLE RULE

```
IF improvement_from_last_cycle >= 3%:
    CONTINUE cycle (build → critic → fix → verify)
ELSE:
    STOP - maximum quality reached
    Proceed to final sign-off
```

## DRIFT PREVENTION

- Self-check every few minutes
- Compare current state against expected state
- Course correction if drift detected
- Log all drift incidents

## DEPENDENCY MANAGEMENT

```bash
# ALWAYS use exact versions
npm install package@1.2.3 --save-exact

# NEVER use ranges
# ❌ "package": "^1.2.3"
# ❌ "package": "~1.2.3"
# ✅ "package": "1.2.3"
```

## FILE STRUCTURE TEMPLATE

```
project/
├── src/
│   ├── app/                    # Next.js app router
│   ├── components/
│   │   ├── ui/                 # Base components
│   │   ├── sections/           # Page sections
│   │   └── layout/             # Layout components
│   ├── lib/                    # Utilities
│   ├── styles/                 # Global styles
│   └── types/                  # TypeScript types
├── public/
│   ├── images/
│   └── fonts/
├── docs/
│   ├── verification/           # Verification reports
│   ├── screenshots/            # Screenshot evidence
│   └── build-receipts/         # Sign-off documents
├── Floyd.md                    # Build guidelines
├── package.json                # Exact versions only
├── package-lock.json
└── README.md
```

## FINAL SIGN-OFF REQUIREMENTS

Per Page:
- [ ] UI Critic #1 signed off (≥95%)
- [ ] UI Critic #2 signed off (≥95%)
- [ ] Accessibility passed (WCAG 2.1 AA)
- [ ] All interactions verified
- [ ] Vision verification passed (≥98%)
- [ ] Lighthouse ≥95 all categories
- [ ] Documentation complete

Project Complete:
- [ ] All pages signed off
- [ ] All links verified
- [ ] All forms working
- [ ] All responsive breakpoints verified
- [ ] Cross-browser tested
- [ ] Final build receipt generated

## TOOLS NEEDED

- floyd-supercache (state persistence)
- floyd-runner (test/lint/build)
- floyd-explorer (file reading)
- floyd-terminal (process management)
- lab-lead (agent spawning)
- Vision analysis via GLM-4.6v

Generate a complete, production-ready CrewAI flow that implements ALL of this.
Complexity: complex
"""


async def main():
    """Run Godzilla to generate the Website Factory agent."""
    
    print("=" * 70)
    print("                GODZILLA - WEBSITE FACTORY GENERATOR")
    print("=" * 70)
    print(f"\nStarted at: {datetime.now().isoformat()}")
    print("-" * 70)
    
    # Create Godzilla instance
    godzilla = GodzillaFlow()
    
    # Pre-populate state with request data
    godzilla.state.customer_request = WEBSITE_FACTORY_REQUEST
    godzilla.state.complexity = "complex"
    
    print(f"\nLLM configured: {godzilla.llm}")
    print(f"\nRequest length: {len(WEBSITE_FACTORY_REQUEST)} characters")
    print("\nStarting agent generation...")
    print("-" * 70)
    
    # Run Godzilla - inputs are already set in state
    result = await godzilla.kickoff_async()
    
    print("\n" + "=" * 70)
    print("                GENERATION COMPLETE")
    print("=" * 70)
    print(f"\nStatus: {godzilla.state.status}")
    print(f"Progress: {godzilla.state.progress}%")
    print(f"Confidence: {godzilla.state.confidence:.2%}")
    print(f"Deployment Ready: {godzilla.state.deployment_ready}")
    
    # Save output - use container-accessible path
    output_dir = Path("/app/agents/website_factory_generated")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if godzilla.state.deployment_ready:
        print("\n" + "-" * 70)
        print("SAVING GENERATED CODE:")
        print("-" * 70)
        
        for filename, content in godzilla.state.final_package.items():
            output_path = output_dir / filename
            with open(output_path, "w") as f:
                f.write(content)
            print(f"  ✓ Saved: {output_path}")
        
        # Also save the full generated code
        code_path = output_dir / "generated_factory_flow.py"
        with open(code_path, "w") as f:
            f.write(godzilla.state.generated_code)
        print(f"  ✓ Saved: {code_path}")
        
        print(f"\n✓ All files saved to: {output_dir}")
        print(f"\nTo copy to host, run:")
        print(f"  docker cp laias-agent-generator:{output_dir}/* /Volumes/Storage/LAIAS/agents/website_factory/")
    
    # Print preview of generated code
    if godzilla.state.generated_code:
        print("\n" + "-" * 70)
        print("GENERATED CODE PREVIEW (first 3000 chars):")
        print("-" * 70)
        print(godzilla.state.generated_code[:3000])
        if len(godzilla.state.generated_code) > 3000:
            print(f"\n... ({len(godzilla.state.generated_code) - 3000} more characters)")
    
    return godzilla.state


if __name__ == "__main__":
    asyncio.run(main())
