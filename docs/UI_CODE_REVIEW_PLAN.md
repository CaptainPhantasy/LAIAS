# LAIAS UI Code Review Plan

**Created:** 2026-02-17
**Purpose:** Verify UI works correctly with backend after LLM provider fixes
**Scope:** Studio UI + Control Room + API Integration

---

## I. Executive Summary

This review verifies the end-to-end flow from UI to backend and back, ensuring:
1. Agent generation works through the UI (not just CLI)
2. Template loading and form pre-population functions correctly
3. Code preview, validation, and deployment integrations are functional
4. Error handling provides meaningful user feedback
5. TypeScript types match backend OpenAPI schemas

---

## II. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              LAIAS FRONTEND STACK                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐       │
│  │   studio-ui     │     │  control-room   │     │     shared      │       │
│  │   (Port 3000)   │     │   (Port 3001)   │     │     types       │       │
│  │                 │     │                 │     │                 │       │
│  │  • Create Page  │     │  • Dashboard    │     │  • API Types    │       │
│  │  • Templates    │     │  • Containers   │     │  • API Client   │       │
│  │  • Agents List  │     │  • Logs Stream  │     │                 │       │
│  │  • Settings     │     │  • Metrics      │     │                 │       │
│  └────────┬────────┘     └────────┬────────┘     └────────┬────────┘       │
│           │                       │                       │                 │
│           └───────────────────────┴───────────────────────┘                 │
│                                   │                                         │
└───────────────────────────────────┼─────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
            ┌───────▼───────┐               ┌───────▼───────┐
            │ agent-generator│               │ docker-       │
            │ (Port 8001)    │               │ orchestrator  │
            │                │               │ (Port 8002)   │
            │ • /api/generate│               │ • /api/deploy │
            │ • /api/validate│               │ • /api/       │
            │ • /api/agents  │               │   containers  │
            │ • /api/templates│              │ • /api/logs   │
            └────────────────┘               └───────────────┘
```

---

## III. Review Scope

### A. Files to Review

#### 1. Studio UI Pages
| File | Purpose | Priority |
|------|---------|----------|
| `frontend/studio-ui/app/create/page.tsx` | Main agent creation form | CRITICAL |
| `frontend/studio-ui/app/templates/page.tsx` | Template selection | HIGH |
| `frontend/studio-ui/app/agents/page.tsx` | Saved agents list | MEDIUM |
| `frontend/studio-ui/app/page.tsx` | Landing/dashboard | MEDIUM |
| `frontend/studio-ui/app/settings/page.tsx` | Settings configuration | LOW |

#### 2. API Layer
| File | Purpose | Priority |
|------|---------|----------|
| `frontend/studio-ui/lib/api.ts` | Studio API client | CRITICAL |
| `frontend/shared/lib/api-client.ts` | Shared API client | CRITICAL |
| `frontend/shared/types/agent-generator.ts` | OpenAPI-generated types | HIGH |

#### 3. Components
| File | Purpose | Priority |
|------|---------|----------|
| `frontend/studio-ui/components/code-editor/code-panel.tsx` | Code preview | HIGH |
| `frontend/studio-ui/components/agent-builder/tool-tile.tsx` | Tool selection | MEDIUM |
| `frontend/studio-ui/components/layout/app-shell.tsx` | Layout wrapper | LOW |

#### 4. Store/State
| File | Purpose | Priority |
|------|---------|----------|
| `frontend/studio-ui/store/builder-store.ts` | Form state management | HIGH |

#### 5. Backend API Routes (for type matching)
| File | Purpose | Priority |
|------|---------|----------|
| `services/agent-generator/app/api/routes/agents.py` | Agent CRUD endpoints | HIGH |
| `services/agent-generator/app/api/routes/templates.py` | Template endpoints | HIGH |
| `services/agent-generator/app/models/requests.py` | Request schemas | CRITICAL |
| `services/agent-generator/app/models/responses.py` | Response schemas | CRITICAL |

---

## IV. Review Checklist

### Phase 1: API Contract Verification

#### 1.1 Request/Response Type Alignment
- [ ] `GenerateAgentRequest` frontend type matches backend Pydantic model
- [ ] `GenerateAgentResponse` frontend type matches backend response
- [ ] `ValidateCodeRequest` matches backend expectations
- [ ] Field names use correct casing (snake_case backend vs camelCase frontend)
- [ ] Optional fields are correctly marked in TypeScript
- [ ] Enum values match exactly

#### 1.2 API Endpoint URLs
- [ ] `/api/generate-agent` - POST - correct URL and method
- [ ] `/api/regenerate` - POST - correct URL and method
- [ ] `/api/validate-code` - POST - correct URL and method
- [ ] `/api/agents` - GET - correct URL and query params
- [ ] `/api/agents/{id}` - GET/PUT/DELETE - correct URL pattern
- [ ] `/api/templates` - GET - correct URL
- [ ] `/api/templates/{id}` - GET - correct URL pattern

#### 1.3 Error Handling
- [ ] HTTP errors are caught and displayed to user
- [ ] Network timeouts are handled gracefully
- [ ] Validation errors show field-specific messages
- [ ] 4xx vs 5xx errors are differentiated in UI

---

### Phase 2: Create Page Flow

#### 2.1 Form Initialization
- [ ] Default values load correctly
- [ ] Form validation works (min/max length, required fields)
- [ ] Debounced validation on description field (500ms)

#### 2.2 Template Loading
- [ ] Template ID from URL params is read correctly
- [ ] Template API call uses correct endpoint
- [ ] Template data pre-fills form fields:
  - [ ] description (from sample_prompts[0])
  - [ ] complexity (from default_complexity)
  - [ ] task_type (from category, mapped to valid enum)
  - [ ] tools_requested (from default_tools)
  - [ ] provider (from suggested_config.llm_provider)
  - [ ] max_agents (from suggested_config.max_agents)
- [ ] Template loading errors are displayed
- [ ] Loading state shows spinner

#### 2.3 Agent Generation Flow
- [ ] Generate button triggers API call
- [ ] Generation state transitions: idle → analyzing → generating → validating → complete
- [ ] Loading indicator shows during generation
- [ ] Generated code populates code panel:
  - [ ] flow_code → flow.py tab
  - [ ] agents_yaml → agents.yaml tab
  - [ ] state_class → state.py tab
- [ ] Validation runs automatically after generation
- [ ] Validation status displays correctly (score, errors, warnings)

#### 2.4 Code Panel Integration
- [ ] Tab switching works (flow.py, agents.yaml, state.py)
- [ ] Code is syntax-highlighted
- [ ] Line numbers display correctly
- [ ] Validation errors highlight problematic lines
- [ ] Copy code button works

#### 2.5 Deploy Integration
- [ ] Deploy button is disabled until validation passes
- [ ] Deploy calls correct API endpoint
- [ ] Container creation is initiated
- [ ] Success redirects to control room
- [ ] Deploy errors are displayed

---

### Phase 3: Templates Page

#### 3.1 Template Listing
- [ ] Templates load from API
- [ ] Template cards display correctly (name, description, category)
- [ ] Category filtering works
- [ ] Search functionality works
- [ ] Click navigates to /create?template={id}

---

### Phase 4: Agents Page

#### 4.1 Agent Listing
- [ ] Saved agents load from API
- [ ] Agent cards display (name, created date, status)
- [ ] Pagination works
- [ ] Filtering by task_type/complexity works

#### 4.2 Agent Actions
- [ ] View agent details
- [ ] Download generated code
- [ ] Delete agent with confirmation

---

### Phase 5: Type Safety Audit

#### 5.1 TypeScript Compilation
- [ ] `npm run build` completes without type errors
- [ ] No `any` types in API call sites
- [ ] All API responses are typed

#### 5.2 Runtime Type Validation
- [ ] Zod schemas match backend Pydantic models
- [ ] Form validation errors match schema constraints

---

### Phase 6: State Management

#### 6.1 Builder Store
- [ ] Generation state persists across re-renders
- [ ] Code files are stored correctly
- [ ] Validation status is updated after API calls
- [ ] Reset function clears all state

---

### Phase 7: Error Scenarios

#### 7.1 Network Errors
- [ ] API timeout shows user-friendly message
- [ ] CORS errors are handled
- [ ] Offline state is detected

#### 7.2 Backend Errors
- [ ] LLM provider errors (429, 401, 500) show meaningful message
- [ ] Validation errors list all issues
- [ ] Partial responses don't break UI

#### 7.3 Edge Cases
- [ ] Empty description submitted
- [ ] Very long description (>2000 chars)
- [ ] Invalid template ID in URL
- [ ] Concurrent generation requests

---

## V. Test Procedures

### A. Manual UI Testing

#### Test 1: Basic Agent Generation
```
1. Navigate to http://localhost:3000/create
2. Enter description: "A simple greeting agent that says hello"
3. Select complexity: simple
4. Select task_type: automation
5. Select provider: zai
6. Click "Generate Agent"
7. Verify:
   - Loading state appears
   - Code appears in right panel
   - Validation score shows
   - Deploy button enables
```

#### Test 2: Template-Based Generation
```
1. Navigate to http://localhost:3000/templates
2. Click on a template card
3. Verify redirect to /create?template={id}
4. Verify form is pre-filled with template data
5. Click "Generate Agent"
6. Verify generation completes
```

#### Test 3: Error Handling
```
1. Navigate to /create?template=nonexistent
2. Verify error message appears
3. Verify "Start Fresh" button works
4. Enter description < 10 chars
5. Verify validation error
6. Try to submit - verify button disabled
```

### B. Automated Testing (Future)

```typescript
// Test file: __tests__/api/generate-agent.test.ts
describe('Generate Agent API', () => {
  it('should send correct request format', async () => {
    // ...
  });
  
  it('should handle ZAI provider correctly', async () => {
    // ...
  });
  
  it('should display validation errors', async () => {
    // ...
  });
});
```

---

## VI. Issues Found During Review

### Phase 1: API Contract Verification (2026-02-17)

```
┌──────────┬──────────┬─────────────────────────────────────────────────────────┬────────────────────────────────────────────────────────────────────────────┬─────────┐
│ ID       │ Severity │ File                                                    │ Description                                                                │ Status  │
├──────────┼──────────┼─────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────┼─────────┤
│ ISS-001  │ LOW      │ frontend/studio-ui/lib/api.ts:102                       │ validateCode sends 'strict_mode' field not in backend ValidateCodeRequest  │ Open    │
│ ISS-002  │ LOW      │ services/agent-generator/app/models/responses.py:32     │ ValidationResult uses 'pattern_compliance' but response uses               │ Open    │
│          │          │                                                         │ 'pattern_compliance_score' - fixed with validation_alias (acceptable)      │         │
│ ISS-003  │ LOW      │ frontend/studio-ui/app/create/page.tsx:48               │ Form field 'provider' vs backend 'llm_provider' (correctly mapped at 295)  │ Closed  │
│ ISS-004  │ HIGH     │ frontend/studio-ui/lib/api.ts:86-93                     │ regenerateAgent sends JSON body but backend expects query params           │ Open    │
│ ISS-005  │ MEDIUM   │ frontend/studio-ui/store/builder-store.ts:70-74         │ CodeTab missing 'state.py', backend returns state_class that isn't shown   │ Open    │
│ ISS-006  │ MEDIUM   │ frontend/studio-ui/app/create/page.tsx:288-296          │ Model selector in UI not included in request payload to backend            │ Open    │
└──────────┴──────────┴─────────────────────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────┴─────────┘
```

#### Issue Details

**ISS-001: Unrecognized field in validateCode request**
- Location: `frontend/studio-ui/lib/api.ts` line 102
- Problem: Sends `strict_mode: true` but backend `ValidateCodeRequest` has no such field
- Impact: Low - backend ignores unknown fields (Pydantic default)
- Recommendation: Remove field or add to backend schema

**ISS-002: Pattern compliance field naming**
- Location: `services/agent-generator/app/models/responses.py` line 32
- Problem: `ValidationResult.pattern_compliance` vs `ValidateCodeResponse.pattern_compliance_score`
- Status: Already fixed with `validation_alias = "pattern_compliance_score"`
- Impact: None - acceptable solution

**ISS-003: Provider field name mismatch**
- Location: `frontend/studio-ui/app/create/page.tsx` lines 48, 295
- Problem: Form uses `provider`, backend expects `llm_provider`
- Status: Closed - correctly mapped at line 295: `llm_provider: formData.provider`

**ISS-004: regenerateAgent request format mismatch**
- Location: `frontend/studio-ui/lib/api.ts` lines 86-93
- Problem: Frontend sends JSON body, but OpenAPI spec shows query params
- Impact: HIGH - regeneration may fail
- Recommendation: Verify backend implementation and align

**ISS-005: Missing state.py tab in CodeTab type**
- Location: `frontend/studio-ui/store/builder-store.ts` lines 70-74
- Problem: `CodeTab` type only has 'flow.py' and 'agents.yaml', backend returns `state_class`
- Impact: MEDIUM - generated state code won't display in UI
- Recommendation: Add 'state.py' to CodeTab type

**ISS-006: Model selector not included in request**
- Location: `frontend/studio-ui/app/create/page.tsx` lines 288-296
- Problem: UI has model selector but value not sent to backend
- Impact: MEDIUM - cannot specify model per request
- Recommendation: Include `model` field in request payload

---

### Phase 2: Create Page Flow Review (2026-02-17)

```
┌──────────┬──────────┬─────────────────────────────────────────────────────────┬────────────────────────────────────────────────────────────────────────────┬─────────┐
│ ID       │ Severity │ File                                                    │ Description                                                                │ Status  │
├──────────┼──────────┼─────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────┼─────────┤
│ ISS-007  │ MEDIUM   │ frontend/studio-ui/store/builder-store.ts:15-20         │ GeneratedCode interface missing stateCode field                            │ Open    │
│ ISS-008  │ MEDIUM   │ frontend/studio-ui/components/code-editor/              │ CodePanel only shows 3 tabs (flow.py, agents.yaml, requirements.txt)       │ Open    │
│          │          │ code-panel.tsx:297-299                                  │ missing state.py for state_class display                                   │         │
│ ISS-009  │ HIGH     │ frontend/studio-ui/app/create/page.tsx:683-690          │ Model selector is uncontrolled component - value not stored or sent        │ Open    │
│ ISS-010  │ INFO     │ frontend/studio-ui/app/create/page.tsx                  │ Form validation, debouncing, state transitions all working correctly       │ Closed  │
└──────────┴──────────┴─────────────────────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────┴─────────┘
```

#### Phase 2 Issue Details

**ISS-007: GeneratedCode interface incomplete**
- Location: `frontend/studio-ui/store/builder-store.ts` lines 15-20, 113-129
- Problem: `GeneratedCode` interface lacks `stateCode`, `setGeneratedCode` doesn't map `state_class`
- Impact: MEDIUM - state.py code is generated by backend but lost in frontend
- Code:
  ```typescript
  // Current (line 15-20)
  interface GeneratedCode {
    agentId: string;
    flowCode: string;
    agentsYaml: string;
    requirements: string;
    // MISSING: stateCode: string;
  }
  ```

**ISS-008: CodePanel missing state.py tab**
- Location: `frontend/studio-ui/components/code-editor/code-panel.tsx` lines 297-299
- Problem: Only 3 tabs rendered, no state.py for displaying `state_class`
- Impact: MEDIUM - user cannot view generated state management code
- Code:
  ```tsx
  // Current (line 297-299)
  <TabsTrigger value="flow.py">flow.py</TabsTrigger>
  <TabsTrigger value="agents.yaml">agents.yaml</TabsTrigger>
  <TabsTrigger value="requirements.txt">requirements.txt</TabsTrigger>
  // MISSING: <TabsTrigger value="state.py">state.py</TabsTrigger>
  ```

**ISS-009: Model selector uncontrolled**
- Location: `frontend/studio-ui/app/create/page.tsx` lines 683-690
- Problem: Model Select has no `value` or `onChange`, not connected to form state
- Impact: HIGH - user cannot select model, always uses backend default
- Code:
  ```tsx
  // Current (line 683-690)
  <Select
    label="Model"
    disabled={loadingTemplate}
    options={MODELS_BY_PROVIDER[watchedProvider]?.map(...) || [...]}
    // MISSING: value={watchedModel}
    // MISSING: onChange={(val) => setValue('model', val)}
  />
  ```

**ISS-010: Working correctly (INFO)**
- Form validation with Zod schema: ✅ Working (lines 41-49)
- Debounced validation (500ms): ✅ Working (lines 217-230)
- State transitions (idle→analyzing→generating→validating→complete): ✅ Working
- Template loading with error handling: ✅ Working (lines 110-214)
- Deploy button disabled until validation passes: ✅ Working (line 403)

---

### Phase 3: Templates Page Review (2026-02-17)

```
┌──────────┬──────────┬─────────────────────────────────────────────────────────┬────────────────────────────────────────────────────────────────────────────┬─────────┐
│ ID       │ Severity │ File                                                    │ Description                                                                │ Status  │
├──────────┼──────────┼─────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────┼─────────┤
│ ISS-011  │ INFO     │ frontend/studio-ui/app/templates/page.tsx               │ Templates page implementation verified - all flows working correctly        │ Closed  │
└──────────┴──────────┴─────────────────────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────┴─────────┘
```

#### Phase 3 Verification Summary

**Templates Page (`frontend/studio-ui/app/templates/page.tsx`):**
- ✅ Proper loading states with skeleton UI (lines 45-50)
- ✅ Error handling with retry button (lines 52-62)
- ✅ Category filtering via tabs (lines 64-83)
- ✅ Search functionality with debounce (lines 84-92)
- ✅ Template cards display correctly (name, description, category)
- ✅ Click navigates to `/create?template={id}` (line 37)
- ✅ Backend API (`services/agent-generator/app/api/routes/templates.py`) contract aligned

**No issues found in Phase 3.** The templates page is well-implemented with proper state management, error handling, and navigation.

---

### Phase 4: Code Panel Review (2026-02-17)

```
┌──────────┬──────────┬─────────────────────────────────────────────────────────┬────────────────────────────────────────────────────────────────────────────┬─────────┐
│ ID       │ Severity │ File                                                    │ Description                                                                │ Status  │
├──────────┼──────────┼─────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────┼─────────┤
│ ISS-012  │ INFO     │ frontend/studio-ui/components/code-editor/              │ Code panel architecture verified: Monaco config, validation integration    │ Closed  │
│          │          │ code-panel.tsx                                          │ and generation state indicator all working correctly                       │         │
└──────────┴──────────┴─────────────────────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────┴─────────┘
```

#### Phase 4 Verification Summary

**CodePanel Component (`frontend/studio-ui/components/code-editor/code-panel.tsx`):**
- ✅ Monaco editor properly configured (lines 319-336)
  - minimap disabled, proper fonts, line numbers, word wrap
  - Custom LAIAS dark theme (lines 45-73)
  - SSR-safe dynamic import (lines 20-23)
- ✅ Tab switching mechanism working (lines 295-300)
- ✅ Generation state indicator (lines 97-149)
  - Proper transitions: idle → analyzing → generating → validating → complete/error
- ✅ Validation panel with score, errors, warnings (lines 155-240)
  - Error details with line numbers (lines 216-237)
  - Quality score color coding (lines 176-184)

**State.py Issue Confirmation (related to ISS-005/007/008):**
The CodePanel correctly implements the current CodeTab type, but the type itself is incomplete:
- `CodePanelProps` (line 29-39): No `stateCode` prop
- `getCodeForTab` (lines 263-272): No state.py case
- `getLanguageForTab` (lines 274-283): No state.py case
- Tab triggers (lines 297-299): Only 3 tabs

**Builder Store (`frontend/studio-ui/store/builder-store.ts`):**
- ✅ Zustand persist middleware configured correctly (lines 190-196)
- ✅ Selectors and hooks properly exported (lines 204-236)
- Confirmed ISS-007: `GeneratedCode` interface (lines 15-20) missing `stateCode`
- Confirmed ISS-005: `initialCodeFiles` (lines 70-74) only has 3 tabs
- Confirmed: `setGeneratedCode` (lines 113-129) doesn't map `state_class` from response

**No new issues in Phase 4.** Code panel is well-implemented; state.py issue is a type cascade problem tracked under ISS-005/007/008.

---

### Phase 5: Error Handling Review (2026-02-17)

```
┌──────────┬──────────┬─────────────────────────────────────────────────────────┬────────────────────────────────────────────────────────────────────────────┬─────────┐
│ ID       │ Severity │ File                                                    │ Description                                                                │ Status  │
├──────────┼──────────┼─────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────┼─────────┤
│ ISS-013  │ LOW      │ frontend/studio-ui/app/create/page.tsx:337-338         │ Validation errors only logged to console, not shown to user                │ Open    │
│ ISS-014  │ INFO     │ frontend/studio-ui/lib/api.ts:35-65                    │ ApiError class and handleResponse well-implemented with good fallbacks     │ Closed  │
│ ISS-015  │ INFO     │ frontend/studio-ui/app/create/page.tsx:110-214         │ Template loading error handling comprehensive with timeout, 404, abort     │ Closed  │
└──────────┴──────────┴─────────────────────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────┴─────────┘
```

#### Phase 5 Verification Summary

**API Error Handling (`frontend/studio-ui/lib/api.ts`):**
- ✅ `ApiError` class (lines 35-44): Properly captures status, data, and message
- ✅ `handleResponse` (lines 46-65):
  - Extracts error detail from string or object form
  - Falls back to HTTP status text
  - Properly typed with generics

**Create Page Error Handling:**
- ✅ Template loading (lines 110-214):
  - AbortController with 10s timeout (line 143)
  - 404 specific error message (lines 156-158)
  - AbortError timeout message (lines 203-204)
  - UI shows error banner with Retry/Start Fresh buttons (lines 414-470)
- ✅ Generation errors (lines 318-325):
  - Sets error state with message
  - Displays below Generate button (lines 716-718)
- ✅ Deploy errors (lines 377-382):
  - Sets error state with message
- ⚠️ Validation errors (lines 337-338):
  - Only logs to console, not displayed to user

**ISS-013: Validation error not shown to user**
- Location: `frontend/studio-ui/app/create/page.tsx` lines 337-338
- Problem: Validation failure silently fails, user not notified
- Impact: LOW - validation usually succeeds after generation
- Code:
  ```typescript
  } catch (error) {
    console.error('Validation failed:', error);
    // MISSING: setGenerationError() or toast notification
  }
  ```

---

### Phase 6: TypeScript Compilation Check (2026-02-17)

```
┌──────────┬──────────┬─────────────────────────────────────────────────────────┬────────────────────────────────────────────────────────────────────────────┬─────────┐
│ ID       │ Severity │ File                                                    │ Description                                                                │ Status  │
├──────────┼──────────┼─────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────┼─────────┤
│ ISS-016  │ INFO     │ frontend/studio-ui/app/settings/team/page.tsx:51       │ ESLint warning: useEffect missing 'fetchTeams' dependency                  │ Closed  │
│ ISS-017  │ INFO     │ frontend/studio-ui/app/templates/page.tsx:162          │ ESLint warning: useEffect missing 'fetchTemplates' dependency              │ Closed  │
└──────────┴──────────┴─────────────────────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────┴─────────┘
```

#### Phase 6 Verification Summary

**Build Result: ✅ SUCCESS**
```
> next build
 ✓ Compiled successfully
 ✓ Generating static pages (9/9)
```

**Bundle Sizes:**
- `/create` page: 37.9 kB (largest, expected for main builder)
- `/_not-found`: 896 B
- First Load JS shared: 100 kB

**Warnings (non-blocking ESLint, not TypeScript errors):**
- `settings/team/page.tsx:51` - useEffect dependency
- `templates/page.tsx:162` - useEffect dependency

**No TypeScript compilation errors.** Build passes cleanly.

---

## VII. Review Execution Order

1. **API Contract Review** (30 min)
   - Compare frontend types with backend schemas
   - Identify mismatches

2. **Create Page Deep Dive** (45 min)
   - Full code review of create/page.tsx
   - Test generation flow

3. **Template Flow Review** (20 min)
   - Template loading
   - Form pre-population

4. **Code Panel Review** (15 min)
   - Code display
   - Validation integration

5. **Error Handling Review** (15 min)
   - All error paths
   - User feedback quality

6. **TypeScript Compilation Check** (5 min)
   - Build verification

---

## VIII. Success Criteria

The UI is considered working if:

1. ✅ User can generate an agent from the UI (not just CLI)
2. ✅ Template selection pre-fills the form correctly
3. ✅ Generated code appears in the code panel
4. ✅ Validation results display correctly
5. ✅ Deploy button works and creates container
6. ✅ Errors show meaningful messages to user
7. ✅ TypeScript compiles without errors
8. ✅ No console errors during normal operation

---

### Phase 7: Manual UI Testing (2026-02-17)

```
┌──────────┬──────────┬─────────────────────────────────────────────────────────┬────────────────────────────────────────────────────────────────────────────┬─────────┐
│ ID       │ Severity │ File                                                    │ Description                                                                │ Status  │
├──────────┼──────────┼─────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────┼─────────┤
│ ISS-018  │ HIGH     │ frontend/studio-ui/app/create/page.tsx:302-307         │ setGeneratedCode does NOT map state_class from response (ISS-005 fix)     │ Open    │
│ ISS-019  │ INFO     │ N/A                                                     │ Backend API verified working via direct testing                            │ Closed  │
└──────────┴──────────┴─────────────────────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────┴─────────┘
```

#### Phase 7 Verification Summary

**Environment Status:**
- All Docker services running and healthy
- UI accessible at http://localhost:3000
- Backend API at http://localhost:8001

**Backend API Testing Results:**

| Endpoint | Method | Status | Notes |
|----------|--------|--------|-------|
| `/api/templates` | GET | ✅ 200 | Returns 3 templates correctly |
| `/api/templates/{id}` | GET | ✅ 200 | Template detail works |
| `/api/templates/nonexistent` | GET | ✅ 404 | Proper error handling |
| `/api/generate-agent` | POST | ✅ 200 | Generation works with proper payload |
| `/api/validate-code` | POST | ✅ 200 | Validation works correctly |
| `/api/regenerate` | POST | ❌ Expected | Backend expects QUERY PARAMS, not JSON body |

**Backend Response Structure (VERIFIED):**
```json
{
  "agent_id": "gen_20260217_114742_f76af03b",
  "agent_name": "HelloWorldFlow",
  "version": "1.0.0",
  "flow_code": "... (10574 chars)",
  "agents_yaml": "... (1235 chars)",
  "state_class": "... (1098 chars)",  // ← PRESENT IN RESPONSE!
  "requirements": ["crewai", "pydantic", ...],
  "estimated_cost_per_run": 0.0187,
  "complexity_score": 3,
  "agents_created": [...],
  "tools_included": [],
  "flow_diagram": "...",
  "validation_status": {...},
  "created_at": "2026-02-17T11:47:42.250575",
  "expires_at": null
}
```

**Frontend Request Mapping (VERIFIED):**
```typescript
// page.tsx lines 288-296 - CORRECT mapping
const requestPayload = {
  description: data.description,
  agent_name: agentName,           // ✅ Auto-generated
  complexity: data.complexity,
  task_type: data.task_type,
  max_agents: data.max_agents,
  tools_requested: data.tools_requested.length > 0 ? data.tools_requested : null,
  llm_provider: data.provider,     // ✅ Correctly mapped
};
```

**ISS-018: state_class NOT mapped to frontend state (NEW)**
- Location: `frontend/studio-ui/app/create/page.tsx` lines 302-307
- Problem: Response contains `state_class` but frontend doesn't store it
- Code:
  ```typescript
  // Current (line 302-307)
  setGeneratedCode({
    agentId: response.agent_id || '',
    flowCode: response.flow_code || '',
    agentsYaml: response.agents_yaml || '',
    requirements: '',  // ❌ Should be response.requirements?.join('\n')
    // MISSING: stateCode: response.state_class || ''
  });
  ```
- Impact: state.py tab will always be empty even though backend generates it

**Confirmed Issues from API Testing:**

| Issue | Severity | Confirmed? | Notes |
|-------|----------|------------|-------|
| ISS-004 | HIGH | ✅ YES | `/api/regenerate` expects query params, frontend sends JSON body |
| ISS-005 | MEDIUM | ✅ YES | Backend returns `state_class`, frontend doesn't use it |
| ISS-006 | MEDIUM | ✅ YES | Model selector value not in request (linked to ISS-009) |
| ISS-007 | MEDIUM | ✅ YES | GeneratedCode interface missing stateCode |
| ISS-008 | MEDIUM | ✅ YES | CodePanel only shows 3 tabs, missing state.py |
| ISS-009 | HIGH | ✅ YES | Model Select has no value/onChange props |
| ISS-013 | LOW | ✅ YES | Validation errors logged but not shown to user |

**Test Commands (for user verification):**
```bash
# All services should be running
docker compose ps

# Open UI
open http://localhost:3000

# Test Case 1: Generate agent
# Navigate to /create
# Enter description: "A simple greeting agent that says hello"
# Select complexity: simple
# Click "Generate Agent"
# Expected: Code appears in right panel (but state.py will be empty due to ISS-018)

# Test Case 2: Model selector (ISS-009)
# Try to select a different model from the dropdown
# Expected: Selection is ignored (uncontrolled component)

# Test Case 3: Regenerate (ISS-004)
# Click regenerate button after generation
# Expected: API call fails with 422 error
```

---

## IX. Final Issue Summary

```
┌──────────┬──────────┬─────────────────────────────────────────────────────────────────────────────────────────┐
│ ID       │ Severity │ Description                                                                          │
├──────────┼──────────┼─────────────────────────────────────────────────────────────────────────────────────────┤
│ ISS-004  │ HIGH     │ regenerateAgent sends JSON body but backend expects query params                     │
│ ISS-005  │ MEDIUM   │ CodeTab type missing 'state.py' - backend returns state_class not displayed          │
│ ISS-006  │ MEDIUM   │ Model selector value not included in request payload                                │
│ ISS-007  │ MEDIUM   │ GeneratedCode interface missing stateCode field                                      │
│ ISS-008  │ MEDIUM   │ CodePanel only shows 3 tabs, missing state.py                                        │
│ ISS-009  │ HIGH     │ Model selector is uncontrolled component - value not stored or sent                  │
│ ISS-013  │ LOW      │ Validation errors only logged to console, not shown to user                          │
│ ISS-018  │ HIGH     │ setGeneratedCode does NOT map state_class from response                              │
└──────────┴──────────┴─────────────────────────────────────────────────────────────────────────────────────────┘
```

### Fix Priority

**P0 (Critical - Blocks Core Functionality):**
1. **ISS-009 + ISS-006:** Model selector uncontrolled - Fix by adding value/onChange props
2. **ISS-004:** Regenerate API mismatch - Fix by sending query params instead of JSON body
3. **ISS-018 + ISS-005/007/008:** state.py not displayed - Fix by mapping state_class in setGeneratedCode

**P1 (Important - Affects User Experience):**
4. **ISS-013:** Show validation errors to user via toast/alert

### Recommended Fixes

**Fix 1: Model Selector (ISS-009/006)**
```diff
--- a/frontend/studio-ui/app/create/page.tsx
+++ b/frontend/studio-ui/app/create/page.tsx
@@ -683,6 +683,8 @@ export default function CreatePage() {
               <Select
                 label="Model"
                 disabled={loadingTemplate}
+                value={watch('model')}
+                onChange={(val) => setValue('model', val)}
                 options={MODELS_BY_PROVIDER[watchedProvider]?.map((m) => ({
                   value: m,
```

**Fix 2: Regenerate API (ISS-004)**
```diff
--- a/frontend/studio-ui/lib/api.ts
+++ b/frontend/studio-ui/lib/api.ts
@@ -84,11 +84,12 @@ export async function generateAgent(request: GenerateAgentRequest): Promise<Gen
  */
 export async function regenerateAgent(request: RegenerateRequest): Promise<GenerateAgentResponse> {
+  const params = new URLSearchParams({
+    agent_id: request.agent_id,
+    feedback: request.feedback,
+    previous_code: request.previous_code,
+  });
+  const response = await fetch(`${AGENT_API_URL}/api/regenerate?${params}`, {
-  const response = await fetch(`${AGENT_API_URL}/api/regenerate`, {
     method: 'POST',
-    headers: { 'Content-Type': 'application/json' },
-    body: JSON.stringify(request),
   });
   return handleResponse<GenerateAgentResponse>(response);
 }
```

**Fix 3: state.py Display (ISS-018/005/007/008)**
```diff
--- a/frontend/studio-ui/app/create/page.tsx
+++ b/frontend/studio-ui/app/create/page.tsx
@@ -300,6 +300,7 @@ export default function CreatePage() {
       setGeneratedCode({
         agentId: response.agent_id || '',
         flowCode: response.flow_code || '',
         agentsYaml: response.agents_yaml || '',
-        requirements: '',
+        requirements: Array.isArray(response.requirements) ? response.requirements.join('\n') : '',
+        stateCode: response.state_class || '',
       });
```

**Fix 4: CodeTab Type (ISS-005)**
```diff
--- a/frontend/studio-ui/types/index.ts
+++ b/frontend/studio-ui/types/index.ts
@@ -48,7 +48,7 @@ export type BuilderSection = 'description' | 'type' | 'tools' | 'advanced' | 'de
 /**
  * Code editor file tabs
  */
-export type CodeTab = 'flow.py' | 'agents.yaml' | 'requirements.txt';
+export type CodeTab = 'flow.py' | 'agents.yaml' | 'requirements.txt' | 'state.py';
```

---

## X. References

- Backend OpenAPI Spec: `docs/openapi-agent-generator.yaml`
- Frontend Types: `frontend/shared/types/agent-generator.ts`
- API Client: `frontend/studio-ui/lib/api.ts`
- Builder Store: `frontend/studio-ui/store/builder-store.ts`
