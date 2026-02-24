# Floyd.md - Website Construction Guidelines

> **Version:** 1.0.0
> **Purpose:** High-level guidelines for building production-grade websites
> **Authority:** All workers MUST follow these guidelines

---

## I. Core Principles

### 1. Zero Defect Tolerance
- Every element must work
- Every link must connect
- Every button must function
- No broken anything ships

### 2. Fresh Worker Discipline
- Workers are spawned for tasks
- Workers are retired after completion
- Context is preserved in Supercache
- No baggage between tasks

### 3. Verification at Every Step
- Code is written → Critic reviews → Fixer fixes → Verifier confirms
- UI is built → Critic grades → Builder improves → Repeat until <3% gain
- Page is complete → Dual critics sign off → Documentation generated

---

## II. Quality Thresholds

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

---

## III. Build Phases

### Phase 0: Planning & Documentation
- Read specification document
- Create Floyd.md (this file)
- Create document management system
- Define file tree structure

### Phase 1: Scaffold
- Initialize project structure
- Install dependencies (LOCKED - no ^ or ~)
- Configure tooling (ESLint, Prettier, TypeScript)
- Create base configuration files

### Phase 2: Design System
- Implement color tokens
- Implement typography scale
- Implement spacing system
- Create base components (Button, Input, Card, etc.)

### Phase 3: Layout
- Header component
- Footer component
- Container/wrapper components
- Navigation (desktop + mobile)

### Phase 4: Pages (per page cycle)
- Build page structure
- Build page sections
- Apply design system
- Critic review cycle
- Repeat until <3% improvement

### Phase 5: Interactions
- Wire all buttons
- Wire all links
- Wire all forms
- Wire all dropdowns
- Wire all modals/accordions

### Phase 6: Verification
- Vision-based screenshot analysis
- Accessibility audit
- Performance audit
- Interaction testing
- Dual-critic sign-off

### Phase 7: Documentation
- Component inventory per page
- Interaction test results per page
- Screenshot evidence per page
- Final build receipt

---

## IV. Critic Protocol

### The Critic's Job
1. Find EVERYTHING wrong
2. Be harsh - no "it's good enough"
3. Document all issues with specific fixes
4. Assign severity (Critical, High, Medium, Low)
5. Grade the work (0-100%)

### Improvement Cycle Rule
```
IF improvement_from_last_cycle >= 3%:
    CONTINUE cycle
ELSE:
    STOP - maximum quality reached
```

### Dual Critic Sign-Off
- Critic A reviews independently
- Critic B reviews independently
- Both must agree page is complete
- Any disagreement → another cycle

---

## V. Vision Verification Protocol

### Screenshot Requirements
- Full page screenshots
- Mobile + Tablet + Desktop breakpoints
- Each interactive state (hover, focus, active)
- Each form state (empty, filled, error, success)

### Vision Analysis Checklist
- [ ] Layout matches spec
- [ ] Typography is correct
- [ ] Colors are correct
- [ ] Spacing is correct
- [ ] Alignment is correct
- [ ] Interactive elements visible
- [ ] No visual regressions
- [ ] Responsive at all breakpoints

### Confidence Requirement
- Minimum 98% confidence
- If below 98%, request clearer screenshot or manual review

---

## VI. Dependency Management

### Installation Rules
```bash
# ALWAYS use exact versions
npm install package@1.2.3 --save-exact

# NEVER use ranges
# ❌ "package": "^1.2.3"
# ❌ "package": "~1.2.3"
# ✅ "package": "1.2.3"
```

### Required Lock Files
- package-lock.json (npm) OR
- yarn.lock (yarn) OR
- pnpm-lock.yaml (pnpm)

---

## VII. File Structure Template

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
├── Floyd.md                    # This file
├── package.json                # Exact versions only
├── package-lock.json
└── README.md
```

---

## VIII. Context Window Management

### For Orchestrator
- Check usage before each spawn
- Store state in Supercache
- Hand off if >70%

### For Workers
- Complete task and exit
- Don't accumulate state
- Report progress to Supercache

### Checkpoint Keys
```
website_factory:phase:{n}:status
website_factory:page:{name}:status
website_factory:component:{name}:status
website_factory:verification:{page}:results
```

---

## IX. Error Handling

### If Build Fails
1. Log error to Supercache
2. Spawn diagnostic worker
3. Fix and retry
4. If 3 retries fail, escalate

### If Verification Fails
1. Document specific failures
2. Spawn fixer worker
3. Re-verify
4. Repeat until pass

### If Context Exhausted
1. Checkpoint current state
2. Document what's left
3. Prepare handoff summary
4. Exit cleanly

---

## X. Final Sign-Off Requirements

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

---

*This document is the authority for all build decisions.*
*When in doubt, refer to Floyd.md.*
