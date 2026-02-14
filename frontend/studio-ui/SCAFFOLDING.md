# Studio UI — Scaffolding Guide

## Directory Structure

```
frontend/studio-ui/
├── app/                          # Next.js App Router pages
│   ├── layout.tsx                # Root layout with theme provider
│   ├── page.tsx                  # Home/landing page
│   ├── create/
│   │   └── page.tsx              # Agent builder page (MAIN WORKSPACE)
│   ├── agents/
│   │   ├── page.tsx              # Agent list page
│   │   └── [id]/
│   │       └── page.tsx          # Agent detail/edit page
│   └── api/
│       └── generate/
│           └── route.ts          # API proxy route (optional)
│
├── components/
│   ├── ui/                       # Base UI primitives
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── textarea.tsx
│   │   ├── select.tsx
│   │   ├── checkbox.tsx
│   │   ├── toggle.tsx
│   │   ├── card.tsx
│   │   ├── modal.tsx
│   │   ├── tabs.tsx
│   │   ├── toast.tsx
│   │   ├── badge.tsx
│   │   ├── tooltip.tsx
│   │   └── index.ts              # Barrel export
│   │
│   ├── layout/                   # Layout components
│   │   ├── app-shell.tsx         # Main app shell with sidebar
│   │   ├── sidebar.tsx           # Navigation sidebar
│   │   ├── top-bar.tsx           # Header with logo/theme/user
│   │   └── index.ts
│   │
│   ├── agent-builder/            # Builder-specific components
│   │   ├── description-section.tsx
│   │   ├── type-section.tsx
│   │   ├── tools-section.tsx
│   │   ├── advanced-section.tsx
│   │   ├── section-panel.tsx
│   │   ├── prompt-suggestions.tsx
│   │   ├── tool-tile.tsx
│   │   └── index.ts
│   │
│   ├── code-editor/              # Monaco editor components
│   │   ├── code-panel.tsx        # Main code preview container
│   │   ├── file-tabs.tsx         # Tab bar for files
│   │   ├── validation-panel.tsx  # Validation status display
│   │   ├── monaco-wrapper.tsx    # Monaco editor wrapper
│   │   └── index.ts
│   │
│   ├── agents/                   # Agent list components
│   │   ├── agent-card.tsx
│   │   ├── agent-grid.tsx
│   │   ├── agent-list.tsx
│   │   └── index.ts
│   │
│   └── actions/                  # Action components
│       ├── generate-button.tsx
│       ├── validate-button.tsx
│       ├── deploy-button.tsx
│       └── index.ts
│
├── hooks/
│   ├── use-agent-generator.ts    # Generation state hook
│   ├── use-deployment.ts         # Deployment state hook
│   ├── use-form-validation.ts    # Form validation hook
│   ├── use-local-storage.ts      # Persistence hook
│   └── index.ts
│
├── lib/
│   ├── api.ts                    # API client (PROVIDED)
│   ├── utils.ts                  # Utility functions
│   └── constants.ts              # App constants
│
├── types/
│   └── index.ts                  # TypeScript types (PROVIDED)
│
├── store/                        # State management (Zustand/Jotai)
│   ├── builder-store.ts          # Builder form state
│   ├── code-store.ts             # Code editor state
│   └── index.ts
│
├── styles/
│   ├── globals.css               # Global styles + Tailwind
│   ├── variables.css             # CSS custom properties
│   └── themes/
│       ├── dark.css
│       └── light.css
│
├── public/
│   ├── icons/
│   └── images/
│
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js
├── Dockerfile
└── README.md
```

## API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `http://localhost:8001/api/generate-agent` | POST | Generate agent from description |
| `http://localhost:8001/api/validate-code` | POST | Validate generated code |
| `http://localhost:8001/api/regenerate` | POST | Regenerate with modifications |
| `http://localhost:8001/api/agents` | GET | List saved agents |
| `http://localhost:8001/api/agents/{id}` | GET/PUT/DELETE | CRUD operations |
| `http://localhost:8002/api/deploy` | POST | Deploy agent to container |

## Key Dependencies

```json
{
  "dependencies": {
    "next": "^15.x",
    "react": "^19.x",
    "react-dom": "^19.x",
    "@monaco-editor/react": "^4.x",
    "react-hook-form": "^7.x",
    "zod": "^3.x",
    "@hookform/resolvers": "^3.x",
    "zustand": "^4.x",
    "tailwindcss": "^4.x"
  }
}
```

## Environment Variables

```env
# .env.local
NEXT_PUBLIC_AGENT_GENERATOR_URL=http://localhost:8001
NEXT_PUBLIC_DOCKER_ORCHESTRATOR_URL=http://localhost:8002
```

## Build Commands

```bash
# Development
npm run dev          # Start on port 3000

# Production
npm run build
npm run start

# Docker
docker build -t laias-studio-ui .
docker run -p 3000:3000 laias-studio-ui
```

## Port Assignment

**Studio UI runs on port 3000**

## Provided Files (Already Created)

| File | Purpose |
|------|---------|
| `types/index.ts` | TypeScript types, form defaults, prompt suggestions |
| `lib/api.ts` | API client with all Studio-specific functions |

## Shared Dependencies (Do Not Modify)

| File | Purpose |
|------|---------|
| `../shared/types/agent-generator.ts` | Auto-generated from OpenAPI |
| `../shared/types/docker-orchestrator.ts` | Auto-generated from OpenAPI |
| `../shared/types/index.ts` | Type re-exports and utilities |
| `../shared/lib/api-client.ts` | Base API client |

## Team Responsibilities

| Component Area | Team Member Focus |
|----------------|-------------------|
| `components/ui/` | Base component library |
| `components/layout/` | App shell, navigation |
| `components/agent-builder/` | Form sections, tool selection |
| `components/code-editor/` | Monaco integration, validation display |
| `components/agents/` | Agent list, cards, actions |
| `hooks/` | Custom React hooks |
| `store/` | State management |
| `app/` | Page routing and layouts |
