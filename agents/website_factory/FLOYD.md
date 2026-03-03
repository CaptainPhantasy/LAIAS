# Website Factory — FLOYD.md

**Last Updated**: 2026-02-25
**Current Phase**: ALIGNMENT VERIFICATION
**Status**: SELF-HEALING IN PROGRESS
**Python Runtime**: REQUIRES VERIFICATION

---

## Project Overview

Website Factory is a multi-agent CrewAI system that reads a website specification
(markdown) and builds a production-ready Next.js website with:

- Real TSX files written to disk
- Critic/Fixer loop with 2% convergence threshold
- Playwright interaction testing
- RAGBOT visual analysis hook
- Persistent todo list as the shared contract between agents

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WEBSITE FACTORY FLOW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   SPEC (markdown) ──► spec_parser ──► SiteSpec (JSON)                       │
│                              │                                               │
│                              ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                     TODO MANAGER                                      │   │
│   │            (Persistent JSON task list on disk)                       │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│          ┌───────────────────┼───────────────────┐                          │
│          ▼                   ▼                   ▼                          │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│   │   BUILDER   │    │   CRITIC    │    │   FIXER     │                     │
│   │   AGENT     │    │   AGENT     │    │   AGENT     │                     │
│   └─────────────┘    └─────────────┘    └─────────────┘                     │
│          │                   │                   │                          │
│          └───────────────────┼───────────────────┘                          │
│                              ▼                                               │
│                    ┌─────────────────┐                                      │
│                    │   PLAYWRIGHT    │                                      │
│                    │   TESTER        │                                      │
│                    └─────────────────┘                                      │
│                              │                                               │
│                              ▼                                               │
│                    ┌─────────────────┐                                      │
│                    │     RAGBOT      │                                      │
│                    │   (optional)    │                                      │
│                    └─────────────────┘                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
agents/website_factory/
├── website_factory_flow.py    # Main orchestrator (WebsiteFactoryOrchestrator)
├── FLOYD.md                   # This file
└── tools/
    ├── __init__.py
    ├── spec_parser.py         # Parses spec markdown → SiteSpec
    ├── todo_manager.py        # Persistent JSON task list
    ├── page_builder_agent.py  # Writes actual TSX files
    ├── critic_agent.py        # Grades pages, outputs ---ISSUE--- blocks
    ├── fixer_agent.py         # Reads todo, applies surgical fixes
    └── playwright_tester.py   # Browser automation + RAGBOT hook
```

---

## Data Contracts (CRITICAL — ALIGNMENT REQUIRED)

### spec_parser.py PRODUCES:

```
SiteSpec:
  - project_name: str
  - spec_source: str
  - colors: List[ColorToken]       # name, hex_value, usage
  - typography: TypographySpec     # heading_font, body_font, scale
  - spacing: SpacingSpec           # base_unit, scale
  - pages: List[PageSpec]

PageSpec:
  - name: str                      # "homepage", "about", etc.
  - path: str                      # "/", "/about", etc.
  - title: str
  - meta_description: str
  - sections: List[Dict]           # [{name, content}, ...]
  - page_copy: Dict[str, str]      # {"full_content": "...", "hero_headline": "..."}
  - cta_primary: str
  - cta_secondary: str
```

### page_builder_agent.py EXPECTS:

```
page.name          → Used in task title, logging
page.path          → Determines output file path
page.cta_primary   → Injected into task description
page.page_copy     → JSON dumped into PAGE COPY AND CONTENT section
page.sections      → JSON dumped into PAGE SPEC section
```

### CRITICAL ALIGNMENT POINTS:

1. `page.page_copy["full_content"]` must contain actual spec content
2. `page.sections` must be populated with section data
3. `spec.raw_sections[page.name]` is fallback for page-specific spec text

---

## Known Issues (2026-02-25)

| Issue | Status | Notes |
|-------|--------|-------|
| Python version mismatch | IDENTIFIED | Wrong venv/Python being used |
| spec_parser extracting 37 pages | FIXED | Now correctly extracts 6 pages |
| page_copy empty `{}` | FIXED | Now extracts full_content from spec |
| sections not populated | FIXED | Now parses section blocks |
| Colors duplicated | PARTIAL | Spec has duplicate color definitions |
| TODO list growing unbounded | KNOWN | Need cleanup between runs |

---

## Required Environment Variables

```bash
# LLM Provider
LAIAS_LLM_PROVIDER=openai|zai
OPENAI_API_KEY=sk-...
ZAI_API_KEY=...

# Optional: RAGBOT integration
RAGBOT_COMMANDS_PATH=/path/to/RAGBOT_COMMANDS.md
RAGBOT_OBSERVATIONS_PATH=/path/to/RAGBOT_OBSERVATIONS.md

# Dev server for Playwright testing
DEV_SERVER_URL=http://localhost:3000
```

---

## Build Commands

```bash
# Run the full factory
python website_factory_flow.py \
  --spec /path/to/specification.md \
  --output /path/to/output/directory \
  --name "Project Name"

# Test spec parser only
python -c "from tools.spec_parser import parse_spec; s=parse_spec('spec.md'); print(len(s.pages))"

# Verify alignment
python -c "
from tools.spec_parser import parse_spec
spec = parse_spec('spec.md')
for p in spec.pages:
    print(f'{p.name}: has_content={bool(p.page_copy.get(\"full_content\"))}')
"
```

---

## Convergence Threshold

The builder loop continues until improvement between cycles is ≤2%:

```
Cycle 1: Grade 65%
Cycle 2: Grade 75%  → +10% improvement → CONTINUE
Cycle 3: Grade 82%  → +7% improvement  → CONTINUE
Cycle 4: Grade 85%  → +3% improvement  → CONTINUE
Cycle 5: Grade 86%  → +1% improvement  → STOP (converged)
```

---

## Handoff Notes

When resuming work on this system:

1. **VERIFY PYTHON ENVIRONMENT FIRST** - Don't assume venv is correct
2. **Check alignment** between spec_parser output and page_builder expectations
3. **Clear todo.json** between runs if starting fresh
4. **Delete output directory** before rebuild to avoid stale state
5. **Run alignment test** before full build:
   ```bash
   python -c "from tools.spec_parser import parse_spec; s=parse_spec('spec.md'); print(s.model_dump_json(indent=2)[:1000])"
   ```

---

## Changelog

| Date | Change |
|------|--------|
| 2026-02-25 | Created FLOYD.md |
| 2026-02-25 | Fixed spec_parser page extraction (37 → 6 pages) |
| 2026-02-25 | Fixed page_copy extraction (empty → populated) |
| 2026-02-25 | Identified Python version mismatch as root cause |

---

*"The spec is the law. Everything the builder builds must match it exactly."*
