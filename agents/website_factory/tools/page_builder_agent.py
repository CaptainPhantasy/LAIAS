"""
================================================================================
            WEBSITE FACTORY — PAGE BUILDER AGENT
            "Writes real files. Not strings. Files."
================================================================================

The page builder is the worker agent that actually writes Next.js TSX files
to disk. It receives the full spec for a page, the design system tokens, and
the existing codebase context, and it outputs complete, working React components.

Key behaviors:
- Reads the parsed spec. Follows it exactly.
- Writes files directly to disk via Python file I/O.
- After writing, runs `npx tsc --noEmit` to check for type errors.
- If there are type errors, fixes them before reporting done.
- Reports what it built to the todo manager.
- Never invents design decisions. Everything comes from the spec.

Author: LAIAS
Version: 1.0.0
================================================================================
"""

import os
import json
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog

from crewai import Agent, Task, Crew, Process, LLM

from .spec_parser import SiteSpec, PageSpec, ColorToken
from .todo_manager import TodoManager, TodoItem, TodoCategory, TodoPriority, TodoStatus

logger = structlog.get_logger()


# =============================================================================
# LLM CONFIGURATION
# =============================================================================


def get_builder_llm() -> LLM:
    """Get the LLM for building tasks."""
    provider = os.getenv("LAIAS_LLM_PROVIDER", "openai")

    if provider == "zai":
        return LLM(
            model="glm-4-plus",
            api_key=os.getenv("ZAI_API_KEY"),
            base_url="https://open.bigmodel.cn/api/paas/v4",
        )
    else:
        return LLM(model=os.getenv("DEFAULT_MODEL", "gpt-4o"), base_url="https://api.portkey.ai/v1", api_key=os.getenv("PORTKEY_API_KEY", ""))


# =============================================================================
# PAGE BUILDER
# =============================================================================


class PageBuilderAgent:
    """
    Builds a single page as real Next.js TSX files on disk.

    One instance per page build. Fresh context every time.
    The spec and todo manager are the only shared state.
    """

    MAX_TYPE_FIX_ATTEMPTS = 3
    IMPROVEMENT_THRESHOLD = 2.0  # % — matches the user's spec

    def __init__(
        self,
        project_path: str,
        spec: SiteSpec,
        todo: TodoManager,
    ):
        self.project_path = Path(project_path)
        self.spec = spec
        self.todo = todo
        self.llm = get_builder_llm()

    # =========================================================================
    # DESIGN SYSTEM CONTEXT
    # =========================================================================

    def _build_design_system_context(self) -> str:
        """Build a concise design system reference for the agent."""
        colors_str = "\n".join(
            f"  {c.name}: {c.hex_value} ({c.usage})" for c in self.spec.colors[:16]
        )

        nav_links_str = ", ".join(self.spec.nav_links)

        return f"""
DESIGN SYSTEM — FOLLOW EXACTLY:

COLORS:
{colors_str}

TYPOGRAPHY:
  Heading font: {self.spec.typography.heading_font}
  Body font: {self.spec.typography.body_font}
  Font scale: {json.dumps(self.spec.typography.scale)}

SPACING (base: {self.spec.spacing.base_unit}px):
  Scale: {json.dumps(self.spec.spacing.scale)}

FRAMEWORK: {self.spec.framework}
STYLING: {self.spec.styling}

NAVIGATION LINKS: {nav_links_str}
PRIMARY CTA: {self.spec.primary_cta}
SITE NAME: {self.spec.site_name}
TAGLINE: {self.spec.tagline}
"""

    # =========================================================================
    # EXISTING CODEBASE CONTEXT
    # =========================================================================

    def _read_existing_files(self) -> str:
        """Read existing shared components so the agent can import them."""
        context_parts = []

        # Read layout components
        layout_dir = self.project_path / "src" / "components" / "layout"
        if layout_dir.exists():
            for f in layout_dir.glob("*.tsx"):
                content = f.read_text()[:2000]  # First 2000 chars
                context_parts.append(
                    f"// EXISTING: {f.relative_to(self.project_path)}\n{content}"
                )

        # Read globals.css for design tokens
        globals_css = self.project_path / "src" / "styles" / "globals.css"
        if globals_css.exists():
            context_parts.append(
                f"// EXISTING: src/styles/globals.css\n{globals_css.read_text()[:1500]}"
            )

        # Read tailwind config if it exists
        tw_config = self.project_path / "tailwind.config.ts"
        if tw_config.exists():
            context_parts.append(
                f"// EXISTING: tailwind.config.ts\n{tw_config.read_text()[:1000]}"
            )

        return "\n\n".join(context_parts)

    # =========================================================================
    # MAIN BUILD
    # =========================================================================

    async def build_page(self, page: PageSpec, cycle: int = 1) -> Dict[str, Any]:
        """
        Build a page and write all files to disk.

        Returns a dict with:
        - files_written: list of file paths
        - type_errors: list of type errors (empty = clean)
        - success: bool
        """
        logger.info("Building page", page=page.name, cycle=cycle, path=page.path)

        # Determine output files
        if page.path == "/":
            page_file = self.project_path / "src" / "app" / "page.tsx"
        else:
            clean_path = page.path.lstrip("/")
            page_file = self.project_path / "src" / "app" / clean_path / "page.tsx"

        page_file.parent.mkdir(parents=True, exist_ok=True)

        # Build context for the agent
        design_context = self._build_design_system_context()
        existing_context = self._read_existing_files()
        page_copy = json.dumps(page.page_copy, indent=2) if page.page_copy else "{}"
        page_sections = json.dumps(page.sections, indent=2) if page.sections else "[]"

        # Get spec section for this page
        raw_spec_section = self.spec.raw_sections.get(
            page.name.lower().replace(" ", "_"), ""
        )[:3000]

        # Add todo task
        todo_item = self.todo.add_build_task(
            title=f"Build {page.name} page — cycle {cycle}",
            page=page.name,
            file_path=str(page_file),
            description=f"Write {page_file} following spec exactly",
            cycle=cycle,
        )
        self.todo.start(todo_item.id, agent="page_builder")

        # -----------------------------------------------------------------------
        # Create the builder agent
        # -----------------------------------------------------------------------
        builder = Agent(
            role="Expert Next.js Page Builder",
            goal=f"Write a complete, production-ready {page.name} page as a Next.js TSX component",
            backstory=f"""You are an expert Next.js developer who has built hundreds of
production websites. You write TypeScript/React code that is:
- Type-safe (no 'any', no TypeScript errors)
- Following the exact design spec provided
- Using Tailwind CSS classes that match the design tokens
- Responsive (mobile-first, works at 320px to 1920px)
- Accessible (ARIA labels, semantic HTML, proper heading hierarchy)
- Import-clean (no unused imports)

You NEVER approximate design values. If the spec says #0369a1, you use #0369a1.
If the spec says the heading font is {self.spec.typography.heading_font}, you use that font.
You write the COMPLETE file. No placeholders. No "// TODO". No "...".""",
            llm=self.llm,
            verbose=True,
            max_iter=20,
        )

        task = Task(
            description=f"""
Write the complete Next.js page component for: **{page.name.upper()}**
Output path: `{page_file.relative_to(self.project_path)}`
Page route: `{page.path}`
Page title: `{page.title}`

{design_context}

PAGE COPY AND CONTENT:
{page_copy}

PAGE SPEC:
{raw_spec_section}

EXISTING COMPONENTS TO IMPORT:
{existing_context}

REQUIREMENTS:
1. Use the Header and Footer components from @/components/layout if they exist
2. Every color must match the design system exactly (use Tailwind classes that map to those values or inline styles)
3. All interactive elements (buttons, links, forms) must be properly connected
4. Mobile-first responsive design
5. Proper TypeScript types — no 'any'
6. Clean imports — only import what you use
7. The file must be self-contained and ready to run with `npm run dev`

OUTPUT FORMAT:
Return ONLY the complete TypeScript file content. No explanation.
Start with the imports. End with the default export.
The output will be written directly to disk.
""",
            expected_output=f"Complete TypeScript/React file for {page.name} page, starting with imports",
            agent=builder,
        )

        crew = Crew(
            agents=[builder],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = await crew.kickoff_async()
        tsx_content = str(result).strip()

        # Clean up common LLM output artifacts
        tsx_content = self._clean_llm_output(tsx_content)

        # Write the file
        page_file.write_text(tsx_content)
        self.todo.increment_files()
        logger.info("Page file written", file=str(page_file), size=len(tsx_content))

        # Type check
        type_errors = await self._run_type_check()

        if type_errors:
            logger.warning(
                "Type errors found after build",
                page=page.name,
                errors=len(type_errors),
            )
            # Attempt to fix type errors inline
            tsx_content, remaining_errors = await self._fix_type_errors(
                tsx_content, type_errors, page_file, page
            )
            page_file.write_text(tsx_content)
        else:
            remaining_errors = []

        self.todo.complete(
            todo_item.id,
            agent="page_builder",
            notes=f"Written to {page_file}. Type errors: {len(remaining_errors)}",
        )

        return {
            "files_written": [str(page_file)],
            "type_errors": remaining_errors,
            "success": len(remaining_errors) == 0,
            "file_size": len(tsx_content),
        }

    # =========================================================================
    # BUILD CONFIGURATION FILES
    # =========================================================================

    async def build_config_files(self) -> List[str]:
        """Build Next.js configuration files needed to run the project."""
        written = []

        # next.config.ts
        next_config = self.project_path / "next.config.ts"
        if not next_config.exists():
            next_config.write_text("""import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  // Production-ready config
  poweredByHeader: false,
  compress: true,
  images: {
    formats: ['image/avif', 'image/webp'],
  },
}

export default nextConfig
""")
            written.append(str(next_config))

        # tailwind.config.ts
        tw_config = self.project_path / "tailwind.config.ts"
        if not tw_config.exists():
            # Build color config from spec
            primary_colors = {
                c.name.lower().replace(" ", "-"): c.hex_value for c in self.spec.colors
            }
            colors_ts = json.dumps(primary_colors, indent=6)

            tw_config.write_text(f"""import type {{ Config }} from 'tailwindcss'

const config: Config = {{
  content: [
    './src/pages/**/*{{.js,.ts,.jsx,.tsx,.mdx}}',
    './src/components/**/*{{.js,.ts,.jsx,.tsx,.mdx}}',
    './src/app/**/*{{.js,.ts,.jsx,.tsx,.mdx}}',
  ],
  theme: {{
    extend: {{
      colors: {colors_ts},
      fontFamily: {{
        heading: ['{self.spec.typography.heading_font}', 'system-ui', 'sans-serif'],
        body: ['{self.spec.typography.body_font}', 'system-ui', 'sans-serif'],
      }},
    }},
  }},
  plugins: [],
}}

export default config
""")
            written.append(str(tw_config))

        # tsconfig.json
        tsconfig = self.project_path / "tsconfig.json"
        if not tsconfig.exists():
            tsconfig.write_text(
                json.dumps(
                    {
                        "compilerOptions": {
                            "target": "ES2017",
                            "lib": ["dom", "dom.iterable", "esnext"],
                            "allowJs": True,
                            "skipLibCheck": True,
                            "strict": True,
                            "noEmit": True,
                            "esModuleInterop": True,
                            "module": "esnext",
                            "moduleResolution": "bundler",
                            "resolveJsonModule": True,
                            "isolatedModules": True,
                            "jsx": "preserve",
                            "incremental": True,
                            "plugins": [{"name": "next"}],
                            "paths": {"@/*": ["./src/*"]},
                        },
                        "include": [
                            "next-env.d.ts",
                            "**/*.ts",
                            "**/*.tsx",
                            ".next/types/**/*.ts",
                        ],
                        "exclude": ["node_modules"],
                    },
                    indent=2,
                )
            )
            written.append(str(tsconfig))

        # src/app/layout.tsx
        layout_file = self.project_path / "src" / "app" / "layout.tsx"
        if not layout_file.exists():
            layout_file.parent.mkdir(parents=True, exist_ok=True)
            layout_file.write_text(f"""import type {{ Metadata }} from 'next'
import {{ Inter }} from 'next/font/google'
import '../styles/globals.css'

const inter = Inter({{ subsets: ['latin'] }})

export const metadata: Metadata = {{
  title: '{self.spec.site_name}',
  description: '{self.spec.tagline}',
}}

export default function RootLayout({{
  children,
}}: {{
  children: React.ReactNode
}}) {{
  return (
    <html lang="en">
      <body className={{inter.className}}>{{children}}</body>
    </html>
  )
}}
""")
            written.append(str(layout_file))

        if written:
            logger.info("Config files written", files=written)

        return written

    # =========================================================================
    # TYPE CHECKING
    # =========================================================================

    async def _run_type_check(self) -> List[str]:
        """Run TypeScript type check and return list of errors."""
        try:
            result = subprocess.run(
                ["npx", "tsc", "--noEmit", "--pretty", "false"],
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                return []

            # Parse errors from output
            errors = []
            for line in (result.stdout + result.stderr).split("\n"):
                if ": error TS" in line:
                    errors.append(line.strip())

            return errors

        except subprocess.TimeoutExpired:
            logger.warning("Type check timed out")
            return []
        except FileNotFoundError:
            logger.warning("npx not found — skipping type check")
            return []

    async def _fix_type_errors(
        self,
        original_content: str,
        errors: List[str],
        file_path: Path,
        page: PageSpec,
    ) -> tuple[str, List[str]]:
        """Attempt to fix type errors using the builder agent."""
        errors_str = "\n".join(errors[:20])  # Cap at 20 errors

        fixer = Agent(
            role="TypeScript Error Fixer",
            goal="Fix TypeScript errors in Next.js components without changing functionality",
            backstory="""You are a TypeScript expert who fixes type errors precisely.
You ONLY fix the type errors listed. You do NOT refactor or redesign the component.
You return the complete fixed file.""",
            llm=self.llm,
            verbose=False,
            max_iter=10,
        )

        task = Task(
            description=f"""Fix these TypeScript errors in the following component:

ERRORS:
{errors_str}

CURRENT FILE ({file_path.name}):
{original_content}

Return ONLY the fixed TypeScript file. No explanation. The output goes directly to disk.""",
            expected_output="Complete fixed TypeScript file",
            agent=fixer,
        )

        crew = Crew(
            agents=[fixer], tasks=[task], process=Process.sequential, verbose=False
        )
        result = await crew.kickoff_async()
        fixed_content = self._clean_llm_output(str(result).strip())

        # Write and re-check
        file_path.write_text(fixed_content)
        remaining_errors = await self._run_type_check()

        return fixed_content, remaining_errors

    # =========================================================================
    # OUTPUT CLEANING
    # =========================================================================

    def _clean_llm_output(self, content: str) -> str:
        """Strip common LLM output artifacts from code."""
        # Strip markdown code fences
        if content.startswith("```"):
            lines = content.split("\n")
            # Remove first line (```tsx or ```typescript etc)
            lines = lines[1:]
            # Remove last ``` if present
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines)

        # Strip any leading/trailing whitespace
        content = content.strip()

        # Ensure it starts with an import or 'use client'
        if not (
            content.startswith("import")
            or content.startswith("'use client'")
            or content.startswith('"use client"')
        ):
            # Try to find where the actual code starts
            for i, line in enumerate(content.split("\n")):
                if line.startswith("import") or line.startswith("'use client'"):
                    content = "\n".join(content.split("\n")[i:])
                    break

        return content
