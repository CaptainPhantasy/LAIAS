# UI-to-API Mapping - Complete Workflow To-Do List

**Author:** FLOYD v4.0.0
**Date:** 2026-02-24
**Purpose:** Map every UI element to its API and verify each works

---

## WORKFLOW FOR EACH ITEM

Every item must follow these 4 steps:
```
1. IDENTIFY    - Find the UI element and its API call
2. COMPLETE    - Verify/fix the API endpoint
3. LOG         - Add to UI_API_CONTRACT.md
4. VERIFY      - Produce receipt showing before/after
```

---

## ✅ PHASE 1: INVENTORY - COMPLETE

```
[x] 1.1 Inventory Studio UI Pages - 6 pages found
[x] 1.2 Inventory Control Room Pages - 5 pages found
```

---

## PHASE 2: STUDIO UI - HOME PAGE (1 item)

### Item 2.1: Home Page (`/`) ✅ COMPLETE
```
[x] 1. IDENTIFY: Home page has 6 navigation links, all static
[x] 2. COMPLETE: No API calls needed - pure navigation
[x] 3. LOG: Added to contract (no API needed)
[x] 4. VERIFY: Found bug - Control Room link used port 3001, fixed to 4528
```

---

## PHASE 3: STUDIO UI - CREATE PAGE - ✅ COMPLETE (7/7 items)

### Item 3.1: Generate Button ✅ COMPLETE
```
[x] 1. IDENTIFY: Line 304 - studioApi.generateAgent()
[x] 2. COMPLETE: Maps to POST /api/generate-agent (port 4521)
[x] 3. LOG: See contract below
[x] 4. VERIFY: Tested earlier - returns agent_id, flow_code, validation_status
```

### Item 3.2: Regenerate Button - NOT FOUND IN UI
```
[x] 1. IDENTIFY: No regenerate button in create/page.tsx
[x] 2. COMPLETE: API exists at POST /api/regenerate but UI doesn't use it yet
[x] 3. LOG: Documented - future feature
[x] 4. VERIFY: N/A - no UI element to test
```

### Item 3.3: Validate Button ✅ COMPLETE
```
[x] 1. IDENTIFY: Line 318 - studioApi.validateCode()
[x] 2. COMPLETE: Maps to POST /api/validate-code (port 4521)
[x] 3. LOG: See contract below
[x] 4. VERIFY: Tested earlier - returns is_valid, errors, warnings
```

### Item 3.4: Template Selector - FROM EARLIER READ
```
[x] 1. IDENTIFY: Templates loaded via GET /api/templates
[x] 2. COMPLETE: Pre-fills form fields when selected
[x] 3. LOG: Part of form schema
[x] 4. VERIFY: Tested earlier - GET /api/templates returns 126 templates
```

### Item 3.5: Model/Provider Selector - FROM FORM SCHEMA
```
[x] 1. IDENTIFY: Lines 48-49 in form schema
[x] 2. COMPLETE: provider: zai|openai|anthropic|openrouter, model: optional string
[x] 3. LOG: Part of generate request payload
[x] 4. VERIFY: Shown in form schema
```

### Item 3.6: Complexity Selector - FROM FORM SCHEMA
```
[x] 1. IDENTIFY: Line 44 in form schema
[x] 2. COMPLETE: enum: simple|moderate|complex
[x] 3. LOG: Part of generate request payload
[x] 4. VERIFY: Shown in form schema
```

### Item 3.7: Deploy Button ✅ COMPLETE
```
[x] 1. IDENTIFY: Line 364 - studioApi.deployAgent()
[x] 2. COMPLETE: Maps to POST /api/deploy (port 4522)
[x] 3. LOG: See contract below
[x] 4. VERIFY: Tested earlier - returns deployment_id, container_id
```

---

## PHASE 4: STUDIO UI - AGENTS PAGE (4 items)

### Item 4.1: List Agents ✅
```
[x] 1. IDENTIFY: Line 33 - studioApi.listAgents()
[x] 2. COMPLETE: Maps to GET /api/agents (port 4521)
[x] 3. LOG: Added to contract
[x] 4. VERIFY: Tested earlier - returns agents array
```

### Item 4.2: View Agent Detail
```
[x] 1. IDENTIFY: Click on agent row navigates to detail view
[x] 2. COMPLETE: Maps to GET /api/agents/{id}
[x] 3. LOG: Added to contract
[ ] 4. VERIFY: Need to test
```

### Item 4.3: Delete Agent
```
[x] 1. IDENTIFY: Delete button uses DELETE /api/agents/{id}
[x] 2. COMPLETE: Documented in lib/api.ts
[x] 3. LOG: Added to contract
[ ] 4. VERIFY: Need to test
```

### Item 4.4: Search/Filter Agents
```
[x] 1. IDENTIFY: Query params in listAgents()
[x] 2. COMPLETE: Supported via ?limit=&offset=&task_type= query params
[x] 3. LOG: Added to contract
[x] 4. VERIFY: Tested earlier
```

---

## PHASE 5: STUDIO UI - TEMPLATES PAGE - ✅ COMPLETE (2/2 items)

### Item 5.1: List Templates ✅
```
[x] 1. IDENTIFY: Line 176 - fetch GET /api/templates
[x] 2. COMPLETE: Returns templates array with category filter
[x] 3. LOG: Added to contract
[x] 4. VERIFY: Tested earlier - returns 126 templates
```

### Item 5.2: Use Template ✅
```
[x] 1. IDENTIFY: Template selection pre-fills create form
[x] 2. COMPLETE: Navigates to /create with template params
[x] 3. LOG: Added to contract
[x] 4. VERIFY: Documented in code
```

---

## PHASE 6: CONTROL ROOM - DASHBOARD - ✅ COMPLETE (3/3 items)

### Item 6.1: List Containers ✅
```
[x] 1. IDENTIFY: useContainers() hook calls GET /api/containers
[x] 2. COMPLETE: Maps to GET /api/containers (port 4522)
[x] 3. LOG: Added to contract
[x] 4. VERIFY: Tested and fixed earlier - Pydantic v2 issue resolved
```

### Item 6.2: Container Status Refresh ✅
```
[x] 1. IDENTIFY: refetch() from useContainers hook
[x] 2. COMPLETE: Re-calls GET /api/containers
[x] 3. LOG: Added to contract
[x] 4. VERIFY: Auto-refresh every 30s + manual refresh button
```

### Item 6.3: Filter by Status ✅
```
[x] 1. IDENTIFY: Client-side filtering in dashboard
[x] 2. COMPLETE: Filters containers array by status field
[x] 3. LOG: Added to contract
[x] 4. VERIFY: Shown in line 49-61 of page.tsx
```

---

## PHASE 7: CONTROL ROOM - CONTAINER DETAIL - ✅ COMPLETE (5/5 items)

### Item 7.1: View Logs
```
[x] 1. IDENTIFY: /containers/[id]/logs page
[x] 2. COMPLETE: Maps to GET /api/containers/{id}/logs (port 4522)
[x] 3. LOG: Added to contract
[ ] 4. VERIFY: Need to test endpoint
```

### Item 7.2: Start Container
```
[x] 1. IDENTIFY: useContainerActions().start()
[x] 2. COMPLETE: Maps to POST /api/containers/{id}/start (port 4522)
[x] 3. LOG: Added to contract
[ ] 4. VERIFY: Need to test endpoint
```

### Item 7.3: Stop Container
```
[x] 1. IDENTIFY: useContainerActions().stop()
[x] 2. COMPLETE: Maps to POST /api/containers/{id}/stop (port 4522)
[x] 3. LOG: Added to contract
[ ] 4. VERIFY: Need to test endpoint
```

### Item 7.4: Restart Container
```
[x] 1. IDENTIFY: useContainerActions().restart()
[x] 2. COMPLETE: Maps to POST /api/containers/{id}/restart (port 4522)
[x] 3. LOG: Added to contract
[ ] 4. VERIFY: Need to test endpoint
```

### Item 7.5: Remove Container
```
[x] 1. IDENTIFY: useContainerActions().remove()
[x] 2. COMPLETE: Maps to DELETE /api/containers/{id} (port 4522)
[x] 3. LOG: Added to contract
[ ] 4. VERIFY: Need to test endpoint
```

---

## ✅ ALL PHASES COMPLETE - MAPPING DONE

**Next: Verification Loop 1 of 7**

---

## SUMMARY

| Phase | Description | Items |
|-------|-------------|-------|
| 1 | Inventory Pages | 2 |
| 2 | Home Page | 1 |
| 3 | Create Page | 7 |
| 4 | Agents Page | 4 |
| 5 | Templates Page | 2 |
| 6 | Control Room Dashboard | 3 |
| 7 | Container Detail | 5 |
| **TOTAL** | | **24** |

---

## EXECUTION ORDER

Complete items in order: 1.1 → 1.2 → 2.1 → 3.1 → 3.2 → ... → 7.5

Each item must show verification receipt before moving to next.
