# LAIAS Ultra-Grade Design System Blueprint v2.0

## Master Design Document for Builder Agent Execution

**Classification:** Technical Design Specification
**Standard:** Elite / Bleeding-Edge 2026
**Compliance Target:** WCAG 2.2 AA (enhanced to AAA where feasible)

---

# SECTION A: DEEP ANALYSIS — Current State Audit

## A.1 Identified Structural Weaknesses

| Category | Current State | Issue | Severity |
|----------|---------------|-------|----------|
| **Token Architecture** | Single-layer CSS variables | Lacks semantic abstraction; no theme-aware derivations | High |
| **Motion System** | Static duration values (150-200ms) | No physics-based animations; no gesture support | High |
| **Typography** | Fixed pixel scale | No fluid typography; no variable font strategy | Medium |
| **Depth System** | Single shadow token | No spatial hierarchy; no glass morphism layer | Medium |
| **Component States** | Implicit state management | No state machine formalization; race condition risk | High |
| **Accessibility** | WCAG AA baseline | Missing reduced-motion, high-contrast modes | Medium |
| **Data Visualization** | Static chart descriptions | No dynamic SVG rendering specs; no real-time update patterns | High |
| **Loading States** | Basic spinner mention | No skeleton specs; no streaming UI patterns for AI | High |

## A.2 Outdated UX Paradigms Detected

1. **Static Glow Effects** — Current box-shadow approach lacks depth animation
2. **Binary Theme Toggle** — Missing intermediate contrast modes
3. **Polling-Based Updates** — WebSocket mentioned but no reconnection/specs
4. **Form-Centric Generation** — No conversational/iterative AI interaction patterns
5. **Grid-Heavy Layouts** — No masonry/adaptive density for varying data volumes

---

# SECTION B: AGENTIC PLANNING — Abstract Structural Framework

## B.1 Core Modular Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        LAIAS DESIGN SYSTEM ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     TOKEN LAYER (Foundation)                         │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐  │    │
│  │  │   Global    │  │  Semantic   │  │     Component-Level         │  │    │
│  │  │   Primitives│  │   Aliases   │  │     Overrides               │  │    │
│  │  │  (RAW)      │→ │  (Context)  │→ │     (Scoped)                │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     ATOM LAYER (Primitives)                          │    │
│  │  Color · Typography · Spacing · Elevation · Motion · Sound          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                   MOLECULE LAYER (Composites)                        │    │
│  │  Button · Input · Badge · Icon · Avatar · Tooltip · Progress       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                   ORGANISM LAYER (Complex)                           │    │
│  │  Card · Modal · DataTable · LogViewer · CodeEditor · CommandBar    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                   TEMPLATE LAYER (Layouts)                           │    │
│  │  AppShell · BuilderCanvas · DashboardGrid · DetailPanel            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## B.2 Interaction State Machine Specification

Every interactive component MUST implement this state graph:

```
┌─────────┐     focus     ┌─────────┐     activate    ┌──────────┐
│  IDLE   │──────────────▶│ FOCUSED │────────────────▶│ ACTIVE   │
└─────────┘               └─────────┘                 └──────────┘
     ▲                          │                          │
     │                          │ blur                     │ complete
     │                          ▼                          │ cancel
     │                    ┌─────────┐                      │
     └────────────────────│  IDLE   │◀─────────────────────┘
                          └─────────┘
                               │
                               │ disable
                               ▼
                         ┌──────────┐
                         │ DISABLED │
                         └──────────┘
                               │
                               │ enable
                               ▼
                          ┌─────────┐
                          │  IDLE   │
                          └─────────┘

EXTENDED STATES (for async operations):
┌──────────┐    start    ┌─────────┐    success    ┌──────────┐
│  READY   │────────────▶│ LOADING │──────────────▶│ SUCCESS  │
└──────────┘             └─────────┘               └──────────┘
                               │
                               │ error
                               ▼
                         ┌──────────┐
                         │  ERROR   │
                         └──────────┘
```

## B.3 Animation Logic Framework

### Easing Functions (Physics-Based)

```typescript
interface EasingPresets {
  // Standard transitions
  easeOut: 'cubic-bezier(0.16, 1, 0.3, 1)';
  easeInOut: 'cubic-bezier(0.65, 0, 0.35, 1)';

  // Spring physics (overshoot)
  springGentle: 'cubic-bezier(0.34, 1.56, 0.64, 1)';
  springSnappy: 'cubic-bezier(0.68, -0.6, 0.32, 1.6)';

  // Mechanical (no overshoot)
  mechanical: 'cubic-bezier(0.4, 0, 0.2, 1)';

  // Expressive (for hero moments)
  expressive: 'cubic-bezier(0.22, 1, 0.36, 1)';
}
```

### Duration Scale

| Token | Duration | Use Case |
|-------|----------|----------|
| `--duration-instant` | 50ms | Micro-feedback (hover states) |
| `--duration-fast` | 100ms | Simple transitions |
| `--duration-normal` | 200ms | Standard interactions |
| `--duration-slow` | 350ms | Complex reveals |
| `--duration-slower` | 500ms | Page transitions |
| `--duration-slowest` | 800ms | Hero animations |

---

# SECTION C: ULTRA-GRADE UPGRADES

## C.1 Advanced Token System (Three-Layer Architecture)

### Layer 1: Global Primitives (Source of Truth)

```json
{
  "global": {
    "colors": {
      "brand": {
        "cyan": { "50": "#E6FBFF", "100": "#CCF7FF", "200": "#99EFFF", "300": "#66E7FF", "400": "#33DFFF", "500": "#2DE2FF", "600": "#24B5CC", "700": "#1B8899", "800": "#125B66", "900": "#092E33" },
        "purple": { "50": "#F3ECFF", "100": "#E7D9FF", "200": "#CFB3FF", "300": "#B78DFF", "400": "#9F67FF", "500": "#8E5CFF", "600": "#724ACC", "700": "#563899", "800": "#3B2666", "900": "#1F1333" },
        "pink": { "50": "#FFE6F2", "100": "#FFCCE5", "200": "#FF99CC", "300": "#FF66B3", "400": "#FF339A", "500": "#FF4FA3", "600": "#CC3F82", "700": "#992F62", "800": "#662041", "900": "#331021" }
      },
      "neutral": {
        "dark": { "900": "#0B1020", "800": "#111C36", "700": "#1E2746", "600": "#2A3456", "500": "#3D4666" },
        "light": { "100": "#F4F7FF", "200": "#E6ECFF", "300": "#D8E2FF", "400": "#C4D0FF", "500": "#A8BAF0" }
      },
      "semantic": {
        "success": "#22C55E",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "info": "#38BDF8"
      }
    },
    "typography": {
      "fontFamilies": {
        "display": "Inter",
        "body": "Inter",
        "mono": "JetBrains Mono"
      },
      "fontWeights": {
        "regular": 400,
        "medium": 500,
        "semibold": 600,
        "bold": 700
      }
    },
    "spacing": {
      "base": 4,
      "scale": [0, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96, 128]
    },
    "radii": {
      "none": 0,
      "sm": 6,
      "md": 10,
      "lg": 16,
      "xl": 24,
      "full": 9999
    },
    "shadows": {
      "sm": "0 1px 2px rgba(0, 0, 0, 0.05)",
      "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
      "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
      "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.1)",
      "inner": "inset 0 2px 4px rgba(0, 0, 0, 0.05)"
    }
  }
}
```

### Layer 2: Semantic Aliases (Context-Aware)

```json
{
  "semantic": {
    "dark": {
      "background": {
        "primary": "{global.colors.neutral.dark.900}",
        "secondary": "{global.colors.neutral.dark.800}",
        "tertiary": "{global.colors.neutral.dark.700}",
        "elevated": "{global.colors.neutral.dark.600}",
        "overlay": "rgba(11, 16, 32, 0.85)"
      },
      "surface": {
        "default": "{global.colors.neutral.dark.800}",
        "hover": "{global.colors.neutral.dark.700}",
        "active": "{global.colors.neutral.dark.600}",
        "disabled": "rgba(255, 255, 255, 0.04)"
      },
      "border": {
        "default": "rgba(255, 255, 255, 0.08)",
        "subtle": "rgba(255, 255, 255, 0.04)",
        "strong": "rgba(255, 255, 255, 0.14)",
        "focus": "{global.colors.brand.cyan.500}"
      },
      "text": {
        "primary": "{global.colors.neutral.light.100}",
        "secondary": "#AAB3C5",
        "muted": "#6F7A96",
        "disabled": "rgba(255, 255, 255, 0.38)"
      },
      "accent": {
        "primary": "{global.colors.brand.cyan.500}",
        "secondary": "{global.colors.brand.purple.500}",
        "tertiary": "{global.colors.brand.pink.500}"
      }
    },
    "light": {
      "background": {
        "primary": "{global.colors.neutral.light.100}",
        "secondary": "{global.colors.neutral.light.200}",
        "tertiary": "{global.colors.neutral.light.300}",
        "elevated": "#FFFFFF",
        "overlay": "rgba(11, 16, 32, 0.50)"
      },
      "surface": {
        "default": "{global.colors.neutral.light.200}",
        "hover": "{global.colors.neutral.light.300}",
        "active": "{global.colors.neutral.light.400}",
        "disabled": "rgba(0, 0, 0, 0.04)"
      },
      "border": {
        "default": "rgba(0, 0, 0, 0.08)",
        "subtle": "rgba(0, 0, 0, 0.04)",
        "strong": "rgba(0, 0, 0, 0.14)",
        "focus": "{global.colors.brand.cyan.500}"
      },
      "text": {
        "primary": "{global.colors.neutral.dark.900}",
        "secondary": "#334155",
        "muted": "#64748B",
        "disabled": "rgba(0, 0, 0, 0.38)"
      },
      "accent": {
        "primary": "{global.colors.brand.cyan.500}",
        "secondary": "{global.colors.brand.purple.500}",
        "tertiary": "{global.colors.brand.pink.500}"
      }
    }
  }
}
```

### Layer 3: Component Overrides (Scoped)

```json
{
  "components": {
    "button": {
      "primary": {
        "background": "{semantic.accent.primary}",
        "color": "{semantic.dark.background.primary}",
        "glow": "0 0 20px rgba(45, 226, 255, 0.4)",
        "glowHover": "0 0 30px rgba(45, 226, 255, 0.6)"
      },
      "secondary": {
        "background": "transparent",
        "border": "{semantic.accent.secondary}",
        "color": "{semantic.accent.secondary}"
      },
      "destructive": {
        "background": "{global.colors.semantic.error}",
        "color": "#FFFFFF"
      }
    },
    "card": {
      "container": {
        "background": "{semantic.surface.default}",
        "border": "{semantic.border.default}",
        "shadow": "{global.shadows.md}",
        "glowSelected": "0 0 0 1px {semantic.accent.primary}, 0 0 24px rgba(45, 226, 255, 0.15)"
      }
    },
    "input": {
      "default": {
        "background": "{semantic.surface.default}",
        "border": "{semantic.border.default}",
        "color": "{semantic.text.primary}"
      },
      "focus": {
        "border": "{semantic.border.focus}",
        "glow": "0 0 0 3px rgba(45, 226, 255, 0.15)"
      },
      "error": {
        "border": "{global.colors.semantic.error}",
        "glow": "0 0 0 3px rgba(239, 68, 68, 0.15)"
      }
    }
  }
}
```

## C.2 Fluid Typography System

```css
/* Type Scale with Fluid Sizing */
:root {
  /* Base: 16px at 375px viewport, 18px at 1440px viewport */
  --font-size-xs: clamp(0.625rem, 0.5rem + 0.25vw, 0.75rem);      /* 10-12px */
  --font-size-sm: clamp(0.75rem, 0.625rem + 0.35vw, 0.875rem);    /* 12-14px */
  --font-size-base: clamp(0.875rem, 0.75rem + 0.5vw, 1rem);       /* 14-16px */
  --font-size-lg: clamp(1rem, 0.875rem + 0.65vw, 1.125rem);       /* 16-18px */
  --font-size-xl: clamp(1.125rem, 0.875rem + 1vw, 1.25rem);       /* 18-20px */
  --font-size-2xl: clamp(1.25rem, 1rem + 1.25vw, 1.5rem);         /* 20-24px */
  --font-size-3xl: clamp(1.5rem, 1rem + 2vw, 2rem);               /* 24-32px */
  --font-size-4xl: clamp(2rem, 1.25rem + 3vw, 3rem);              /* 32-48px */
  --font-size-5xl: clamp(2.5rem, 1.5rem + 4vw, 4rem);             /* 40-64px */

  /* Line Heights */
  --line-height-tight: 1.2;
  --line-height-snug: 1.35;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.65;

  /* Letter Spacing */
  --letter-spacing-tight: -0.025em;
  --letter-spacing-normal: 0;
  --letter-spacing-wide: 0.025em;
  --letter-spacing-wider: 0.05em;
}

/* Gradient Text (Headings Only) */
.text-gradient-brand {
  background: linear-gradient(135deg, var(--accent-cyan) 0%, var(--accent-purple) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
```

## C.3 Advanced Glow & Depth System

```css
/* Glow System */
:root {
  /* Cyan Glows */
  --glow-cyan-sm: 0 0 10px rgba(45, 226, 255, 0.25);
  --glow-cyan-md: 0 0 20px rgba(45, 226, 255, 0.35);
  --glow-cyan-lg: 0 0 40px rgba(45, 226, 255, 0.45);
  --glow-cyan-ring: 0 0 0 1px rgba(45, 226, 255, 0.5), 0 0 20px rgba(45, 226, 255, 0.3);

  /* Purple Glows */
  --glow-purple-sm: 0 0 10px rgba(142, 92, 255, 0.25);
  --glow-purple-md: 0 0 22px rgba(142, 92, 255, 0.35);
  --glow-purple-lg: 0 0 44px rgba(142, 92, 255, 0.45);

  /* Status Glows */
  --glow-success: 0 0 20px rgba(34, 197, 94, 0.3);
  --glow-warning: 0 0 20px rgba(245, 158, 11, 0.3);
  --glow-error: 0 0 20px rgba(239, 68, 68, 0.4);

  /* Focus Ring */
  --focus-ring: 0 0 0 2px var(--bg-primary), 0 0 0 4px var(--accent-cyan);
  --focus-ring-inset: inset 0 0 0 2px var(--accent-cyan);
}

/* Elevation Depth System */
:root {
  --elevation-0: none;
  --elevation-1: 0 1px 2px rgba(0, 0, 0, 0.12);
  --elevation-2: 0 4px 8px rgba(0, 0, 0, 0.14);
  --elevation-3: 0 8px 16px rgba(0, 0, 0, 0.16);
  --elevation-4: 0 12px 24px rgba(0, 0, 0, 0.18);
  --elevation-5: 0 20px 40px rgba(0, 0, 0, 0.22);
}

/* Glass Morphism Layer */
.glass-surface {
  background: rgba(17, 28, 54, 0.6);
  backdrop-filter: blur(12px) saturate(180%);
  -webkit-backdrop-filter: blur(12px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

/* Ambient Light Effect */
.ambient-glow {
  position: relative;
}

.ambient-glow::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(
    ellipse at 50% 0%,
    rgba(45, 226, 255, 0.08) 0%,
    transparent 50%
  );
  pointer-events: none;
  z-index: -1;
}
```

## C.4 Micro-Interaction Specifications

### Button Interaction

```typescript
interface ButtonInteraction {
  states: {
    default: {
      transform: 'scale(1)',
      boxShadow: 'var(--elevation-1)',
      transition: 'all var(--duration-fast) var(--ease-out)'
    },
    hover: {
      transform: 'scale(1.02)',
      boxShadow: 'var(--elevation-2), var(--glow-cyan-sm)',
      filter: 'brightness(1.05)'
    },
    active: {
      transform: 'scale(0.98)',
      boxShadow: 'var(--elevation-1)',
      transition: 'all var(--duration-instant) var(--ease-out)'
    },
    focus: {
      boxShadow: 'var(--focus-ring)',
      outline: 'none'
    },
    loading: {
      cursor: 'wait',
      opacity: 0.8,
      pointerEvents: 'none'
    },
    disabled: {
      opacity: 0.5,
      cursor: 'not-allowed',
      filter: 'grayscale(0.5)'
    }
  },
  haptic: {
    tap: 'light impact',
    longPress: 'medium impact'
  }
}
```

### Card Selection Animation

```typescript
interface CardSelectionAnimation {
  sequence: [
    { property: 'border-color', from: 'transparent', to: 'var(--accent-cyan)', duration: 100 },
    { property: 'box-shadow', from: 'none', to: 'var(--glow-cyan-ring)', duration: 200, delay: 50 },
    { property: 'transform', from: 'scale(1)', to: 'scale(1.01)', duration: 150 }
  ],
  easing: 'var(--ease-spring-gentle)',
  exitDuration: 150
}
```

### Log Stream Animation

```typescript
interface LogStreamAnimation {
  entryAnimation: {
    opacity: [0, 1],
    transform: ['translateY(-8px)', 'translateY(0)'],
    duration: 150,
    easing: 'var(--ease-out)'
  },
  scrollBehavior: 'smooth',
  autoScrollIndicator: {
    position: 'bottom-right',
    pulse: true,
    pulseDuration: 2000
  }
}
```

## C.5 AI-Native Loading Patterns

### Streaming Generation Progress

```typescript
interface StreamingProgressPattern {
  progressBar: {
    type: 'indeterminate-scan',
    gradient: 'linear-gradient(90deg, var(--accent-cyan) 0%, var(--accent-purple) 100%)',
    height: 2,
    animation: {
      duration: 1500,
      easing: 'linear',
      iteration: 'infinite'
    }
  },
  skeleton: {
    baseColor: 'var(--surface-2)',
    highlightColor: 'var(--surface-3)',
    animation: 'shimmer 1.5s ease-in-out infinite'
  },
  tokenReveal: {
    type: 'typewriter',
    speed: '15ms per character',
    cursor: {
      char: '▌',
      color: 'var(--accent-cyan)',
      blink: true,
      blinkDuration: 530
    }
  }
}
```

### Generation State Visualization

```typescript
interface GenerationStateVisual {
  states: {
    idle: {
      icon: 'sparkle',
      color: 'var(--text-muted)',
      label: 'Ready to generate'
    },
    analyzing: {
      icon: 'brain-pulse',
      color: 'var(--accent-purple)',
      label: 'Analyzing description...',
      animation: 'pulse 1.5s ease-in-out infinite'
    },
    generating: {
      icon: 'code-stream',
      color: 'var(--accent-cyan)',
      label: 'Generating code...',
      animation: 'shimmer 2s linear infinite'
    },
    validating: {
      icon: 'check-circle-outline',
      color: 'var(--info)',
      label: 'Validating patterns...'
    },
    complete: {
      icon: 'check-circle',
      color: 'var(--success)',
      label: 'Generation complete'
    },
    error: {
      icon: 'error-circle',
      color: 'var(--error)',
      label: 'Generation failed'
    }
  }
}
```

## C.6 Data Visualization Enhancement

### Dynamic SVG Chart Specifications

```typescript
interface ChartVisualSpec {
  gridLines: {
    color: 'rgba(255, 255, 255, 0.04)',
    strokeWidth: 1,
    dashArray: '4 4'
  },
  dataLine: {
    strokeWidth: 2,
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
    gradient: {
      id: 'data-gradient',
      stops: [
        { offset: '0%', color: 'var(--accent-cyan)', opacity: 1 },
        { offset: '100%', color: 'var(--accent-purple)', opacity: 1 }
      ]
    },
    glowFilter: {
      stdDeviation: 3,
      floodColor: 'var(--accent-cyan)',
      floodOpacity: 0.4
    }
  },
  areaFill: {
    gradient: {
      stops: [
        { offset: '0%', color: 'var(--accent-cyan)', opacity: 0.2 },
        { offset: '100%', color: 'var(--accent-cyan)', opacity: 0 }
      ]
    }
  },
  tooltip: {
    background: 'var(--surface-elevated)',
    border: '1px solid var(--border-strong)',
    borderRadius: 'var(--radius-md)',
    boxShadow: 'var(--elevation-4)',
    padding: '8px 12px'
  },
  animation: {
    drawDuration: 800,
    easing: 'var(--ease-expressive)',
    pointRevealDelay: 50,
    updateTransition: 300
  }
}
```

### Real-Time Metric Update Pattern

```typescript
interface MetricUpdatePattern {
  numberTransition: {
    type: 'tween',
    duration: 400,
    easing: 'var(--ease-out)',
    formatLocale: 'en-US'
  },
  sparkline: {
    maxPoints: 20,
    updateInterval: 1000,
    strokeColor: 'var(--accent-cyan)',
    fillGradient: true
  },
  statusIndicator: {
    increasing: { icon: 'arrow-up', color: 'var(--success)' },
    decreasing: { icon: 'arrow-down', color: 'var(--error)' },
    stable: { icon: 'minus', color: 'var(--text-muted)' }
  }
}
```

---

# SECTION D: LAYOUT ARCHITECTURE

## D.1 Responsive Grid System

```css
:root {
  /* Breakpoints */
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1280px;
  --breakpoint-2xl: 1536px;

  /* Container Widths */
  --container-sm: 640px;
  --container-md: 768px;
  --container-lg: 1024px;
  --container-xl: 1280px;
  --container-2xl: 1440px;

  /* Grid */
  --grid-columns: 12;
  --grid-gap: var(--space-6); /* 24px */
  --grid-gap-sm: var(--space-4); /* 16px */
}

/* App Shell Layout */
.app-shell {
  display: grid;
  grid-template-columns: auto 1fr;
  grid-template-rows: auto 1fr;
  grid-template-areas:
    "sidebar header"
    "sidebar main";
  height: 100vh;
  overflow: hidden;
}

.app-shell--sidebar-collapsed {
  grid-template-columns: var(--sidebar-collapsed-width) 1fr;
}

/* Builder Canvas (3-Column) */
.builder-canvas {
  display: grid;
  grid-template-columns: 240px 1fr 400px;
  gap: var(--space-4);
  height: 100%;
  overflow: hidden;
}

@media (max-width: 1280px) {
  .builder-canvas {
    grid-template-columns: 200px 1fr 320px;
  }
}

@media (max-width: 1024px) {
  .builder-canvas {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr auto;
  }
}
```

## D.2 Z-Index Scale

```css
:root {
  --z-below: -1;
  --z-base: 0;
  --z-above: 1;
  --z-dropdown: 1000;
  --z-sticky: 1100;
  --z-fixed: 1200;
  --z-modal-backdrop: 1300;
  --z-modal: 1400;
  --z-popover: 1500;
  --z-tooltip: 1600;
  --z-toast: 1700;
  --z-maximum: 9999;
}
```

---

# SECTION E: INTERACTION LOGIC SPECIFICATION

## E.1 Keyboard Navigation Matrix

| Context | Key | Action |
|---------|-----|--------|
| Global | `Tab` | Move focus forward |
| Global | `Shift + Tab` | Move focus backward |
| Global | `?` | Open keyboard shortcuts modal |
| Sidebar | `↑` / `↓` | Navigate items |
| Sidebar | `Enter` | Select item |
| Tabs | `←` / `→` | Switch tabs |
| Cards Grid | `Arrow keys` | Navigate grid |
| Cards Grid | `Enter` / `Space` | Select card |
| Modal | `Escape` | Close modal |
| Dropdown | `↑` / `↓` | Navigate options |
| Dropdown | `Enter` | Select option |
| Code Editor | `Cmd/Ctrl + S` | Save (custom handler) |
| Log Viewer | `f` | Focus search |
| Log Viewer | `c` | Copy selected log |

## E.2 WebSocket Connection State Machine

```typescript
type ConnectionState = 'connecting' | 'connected' | 'disconnecting' | 'disconnected' | 'error';

interface WebSocketConfig {
  reconnectAttempts: 5;
  reconnectDelay: 1000; // with exponential backoff
  heartbeatInterval: 30000;
  connectionTimeout: 10000;
  visualIndicators: {
    connecting: { icon: 'wifi-pulse', color: 'var(--warning)', animate: true },
    connected: { icon: 'wifi', color: 'var(--success)', animate: false },
    disconnected: { icon: 'wifi-off', color: 'var(--error)', animate: false },
    error: { icon: 'wifi-error', color: 'var(--error)', animate: true }
  }
}
```

## E.3 Form Validation Timing

```typescript
interface ValidationTiming {
  debounce: {
    description: 500, // ms after last keystroke
    default: 300
  },
  triggers: {
    onBlur: true,
    onSubmit: true,
    onDebounce: ['description'] // fields that validate on debounce
  },
  feedback: {
    delay: 100, // before showing error
    successClearDelay: 0
  }
}
```

---

# SECTION F: ACCESSIBILITY ENHANCEMENTS

## F.1 Reduced Motion Mode

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}

/* User-overrideable class */
[data-reduced-motion="true"] *,
[data-reduced-motion="true"] *::before,
[data-reduced-motion="true"] *::after {
  animation-duration: 0.01ms !important;
  transition-duration: 0.01ms !important;
}
```

## F.2 High Contrast Mode

```css
@media (prefers-contrast: high) {
  :root {
    --border-default: rgba(255, 255, 255, 0.5);
    --border-strong: rgba(255, 255, 255, 0.75);
    --text-muted: #A0A0A0;
  }

  .button--primary {
    border: 2px solid currentColor;
  }

  .status-badge {
    border: 2px solid currentColor;
  }
}
```

## F.3 Focus Visible Polyfill Pattern

```css
/* Hide focus ring if not using keyboard */
:focus:not(:focus-visible) {
  outline: none;
  box-shadow: none;
}

/* Show focus ring only for keyboard navigation */
:focus-visible {
  outline: 2px solid var(--accent-cyan);
  outline-offset: 2px;
}
```

---

# SECTION G: COMPONENT BLUEPRINT CATALOG

## G.1 Button Component

```typescript
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive' | 'link';
  size: 'sm' | 'md' | 'lg';
  iconLeft?: React.ReactNode;
  iconRight?: React.ReactNode;
  loading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
  children: React.ReactNode;
  asChild?: boolean;
}

// Visual Parameters
const buttonVisualConfig = {
  primary: {
    background: 'var(--accent-cyan)',
    color: 'var(--bg-primary)',
    border: 'none',
    glow: 'var(--glow-cyan-sm)',
    glowHover: 'var(--glow-cyan-md)'
  },
  secondary: {
    background: 'transparent',
    color: 'var(--accent-purple)',
    border: '1px solid var(--accent-purple)',
    glow: 'var(--glow-purple-sm)',
    glowHover: 'var(--glow-purple-md)'
  },
  destructive: {
    background: 'var(--error)',
    color: '#FFFFFF',
    border: 'none',
    glow: 'var(--glow-error)'
  }
};
```

## G.2 Card Component

```typescript
interface CardProps {
  variant: 'default' | 'elevated' | 'outlined' | 'interactive' | 'status';
  title?: string;
  description?: string;
  status?: 'running' | 'stopped' | 'error' | 'pending';
  selected?: boolean;
  hoverable?: boolean;
  compact?: boolean;
  headerAction?: React.ReactNode;
  footerContent?: React.ReactNode;
  children: React.ReactNode;
}

// State Visual Map
const cardStateVisuals = {
  default: {
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    boxShadow: 'var(--elevation-1)'
  },
  hover: {
    background: 'var(--surface-hover)',
    boxShadow: 'var(--elevation-2)'
  },
  selected: {
    border: '1px solid var(--accent-cyan)',
    boxShadow: 'var(--glow-cyan-ring)'
  },
  'status-running': {
    accentBar: { position: 'left', color: 'var(--success)', width: 3 }
  },
  'status-error': {
    accentBar: { position: 'left', color: 'var(--error)', width: 3 }
  }
};
```

## G.3 Log Viewer Component

```typescript
interface LogViewerProps {
  containerId: string;
  websocketUrl: string;
  maxLines?: number;
  showTimestamp?: boolean;
  showLevel?: boolean;
  autoScroll?: boolean;
  searchEnabled?: boolean;
  levelFilter?: ('info' | 'warn' | 'error' | 'debug')[];
  onExport?: () => void;
}

// Log Level Visual Map
const logLevelVisuals = {
  info: {
    indicator: { color: 'var(--info)', width: 3 },
    icon: 'info-circle',
    text: 'var(--text-primary)'
  },
  warn: {
    indicator: { color: 'var(--warning)', width: 3 },
    icon: 'warning-triangle',
    text: 'var(--text-primary)'
  },
  error: {
    indicator: { color: 'var(--error)', width: 3 },
    icon: 'error-circle',
    text: 'var(--text-primary)'
  },
  debug: {
    indicator: { color: 'var(--text-muted)', width: 2 },
    icon: 'bug',
    text: 'var(--text-muted)'
  }
};

// Virtualization Config
const logVirtualization = {
  overscan: 20,
  estimatedLineHeight: 24,
  scrollToBottomOnNew: true,
  scrollToBottomButton: {
    showThreshold: 200, // pixels from bottom
    animation: 'fade-slide-up'
  }
};
```

## G.4 Code Editor Panel

```typescript
interface CodeEditorPanelProps {
  files: Array<{
    name: string;
    language: 'python' | 'yaml' | 'text';
    content: string;
    readOnly?: boolean;
    dirty?: boolean;
  }>;
  activeFile?: string;
  validation?: {
    status: 'pending' | 'valid' | 'warning' | 'error';
    messages: Array<{
      line?: number;
      column?: number;
      severity: 'error' | 'warning' | 'info';
      message: string;
    }>;
  };
  onFileChange?: (filename: string, content: string) => void;
  onFileSelect?: (filename: string) => void;
}

// Monaco Theme Config
const monacoThemeConfig = {
  base: 'vs-dark',
  inherit: true,
  rules: [
    { token: 'comment', foreground: '6F7A96', fontStyle: 'italic' },
    { token: 'keyword', foreground: '8E5CFF' },
    { token: 'string', foreground: '22C55E' },
    { token: 'number', foreground: 'FF4FA3' },
    { token: 'type', foreground: '2DE2FF' }
  ],
  colors: {
    'editor.background': '#111C36',
    'editor.foreground': '#F4F7FF',
    'editorLineNumber.foreground': '#3D4666',
    'editorLineNumber.activeForeground': '#AAB3C5',
    'editor.selectionBackground': '#2DE2FF30',
    'editor.lineHighlightBackground': '#1E2746',
    'editorCursor.foreground': '#2DE2FF'
  }
};
```

## G.5 Tool Selection Tile

```typescript
interface ToolTileProps {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  selected: boolean;
  disabled?: boolean;
  onSelect: (id: string, selected: boolean) => void;
}

// Visual States
const toolTileVisuals = {
  default: {
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    cursor: 'pointer'
  },
  hover: {
    background: 'var(--surface-hover)',
    borderColor: 'var(--border-strong)'
  },
  selected: {
    background: 'rgba(45, 226, 255, 0.05)',
    border: '1px solid var(--accent-cyan)',
    boxShadow: 'var(--glow-cyan-sm)'
  },
  disabled: {
    opacity: 0.5,
    cursor: 'not-allowed'
  }
};
```

## G.6 Status Badge

```typescript
interface StatusBadgeProps {
  status: 'running' | 'stopped' | 'error' | 'pending' | 'success';
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  pulse?: boolean;
  children?: string;
}

const statusBadgeConfig = {
  running: {
    color: 'var(--success)',
    icon: 'circle-filled',
    pulse: true,
    label: 'Running'
  },
  stopped: {
    color: 'var(--text-muted)',
    icon: 'circle',
    pulse: false,
    label: 'Stopped'
  },
  error: {
    color: 'var(--error)',
    icon: 'error-circle',
    pulse: false,
    label: 'Error'
  },
  pending: {
    color: 'var(--warning)',
    icon: 'clock',
    pulse: true,
    label: 'Pending'
  },
  success: {
    color: 'var(--success)',
    icon: 'check-circle',
    pulse: false,
    label: 'Success'
  }
};
```

---

# SECTION H: PAGE BLUEPRINTS

## H.1 Studio UI — /create Page

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ [Logo]  Studio  │  Control Room  │  Docs          [Theme Toggle] [Avatar]   │
├──────────────────────────────────────────────────────────────────────────────┤
│ ▸ Home         │ ┌────────────────────────────────────────────────────┐     │
│ ▸ Create Agent │ │ CREATE AGENT                           ● Draft    │     │
│ ▸ Agents       │ ├────────────────────────────────────────────────────┤     │
│ ▸ Templates    │ │ [Section Nav] │ [Form Area]       │ [Code Preview] │     │
│ ▸ Settings     │ │               │                   │                │     │
│                │ │ 1.Description │ ┌──────────────┐  │ ┌────────────┐ │     │
│                │ │ 2.Type        │ │ Describe...  │  │ │flow.py ▾  ≡│ │     │
│                │ │ 3.Tools    ✓  │ │              │  │ │            │ │     │
│                │ │ 4.Advanced    │ └──────────────┘  │ │ [Monaco]   │ │     │
│                │ │ 5.Deploy      │                   │ │            │ │     │
│                │ │               │ ┌──────────────┐  │ │            │ │     │
│                │ │               │ │ Agent Type   │  │ │            │ │     │
│                │ │               │ │ [Solo    ▾]  │  │ │            │ │     │
│                │ │               │ └──────────────┘  │ ├────────────┤ │     │
│                │ │               │                   │ │✓ Patterns  │ │     │
│                │ │               │ ┌──────────────┐  │ │⚠ 2 Warnings│ │     │
│                │ │               │ │ [Web Search] │  │ │✕ 0 Errors  │ │     │
│                │ │               │ │ [Scraper]    │  │ ├────────────┤ │     │
│                │ │               │ │ [Code Int.]  │  │ │[Validate]  │ │     │
│                │ │               │ │ [Database]   │  │ │[Deploy →]  │ │     │
│                │ │               │ └──────────────┘  │ └────────────┘ │     │
│                │ └───────────────┴───────────────────┴────────────────┘     │
└──────────────────────────────────────────────────────────────────────────────┘

INTERACTION STATES:
- Section Nav: Click to scroll, active = cyan left border
- Form: Real-time validation, debounced generation trigger
- Code Preview: Tab switch (animated), dirty indicator (dot)
- Deploy: Disabled until validation passes
```

## H.2 Control Room — /containers Page

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ [Logo]  Studio  │  Control Room  │  Docs          [Theme Toggle] [Avatar]   │
├──────────────────────────────────────────────────────────────────────────────┤
│ ▸ Dashboard    │ ┌────────────────────────────────────────────────────────┐ │
│ ▸ Containers   │ │ CONTAINERS       [Search...] [Filter▾] [⟳ Refresh]    │ │
│ ▸ Metrics      │ ├────────────────────────────────────────────────────────┤ │
│ ▸ Logs         │ │ ┌──────────────────┐ ┌──────────────────┐              │ │
│ ▸ Settings     │ │ │ ● Running        │ │ ● Running        │              │ │
│                │ │ │ Research Agent   │ │ Data Processor   │              │ │
│                │ │ │ CPU: 42%  MEM:   │ │ CPU: 18%  MEM:   │              │ │
│                │ │ │ 512MB            │ │ 256MB            │              │ │
│                │ │ │ Uptime: 2h 34m   │ │ Uptime: 45m      │              │ │
│                │ │ │ [▶][⏸][🗑]       │ │ [▶][⏸][🗑]       │              │ │
│                │ │ └──────────────────┘ └──────────────────┘              │ │
│                │ │ ┌──────────────────┐ ┌──────────────────┐              │ │
│                │ │ │ ○ Stopped        │ │ ● Error          │              │ │
│                │ │ │ Summary Writer   │ │ Web Scraper      │              │ │
│                │ │ │ —                │ │ Exit code: 1     │              │ │
│                │ │ │ —                │ │ Stopped: 5m ago  │              │ │
│                │ │ │ [▶][🗑]          │ │ [▶][📋 Logs]     │              │ │
│                │ │ └──────────────────┘ └──────────────────┘              │ │
│                │ └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘

INTERACTION STATES:
- Container Card: Hover = elevation + border glow
- Status Badge: Pulse animation for running/pending states
- Quick Actions: Tooltip on hover, confirmation for destructive
- Real-time: WebSocket updates every 5s, immediate on state change
```

---

# SECTION I: PERFORMANCE BUDGETS

| Metric | Target | Measurement |
|--------|--------|-------------|
| First Contentful Paint | < 1.5s | Lighthouse |
| Largest Contentful Paint | < 2.5s | Lighthouse |
| Time to Interactive | < 3.0s | Lighthouse |
| Cumulative Layout Shift | < 0.1 | Lighthouse |
| First Input Delay | < 100ms | Lighthouse |
| Bundle Size (Initial) | < 200KB | gzip |
| Bundle Size (Lazy) | < 50KB per chunk | gzip |
| Animation Frame Rate | 60fps | DevTools |
| WebSocket Reconnect | < 3s | Custom |

---

# SECTION J: IMPLEMENTATION PRIORITY

| Phase | Components | Priority |
|-------|------------|----------|
| **P0** | Token System, Button, Input, Card, Status Badge | Critical |
| **P1** | Modal, Tabs, Toast, Sidebar, TopBar | High |
| **P2** | DataTable, LogViewer, CodeEditor, ToolTile | High |
| **P3** | Charts, KPI Cards, Empty States | Medium |
| **P4** | Animations, Micro-interactions | Medium |
| **P5** | High Contrast, Advanced Accessibility | Low |

---

*END OF ULTRA-GRADE BLUEPRINT v2.0*
*Ready for Builder Agent Execution*
