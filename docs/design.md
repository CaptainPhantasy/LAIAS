
![](design/laias-logo.png)


# # 🎛 LAIAS Control Room — Visual System Specification
# 1\. Design Intent
Create a **cyber-ops control room aesthetic**:
* Deep space background
* Electric neon accents (cyan primary, purple secondary)
* Soft glow highlights (never overused)
* High contrast, readable, operator-grade UI
* Feels like: AI infrastructure + DevOps + neon intelligence

⠀Mood: **confident, sharp, technical, premium**

# 2\. Accessibility Standard
Target: **WCAG 2.2 AA compliance**
### Required:
* Body text contrast ≥ 4.5:1
* Large text contrast ≥ 3:1
* UI components ≥ 3:1
* Focus indicators must not rely on color alone
* All states (hover, active, disabled, error) clearly differentiated

⠀Neon may NOT be used as small body text color.

# 3\. Color System (Token-Based)
# 3.1 Dark Theme (Primary)
### Foundation (80% of UI)
### --bg-primary:     #0B1020
### --bg-secondary:   #111C36
### --bg-tertiary:    #1E2746
### --border-subtle:  rgba(255,255,255,0.08)
### Text
### --text-primary:   #F4F7FF
### --text-secondary: #AAB3C5
### --text-muted:     #6F7A96
### Brand Accents
### --accent-cyan:    #2DE2FF
### --accent-purple:  #8E5CFF
### --accent-pink:    #FF4FA3
### Functional Status
### --success: #22C55E
### --warning: #F59E0B
### --error:   #EF4444
### --info:    #38BDF8

# 3.2 Inverse Theme (Light Cyber)
Do NOT just invert colors.
Use controlled inversion:
### Foundation
### --bg-primary:     #F4F7FF
### --bg-secondary:   #E6ECFF
### --bg-tertiary:    #D8E2FF
### --border-subtle:  rgba(0,0,0,0.08)
### Text
### --text-primary:   #0B1020
### --text-secondary: #334155
### --text-muted:     #64748B
### Brand Accents (unchanged)
Keep:
### --accent-cyan
### --accent-purple
### --accent-pink
Neon accents must remain vivid in both themes.

# 4\. Usage Rules
# 4.1 Proportion Rule
* 70–80% neutral surfaces
* 10–15% accent color
* 5–10% functional states
* Neon never dominates layout

⠀
# 4.2 Glow Rules
Allowed:
* Buttons (primary)
* Active nav indicator
* Selected cards
* Graph highlights

⠀Glow spec:
### box-shadow:
### 0 0 18px rgba(45,226,255,0.35);
Do NOT apply glow to:
* Paragraph text
* Tables
* Log lines
* Long content blocks

⠀
# 5\. Layout Standard
Use:
* 8px spacing grid
* 12-column layout
* Max width: 1440px
* Border radius scale:
  * small: 8px
  * medium: 12px
  * large: 20px

⠀Control Room is NOT playful — it is precise.

# 6\. Component Specifications
# 6.1 Container Cards
* Background: bg-secondary
* Border: subtle neutral
* Status pill: colored + icon + label
* Hover: slight brightness increase + left neon bar

⠀
# 6.2 Buttons
### Primary
* Background: accent-cyan
* Text: dark background color
* Glow allowed
* Hover: brightness + subtle scale (1.02)

⠀Secondary
* Border: accent-purple
* Background: transparent
* Text: accent-purple

⠀Destructive
* Background: error
* No neon glow

⠀
# 6.3 Log Viewer
* Monospace font
* Dark panel background
* Log level indicator:
  * info → info color left bar
  * warning → warning color
  * error → error color
* Never color entire log line

⠀
# 6.4 Charts
* Background: neutral
* Grid lines: faint muted color
* Data lines: neon accent (cyan primary)
* Secondary dataset: purple
* Warning thresholds: amber
* Error thresholds: red

⠀
# 7\. Focus & Interaction Compliance
All interactive elements must have:
### focus-visible:ring-2
### focus-visible:ring-accent-cyan
### focus-visible:ring-offset-2
### focus-visible:ring-offset-bg-primary
Disabled:
* 50% opacity
* No glow
* Cursor not-allowed

⠀
# 8\. Motion Standard
Subtle, fast, professional.
* Duration: 150–200ms
* Easing: ease-out
* No bouncing
* No playful elastic effects

⠀
# 9\. Typography
Max 2 fonts:
Headings:
* Modern geometric sans (semi-bold or bold)

⠀Body:
* Clean sans (400–500)

⠀Logs:
* Monospace

⠀Scale: 12 / 14 / 16 / 20 / 24 / 32 / 48
Line height: 1.5 for body 1.2–1.3 for headings

# 10\. Theme Switching Rules
Theme must:
* Use CSS variables
* Toggle via class on <html>
* Persist via localStorage
* Default to system preference
* Transition smoothly (150ms fade)

⠀Do NOT dynamically recalc colors in JS.

# 11\. Visual Identity Summary
The system must feel:
* Intelligent
* Tactical
* Controlled
* High signal-to-noise
* DevOps serious
* Slightly cyberpunk, not arcade

⠀If UI feels like a gaming dashboard → reduce neon. If it feels boring enterprise gray → increase accent presence.


-------

# 🎚 LAIAS Studio UI — Visual & UX Specification (Builder Agent Input)
# 1) Design Intent
The Studio UI is a **creative workspace** (like a modern IDE + wizard), not an ops dashboard.
It must feel:
* **sexy + premium**
* **creative + “agent studio”**
* **trustworthy + compliant**
* **fast + focused**
* visually consistent with Control Room, but slightly more **expressive** (more gradient + neon allowed in headers/hero areas)

⠀
# 2) Compliance Target
Target: **WCAG 2.2 AA** (same as Control Room)
Hard rules:
* Body text and form labels use neutral text tokens only
* Neon colors are accents only (borders, highlights, chips, headings, icons)
* Every interactive element has visible focus ring
* Validation states use icon + label (not only color)

⠀
# 3) Theme System
Use **CSS variable tokens** with a single data-theme attribute on <html>.
* data-theme="dark" (default)
* data-theme="inverse" (light cyber)
* Persist in localStorage
* Default to system preference
* Smooth transition: 150ms

⠀
# 4) Token Set
### 4.1 Shared Brand Accents (same in both themes)
### --accent-cyan:   #2DE2FF
### --accent-purple: #8E5CFF
### --accent-pink:   #FF4FA3
### 4.2 Dark Theme Tokens
### --bg-primary:    #0B1020
### --bg-secondary:  #111C36
### --bg-tertiary:   #1E2746

### --surface:       #111C36
### --surface-2:     #1E2746
### --surface-3:     rgba(255,255,255,0.04)

### --border:        rgba(255,255,255,0.08)
### --border-strong: rgba(255,255,255,0.14)

### --text:          #F4F7FF
### --text-2:        #AAB3C5
### --text-3:        #6F7A96

### --shadow:        rgba(0,0,0,0.4)
### 4.3 Inverse Theme Tokens
### --bg-primary:    #F4F7FF
### --bg-secondary:  #E6ECFF
### --bg-tertiary:   #D8E2FF

### --surface:       #FFFFFF
### --surface-2:     #EAF0FF
### --surface-3:     rgba(0,0,0,0.03)

### --border:        rgba(0,0,0,0.08)
### --border-strong: rgba(0,0,0,0.14)

### --text:          #0B1020
### --text-2:        #334155
### --text-3:        #64748B

### --shadow:        rgba(15,23,42,0.12)
### 4.4 Functional Colors (shared)
### --success: #22C55E
### --warning: #F59E0B
### --error:   #EF4444
### --info:    #38BDF8

# 5) Visual Style Rules
### Proportions
Studio is more expressive than Control Room:
* 65–75% neutral surfaces
* 15–20% neon accents (but not as body text)
* 5–10% functional states

⠀Glow Rules
Glow allowed for:
* Primary CTA
* Active step / section header
* Selected tool chips
* Editor tab active indicator

⠀Glow forbidden for:
* Form labels
* Body copy
* Large table blocks
* Long lists

⠀Glow spec:
### Cyan glow:   0 0 18px rgba(45,226,255,0.35)
### Purple glow: 0 0 22px rgba(142,92,255,0.30)
### Shape & Depth
* Border radius: 12px standard, 20px for hero cards
* Subtle shadows, never heavy
* Borders are **always** subtle, accents appear on hover/active

⠀Motion
* 150–200ms, ease-out
* No bounce
* Prefer fade + slight translate (2–4px)

⠀
# 6) Layout Blueprint (Pages)
### Global Layout
* Top bar: project selector + theme toggle + user menu
* Left sidebar: navigation
* Main area: builder canvas
* Right panel: validation + deploy status (contextual)
* Bottom drawer (optional): run output / generation trace

⠀/create Builder Page Layout (Core)
Two recommended patterns; builders may pick either:
**Pattern A (Best for speed): 3-column**
1. Left: Sections nav (Description / Type / Tools / Advanced / Deploy)
2. Center: Form sections
3. Right: Code + Validation tabs

⠀**Pattern B (Best for focus): Split-view**
* Left: Form
* Right: Monaco editor + validation + file tabs

⠀Either way: keep “Generate / Validate / Deploy” actions sticky.

# 7) Component Specifications
### 7.1 Agent Description (Textarea)
* Large, prominent, first thing
* Supports helper text + character counter
* “Suggested prompts” chips under it (neon outline, subtle)

⠀7.2 Form Sections
Use consistent section cards:
* Background: --surface
* Border: --border
* Title row has optional accent line (cyan/purple alternating)

⠀7.3 Tool Selection
Tools are “chips / cards” with:
* icon
* name
* description
* toggle/checkbox
* Selected state:
  * border accent-cyan
  * subtle cyan glow
  * check icon
* Disabled state:
  * muted text, no glow

⠀7.4 Advanced Options (Collapsible)
Collapsed by default. When expanded, show:
* Provider
* Model
* Memory type
* Analytics Use a “danger boundary” for analytics/privacy toggles (clear wording, no dark patterns).

⠀7.5 Code Preview Panel (Monaco)
* File tabs: flow.py, agents.yaml, requirements.txt
* Dirty state: dot indicator + “Reset” button
* Validation indicators:
  * Pass: green check
  * Warn: amber triangle
  * Fail: red x
* Avoid neon text; use Monaco theme + neutral UI chrome.

⠀7.6 Primary Actions
Sticky action group:
* Primary: **Generate / Regenerate**
* Secondary: **Validate**
* Primary (final): **Deploy**
* After deploy: “View in Control Room” (link button)

⠀Primary button style:
* Background: accent-cyan
* Text: dark background token (dark theme = --bg-primary, inverse = --bg-primary)
* Glow allowed
* Hover: +5–8% brightness

⠀Destructive (Delete):
* Background: error
* No glow

⠀
# 8) Accessibility & Interaction Rules
### Focus
All interactive elements must have:
* focus-visible:ring-2
* ring color: accent-cyan
* offset color: bg-primary

⠀Forms
* Labels always visible (no placeholder-only labels)
* Errors: message text + icon + aria-describedby
* Required fields indicated with text + symbol, not color alone

⠀Keyboard
* Sidebar nav fully keyboard accessible
* Tool chips togglable with Space/Enter
* Tabs navigable

⠀
# 9) Typography
Use 2 fonts max:
* UI font: modern sans
* Logs/code: monospace (Monaco handles this)

⠀Scale:
* 12 / 14 / 16 / 20 / 24 / 32 / 48
* Body line-height 1.5

⠀Headings can use gradient text:
* Only for H1/H2, not for form labels

⠀Gradient heading:
* cyan → purple

⠀
# 10) “Sexy but compliant” brand cues to include
* Gradient header bar on /create
* Neon accent line on active section
* Tool chips with subtle glow when selected
* Animated “generation” state (thin neon progress line)
* Empty states with tasteful illustration-like iconography (simple, not cartoon)

⠀
# 11) Done Definition
Studio UI passes when:
* Theme toggle works across the app + persists
* All buttons/inputs/tabs have visible focus states
* Body text stays neutral and readable on both themes
* Neon is used as accent, not readability crutch
* Generate/Validate/Deploy flows are obvious and fast

-------

Love this phase. Wireframes are where the product actually becomes real.
Below are **clean, builder-ready wireframe docs** for both:
* 🧠 Studio UI (Agent Builder)
* 🖥 Control Room (Ops Dashboard)

⠀These are **layout + interaction wireframes**, not color/style (since we already defined your neon system). Your builder agents can use these to scaffold pages immediately.

# 🧠 STUDIO UI — Wireframe Document
## 1️⃣ Global Layout
┌──────────────────────────────────────────────────────────────┐
│ Top Bar                                                      │
│ [Logo]  Studio  |  Control Room  |  Docs      [Theme][User]│
├──────────────────────────────────────────────────────────────┤
│ Sidebar          │ Main Content Area                        │
│                  │                                           │
│ ▸ Home           │                                           │
│ ▸ Create Agent   │                                           │
│ ▸ Agents         │                                           │
│ ▸ Templates      │                                           │
│ ▸ Settings       │                                           │
└──────────────────────────────────────────────────────────────┘
### Behavior
* Sidebar collapsible
* Active page indicator
* Theme toggle in top right
* Layout responsive (sidebar becomes drawer on tablet)

⠀
# 2️⃣/create — Agent Builder (Primary Workspace)
### Layout Option (Recommended): 3-Column Builder
┌──────────────────────────────────────────────────────────────┐
│ Page Header: "Create Agent" + Status Indicator              │
├──────────────┬────────────────────────────┬──────────────────┤
│ Section Nav  │ Builder Form               │ Code Preview     │
│ (sticky)     │                            │ + Validation     │
│              │                            │ (sticky)         │
│ 1. Desc      │ [Description Textarea]     │ Tabs:            │
│ 2. Type      │                            │ flow.py          │
│ 3. Tools     │ [Agent Type Select]        │ agents.yaml      │
│ 4. Advanced  │ [Complexity Select]        │ requirements.txt │
│ 5. Deploy    │                            │                  │
│              │ [Task Type Select]         │ Monaco Editor    │
│              │                            │                  │
│              │ [Tool Checkboxes/Grid]     │ Validation       │
│              │                            │ Status Panel     │
│              │ [Advanced Collapsible]     │                  │
│              │                            │ [Validate]       │
│              │                            │ [Deploy]         │
└──────────────┴────────────────────────────┴──────────────────┘

## Section Details
### 1️⃣ Description Section
[Textarea - Large]
"Describe your AI agent..."

[Character Counter]
[Prompt Suggestion Chips]
Behavior:
* Debounced auto-generate option
* Character count bottom-right
* Helper text under field

⠀
### 2️⃣ Agent Type + Complexity
[Agent Type Dropdown]
[Complexity Dropdown]
[Task Type Dropdown]
Simple stacked layout.

### 3️⃣ Tool Selection
Grid layout:
[ Web Search ]   [ Web Scraper ]
[ Code Interp ]  [ File Manager ]
[ Database ]     [ API Connector ]
Each tile contains:
* Icon
* Title
* Short description
* Toggle checkbox
* Selected state highlight

⠀
### 4️⃣ Advanced Options (Collapsible Panel)
▼ Advanced Options
  [LLM Provider Select]
  [Model Select]
  [Memory Type Select]
  [Analytics Toggle]
Collapsed by default.

### 5️⃣ Code Preview Panel
Right column layout:
[ Tabs: flow.py | agents.yaml | requirements.txt ]

---------------------------------------------------
| Monaco Editor                                  |
---------------------------------------------------

[Validation Status]
- [x] Pattern Compliant
⚠ 2 Warnings
✕ 1 Error

[Validate]   [Deploy]
Behavior:
* Dirty state indicator
* Tab switching
* Deploy disabled until validation passes

⠀
# 3️⃣/agents — Agent List Page
┌──────────────────────────────────────────────────────────────┐
│ Agents                                                       │
│ [Search] [Filter Dropdown]      [Create Agent Button]      │
├──────────────────────────────────────────────────────────────┤
│ Agent Card Grid                                             │
│ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│ │ Agent Name  │  │ Agent Name  │  │ Agent Name  │          │
│ │ Type        │  │ Type        │  │ Type        │          │
│ │ Updated     │  │ Updated     │  │ Updated     │          │
│ │ [Edit]      │  │ [Edit]      │  │ [Edit]      │          │
│ │ [Deploy]    │  │ [Deploy]    │  │ [Deploy]    │          │
│ └─────────────┘  └─────────────┘  └─────────────┘          │
└──────────────────────────────────────────────────────────────┘
Behavior:
* Card hover state
* Duplicate + delete in overflow menu
* Pagination or infinite scroll

⠀
# 🖥 CONTROL ROOM — Wireframe Document
This one is more operational and data-dense.

# 1️⃣ Global Layout
Same top bar for consistency.
Sidebar:
▸ Dashboard
▸ Containers
▸ Metrics
▸ Logs
▸ Settings

# 2️⃣/ — Dashboard Overview
┌──────────────────────────────────────────────────────────────┐
│ System Overview                                              │
├──────────────────────────────────────────────────────────────┤
│ [Active Containers] [CPU Usage] [Memory] [Errors Today]     │
├──────────────────────────────────────────────────────────────┤
│ Recent Deployments Table                                     │
└──────────────────────────────────────────────────────────────┘
KPI cards:
* Large number
* Label
* Trend indicator

⠀
# 3️⃣/containers — Container Grid
┌──────────────────────────────────────────────────────────────┐
│ Containers                                                   │
│ [Search] [Status Filter] [Refresh]                          │
├──────────────────────────────────────────────────────────────┤
│ Grid View                                                    │
│ ┌─────────────────────┐                                      │
│ │ Agent Name          │                                      │
│ │ Status: ● Running   │                                      │
│ │ CPU: 42%            │                                      │
│ │ Memory: 512MB       │                                      │
│ │ [Start] [Stop] ...  │                                      │
│ └─────────────────────┘                                      │
└──────────────────────────────────────────────────────────────┘
Card states:
* Running
* Stopped
* Error

⠀Quick action buttons inline.

# 4️⃣/containers/[id] — Container Detail
┌──────────────────────────────────────────────────────────────┐
│ Agent Name      Status: Running    [Restart] [Stop]         │
├──────────────────────────────────────────────────────────────┤
│ Metrics Panel                                                │
│ [CPU Chart]  [Memory Chart]  [Network Chart]                │
├──────────────────────────────────────────────────────────────┤
│ Tabs: Logs | Config | Environment                            │
└──────────────────────────────────────────────────────────────┘

# 5️⃣/containers/[id]/logs — Log Viewer
┌──────────────────────────────────────────────────────────────┐
│ Logs                                                         │
│ [Search] [Level Filter] [Auto-scroll Toggle] [Export]       │
├──────────────────────────────────────────────────────────────┤
│ Log Stream Window                                            │
│ -----------------------------------------------------------  │
│ 12:04:01 INFO  Agent started                                 │
│ 12:04:05 WARN  Retry attempt                                 │
│ 12:04:07 ERROR Connection failed                             │
│ -----------------------------------------------------------  │
└──────────────────────────────────────────────────────────────┘
Behavior:
* Sticky filter bar
* Auto-scroll
* Copy + export

⠀
# System-Level Consistency Rules (Both UIs)
* Same header + sidebar structure
* Same spacing system
* Same typography scale
* Same theme toggle logic
* Same button variants
* Same modal + confirmation style
* Same loading skeleton style

⠀Studio = creative workspace Control Room = operational command center
Same brand, different mood intensity.


------

Perfect. Now we’re getting into the real design system layer.
Below is a **component-level wireframe specification** for both Studio UI and Control Room. This is implementation-ready and structured so your builder agents can generate reusable UI primitives inside components/ui/.
No color styling here — only structure, states, behavior, hierarchy, and layout contracts.

# 🧱 CORE DESIGN SYSTEM — Component Wireframes
These components are shared across:
* Studio UI
* Control Room

⠀
# 1️⃣ Button Component
# Variants
* primary
* secondary
* outline
* ghost
* destructive
* icon
* link

⠀
# Wireframe
### ┌──────────────────────┐
### │ [icon] Label         │
### └──────────────────────┘

# Props Contract
* variant
* size (sm | md | lg)
* iconLeft
* iconRight
* loading
* disabled
* fullWidth
* asChild (for link wrapping)

⠀
# States
| **State** | **Behavior** |
|:-:|:-:|
| Default | Normal |
| Hover | Slight brightness + elevation |
| Active | Subtle scale (0.98) |
| Focus | Visible focus ring |
| Disabled | Reduced opacity + no pointer events |
| Loading | Spinner replaces icon |

# Sizes
* Small: compact toolbar buttons
* Medium: default
* Large: primary page actions

⠀
# 2️⃣ Card Component
Used for:
* Agent cards
* Container cards
* Dashboard KPIs
* Form sections

⠀
# Base Wireframe
### ┌──────────────────────────┐
### │ Header (optional)        │
### ├──────────────────────────┤
### │ Content                  │
### │                          │
### ├──────────────────────────┤
### │ Footer (optional)        │
### └──────────────────────────┘

# Props
* title
* description
* actions
* hoverable
* selectable
* status
* compact

⠀
# Variants
* default
* elevated
* outlined
* interactive
* status-card

⠀
# Interaction Rules
Interactive card:
* Cursor pointer
* Hover highlight
* Selected state indicator
* Keyboard accessible (role="button")

⠀
# 3️⃣ Modal Component
Used for:
* Delete confirmations
* Deploy confirmations
* Advanced settings
* Error dialogs

⠀
# Wireframe
### Overlay (blurred background)

###         ┌──────────────────────────┐
###         │ Header                   │
###         │ Title        [X Close]   │
###         ├──────────────────────────┤
###         │ Content                  │
###         │                          │
###         ├──────────────────────────┤
###         │ Cancel     Confirm       │
###         └──────────────────────────┘

# Behavior
* ESC closes
* Trap focus inside
* Click outside optional
* Close button always top-right
* Confirmation modals require explicit action

⠀
# Sizes
* sm – simple confirm
* md – standard
* lg – complex form
* fullscreen – mobile

⠀
# 4️⃣ Tabs Component
Used in:
* Code Preview
* Container Detail
* Logs
* Settings

⠀
# Wireframe
### [ Tab 1 ] [ Tab 2 ] [ Tab 3 ]
### --------------------------------
### | Tab Content                 |
### --------------------------------

# Variants
* underline
* pill
* segmented

⠀
# Behavior
* Keyboard arrow navigation
* Active indicator animated
* Scrollable if overflow
* Dirty state dot supported

⠀
# 5️⃣ Input Components
# 5.1 Text Input
### Label
### ┌──────────────────────┐
### │ Input                │
### └──────────────────────┘
### Helper text / Error
States:
* Default
* Focus
* Error
* Disabled
* Success

⠀Must support:
* aria-describedby
* Icon inside
* Prefix/suffix
* Clear button

⠀
# 5.2 Textarea
Same structure +:
* Character counter
* Resize control (optional)

⠀
# 5.3 Select (Dropdown)
### Label
### ┌──────────────────────┐
### │ Selected value  ▼    │
### └──────────────────────┘
Behavior:
* Keyboard navigation
* Typeahead support
* Grouped options
* Scrollable menu

⠀
# 5.4 Checkbox
### ☐ Label
Supports:
* indeterminate
* disabled
* error

⠀
# 5.5 Toggle Switch
### [ OFF ]  or  [ ON ]
Used for:
* Analytics
* Feature flags
* Auto-scroll logs

⠀Must support label + description.

# 6️⃣ Tool Selection Tile (Studio-Specific)
Custom component.

# Wireframe
### ┌────────────────────────────┐
### │ Icon   Tool Name           │
### │        Short description   │
### │                            │
### │            [Checkbox]      │
### └────────────────────────────┘
States:
* Default
* Hover
* Selected
* Disabled

⠀Selected state:
* Highlight border
* Check indicator
* Keyboard toggle support

⠀
# 7️⃣ Section Panel Component
Used for:
* Studio form sections
* Metrics panels
* Config panels

⠀
# Wireframe
### ┌──────────────────────────┐
### │ Section Title            │
### │ Optional Description     │
### ├──────────────────────────┤
### │ Section Content          │
### └──────────────────────────┘
Supports:
* Collapsible
* Sticky header
* Validation state badge

⠀
# 8️⃣ Data Table Component
Used for:
* Agents list
* Containers list
* Recent deployments

⠀
# Wireframe
### ------------------------------------------------------
### | Col 1 | Col 2 | Col 3 | Actions                  |
### ------------------------------------------------------
### | Row                                         ⋮     |
### | Row                                         ⋮     |
### ------------------------------------------------------
Supports:
* Sortable columns
* Pagination
* Row selection
* Bulk actions
* Empty state
* Loading skeleton
* Row hover highlight

⠀
# 9️⃣ Status Badge Component
### ● Running
### ● Error
### ● Warning
Props:
* status
* size
* withIcon

⠀Must never rely on color alone. Always include text label.

# 🔟 KPI Metric Card
Control Room specific.

# Wireframe
### ┌────────────────────────────┐
### │ Title                      │
### │                            │
### │  82%                       │
### │  ▲ +4% since last hour     │
### └────────────────────────────┘
Supports:
* Trend indicator
* Sparkline
* Loading state

⠀
# 11️⃣ Log Viewer Component
Control Room specific.

# Wireframe
### Toolbar:
### [Search] [Level Filter] [Auto Scroll] [Export]

### -------------------------------------------
### | Timestamp | Level | Message            |
### -------------------------------------------
### | 12:01     | INFO  | Agent started      |
### | 12:05     | WARN  | Retry attempt      |
### -------------------------------------------
Features:
* Virtualized list
* Auto-scroll toggle
* Level filtering
* Copy line
* Scroll-to-bottom button

⠀
# 12️⃣ Sidebar Navigation
### ▸ Dashboard
### ▸ Containers
### ▸ Metrics
### ▸ Logs
Supports:
* Collapsible
* Active indicator
* Nested items
* Keyboard nav

⠀
# 13️⃣ Top Bar Component
### [Logo]  Studio | Control Room   [Theme] [User]
Features:
* Breadcrumb support
* Environment badge
* Theme toggle
* User dropdown

⠀
# 14️⃣ Toast Notification
### ┌──────────────────────────┐
### │ ✓ Agent deployed         │
### └──────────────────────────┘
Supports:
* success
* error
* warning
* info
* auto dismiss
* manual close

⠀
# 15️⃣ Empty State Component
### [Icon]
### No agents yet.
### [Create Agent]
Supports:
* Illustration icon
* Description
* CTA

⠀
# System Contracts (Important)
Every component must:
* Be fully keyboard accessible
* Support focus-visible
* Support dark + inverse themes via tokens
* Avoid hard-coded colors
* Use spacing scale
* Be usable in isolation

⠀
