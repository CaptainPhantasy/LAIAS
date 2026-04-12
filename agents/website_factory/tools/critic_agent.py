"""
================================================================================
            WEBSITE FACTORY — CRITIC AGENT
            "No mercy. Grade harshly. Document everything."
================================================================================

The critic reads the actual files on disk, compares them against the spec,
and produces a structured list of issues in the exact format the todo manager
expects. It also produces a numerical grade (0-100) used for the convergence
check.

The critic output format is strict — it uses ---ISSUE--- / ---END--- delimiters
so the todo manager can parse it deterministically. No freeform feedback.

Author: LAIAS
Version: 1.0.0
================================================================================
"""

import os
import re
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import structlog

from crewai import Agent, Task, Crew, Process, LLM

from .spec_parser import SiteSpec, PageSpec
from .todo_manager import TodoManager, TodoCategory

logger = structlog.get_logger()


# =============================================================================
# CRITIQUE RESULT
# =============================================================================


@dataclass
class CritiqueResult:
    """Structured result from the critic agent."""

    page: str
    cycle: int
    overall_grade: float  # 0-100
    issue_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    raw_output: str  # Full critic output (contains ---ISSUE--- blocks)
    can_improve: bool  # True if improvement >= threshold possible
    sign_off: bool  # True if grade >= 95 and no critical/high issues


# =============================================================================
# CRITIC AGENT
# =============================================================================


class CriticAgent:
    """
    The harsh critic. Reviews built pages against the spec.
    Produces a grade and a structured list of issues.
    """

    SIGN_OFF_THRESHOLD = 95.0  # Grade required for sign-off
    IMPROVEMENT_THRESHOLD = 2.0  # % improvement to continue cycling

    def __init__(
        self,
        project_path: str,
        spec: SiteSpec,
        todo: TodoManager,
    ):
        self.project_path = Path(project_path)
        self.spec = spec
        self.todo = todo
        self.llm = self._get_llm()

    def _get_llm(self) -> LLM:
        provider = os.getenv("LAIAS_LLM_PROVIDER", "openai")
        if provider == "zai":
            return LLM(
                model="glm-4-plus",
                api_key=os.getenv("ZAI_API_KEY"),
                base_url="https://open.bigmodel.cn/api/paas/v4",
            )
        return LLM(model=os.getenv("DEFAULT_MODEL", "gpt-4o"), base_url="https://api.portkey.ai/v1", api_key=os.getenv("PORTKEY_API_KEY", ""))

    # =========================================================================
    # MAIN CRITIQUE
    # =========================================================================

    async def critique_page(self, page: PageSpec, cycle: int) -> CritiqueResult:
        """
        Critique a built page against the spec.

        Reads actual files from disk. Compares to spec.
        Returns structured CritiqueResult with grade and issue list.
        """
        logger.info("Critiquing page", page=page.name, cycle=cycle)

        # Read the built files
        file_contents = self._read_page_files(page)
        if not file_contents:
            logger.warning("No files found for page", page=page.name)
            return self._empty_critique(page.name, cycle)

        # Build design system reference
        design_ref = self._build_design_reference()

        # Build page spec reference
        page_spec_ref = self._build_page_spec_reference(page)

        # Create the critic agent
        critic = Agent(
            role="Harsh Website Quality Critic",
            goal=f"Find EVERY defect in the {page.name} page and grade it ruthlessly",
            backstory="""You are the harshest critic in the web development industry.
Your job is NOT to be nice. Your job is to find problems.

You check:
- Colors (do they EXACTLY match the design spec hex values?)
- Typography (right fonts? right sizes? right weights?)
- Spacing (does it match the spacing system?)
- Layout (correct structure? proper alignment?)
- Responsiveness (does it work at 320px? 768px? 1280px?)
- Accessibility (ARIA labels? semantic HTML? focus indicators?)
- Interactions (are all buttons/links/forms properly connected?)
- Copy (does it match the provided copy exactly?)
- Component usage (is the design system being used correctly?)

A grade of 95 means you found real issues. 100 is perfect.
You document EVERY issue you find, no matter how small.
You never say "looks good" unless it literally has zero issues.""",
            llm=self.llm,
            verbose=True,
            max_iter=25,
        )

        # Create the critique task
        task = Task(
            description=f"""
Critique the {page.name.upper()} page ruthlessly against the specification.

DESIGN SPECIFICATION:
{design_ref}

PAGE SPECIFICATION:
{page_spec_ref}

BUILT FILES TO REVIEW:
{file_contents}

YOUR OUTPUT FORMAT (MANDATORY — use this EXACT format for each issue):

---ISSUE---
SEVERITY: critical|high|medium|low
FILE: relative/path/to/file.tsx
SELECTOR: .css-selector-or-element-name (or "N/A")
TITLE: One-line description of the issue
EXPECTED: What it should be according to the spec
ACTUAL: What it currently is in the code
FIX: Exact code change needed to fix this
---END---

After ALL issues, output:

GRADE: [number 0-100]
SUMMARY: [one paragraph explaining the overall quality and what most needs fixing]

GRADING RUBRIC:
- Start at 100
- Deduct 15 for each CRITICAL issue
- Deduct 8 for each HIGH issue
- Deduct 3 for each MEDIUM issue
- Deduct 1 for each LOW issue
- Minimum grade: 0

Be thorough. A page with zero issues is rare. Look hard.
""",
            expected_output="Structured issue list with ---ISSUE--- blocks and a final GRADE",
            agent=critic,
        )

        crew = Crew(
            agents=[critic],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = await crew.kickoff_async()
        raw_output = str(result)

        # Parse grade
        grade = self._parse_grade(raw_output)

        # Parse and count issues
        issue_counts = self._count_issues(raw_output)

        # Add issues to todo list
        issues_added = self.todo.add_from_critic_output(
            critic_output=raw_output,
            page=page.name,
            cycle=cycle,
            project_path=str(self.project_path),
        )

        # Record grade for convergence tracking
        self.todo.record_grade(page.name, grade, cycle)

        # Determine if we should continue
        can_improve = self.todo.should_continue_cycle(
            page.name, grade, self.IMPROVEMENT_THRESHOLD
        )
        sign_off = (
            grade >= self.SIGN_OFF_THRESHOLD
            and issue_counts["critical"] == 0
            and issue_counts["high"] == 0
        )

        critique = CritiqueResult(
            page=page.name,
            cycle=cycle,
            overall_grade=grade,
            issue_count=len(issues_added),
            critical_count=issue_counts["critical"],
            high_count=issue_counts["high"],
            medium_count=issue_counts["medium"],
            low_count=issue_counts["low"],
            raw_output=raw_output,
            can_improve=can_improve,
            sign_off=sign_off,
        )

        logger.info(
            "Critique complete",
            page=page.name,
            cycle=cycle,
            grade=grade,
            issues=len(issues_added),
            critical=issue_counts["critical"],
            sign_off=sign_off,
        )

        return critique

    # =========================================================================
    # SINGLE-PASS CRITIQUE AND FIX (merged for efficiency)
    # =========================================================================

    async def critique_and_fix(self, page: PageSpec, cycle: int) -> CritiqueResult:
        """
        Single-pass: Critique the page AND apply all fixes in one LLM call.
        This replaces the separate critique → todo → fix loop for efficiency.
        """
        logger.info("Single-pass critique and fix", page=page.name, cycle=cycle)

        # Read the built files
        file_contents = self._read_page_files(page)
        if not file_contents:
            logger.warning("No files found for page", page=page.name)
            return self._empty_critique(page.name, cycle)

        # Build references
        design_ref = self._build_design_reference()
        page_spec_ref = self._build_page_spec_reference(page)

        # Create the reviewer-fixer agent
        reviewer_fixer = Agent(
            role="Reviewer-Fixer",
            goal=f"Find ALL issues in {page.name} and fix them ALL in one pass",
            backstory="""You are a senior code reviewer who also writes fixes. You find issues
AND you fix them in the same output. You don't hand off to anyone else.

Your process:
1. Read the current code
2. Compare it to the spec (colors, fonts, copy, structure)
3. List EVERY issue you find
4. Output the FIXED version of EACH file that has issues
5. Give a final grade

You fix EVERYTHING in one pass. No iterations. No handoffs.
If a button text is wrong, you fix it. If a color is wrong, you fix it.
You output the complete fixed file contents.""",
            llm=self.llm,
            verbose=True,
            max_iter=30,  # Higher limit since we're doing more work
        )

        task = Task(
            description=f"""
Review AND fix the {page.name.upper()} page in one pass.

DESIGN SPECIFICATION:
{design_ref}

PAGE SPECIFICATION:
{page_spec_ref}

CURRENT FILES:
{file_contents}

YOUR OUTPUT FORMAT (MANDATORY):

For EACH file that needs fixes, output:
---FIXED_FILE---
PATH: relative/path/to/file.tsx
CONTENT:
[Complete fixed file content here]
---END---

After all fixed files, output:
ISSUES_FIXED: [number of issues you fixed]
GRADE: [number 0-100]
SUMMARY: [brief summary of what was fixed]
""",
            expected_output="Fixed file blocks, ISSUES_FIXED count, GRADE, and SUMMARY",
            agent=reviewer_fixer,
        )

        crew = Crew(
            agents=[reviewer_fixer],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = await crew.kickoff_async()
        raw_output = str(result)

        # Parse and apply fixed files
        fixed_count = self._apply_fixed_files(raw_output)

        # Parse grade
        grade = self._parse_grade(raw_output)

        # Parse issues fixed count
        issues_fixed_match = re.search(r"ISSUES_FIXED:\s*(\d+)", raw_output)
        issues_fixed = int(issues_fixed_match.group(1)) if issues_fixed_match else fixed_count

        # Record grade for convergence tracking
        self.todo.record_grade(page.name, grade, cycle)

        # Determine sign-off
        sign_off = grade >= self.SIGN_OFF_THRESHOLD

        critique = CritiqueResult(
            page=page.name,
            cycle=cycle,
            overall_grade=grade,
            issue_count=issues_fixed,
            critical_count=0,  # We fixed them all
            high_count=0,
            medium_count=0,
            low_count=0,
            raw_output=raw_output,
            can_improve=False,  # We already fixed everything
            sign_off=sign_off,
        )

        logger.info(
            "Single-pass critique and fix complete",
            page=page.name,
            cycle=cycle,
            grade=grade,
            issues_fixed=issues_fixed,
            files_fixed=fixed_count,
            sign_off=sign_off,
        )

        return critique

    def _apply_fixed_files(self, raw_output: str) -> int:
        """Parse and apply fixed file blocks from reviewer-fixer output."""
        fixed_count = 0
        pattern = r"---FIXED_FILE---\s*PATH:\s*([^\n]+)\s*CONTENT:\s*(.*?)---END---"

        for match in re.finditer(pattern, raw_output, re.DOTALL):
            file_path = match.group(1).strip()
            content = match.group(2).strip()

            # Resolve the full path
            full_path = self.project_path / file_path

            if full_path.exists():
                # Clean up content (remove markdown code blocks if present)
                if content.startswith("```"):
                    lines = content.split("\n")[1:]
                    if lines and lines[-1].strip() == "```":
                        lines = lines[:-1]
                    content = "\n".join(lines)

                full_path.write_text(content)
                fixed_count += 1
                logger.info("Applied fix to file", file=str(full_path))
            else:
                logger.warning("Fixed file path not found", file=str(full_path))

        return fixed_count

    # =========================================================================
    # DUAL SIGN-OFF CRITIQUE
    # =========================================================================

    async def final_signoff_critique(
        self,
        page: PageSpec,
        critic_number: int,
        previous_critiques: List[CritiqueResult],
    ) -> CritiqueResult:
        """
        Final independent sign-off critique.
        Called twice with different critic instances.
        """
        logger.info("Final sign-off critique", page=page.name, critic=critic_number)

        file_contents = self._read_page_files(page)
        design_ref = self._build_design_reference()

        grade_history = self.todo.get_grade_history(page.name)
        history_str = " → ".join(f"{g:.1f}%" for g in grade_history)

        critic = Agent(
            role=f"Final Sign-Off Critic #{critic_number}",
            goal=f"Independently verify {page.name} is production-ready for final sign-off",
            backstory=f"""You are Final Critic #{critic_number}. You review pages for final
production sign-off. You are INDEPENDENT — you do not consult other critics.
You have seen many websites. Your standards are extremely high.
You only sign off when you are 100% confident the page is complete,
professional, and would not embarrass the client.

Previous grade history for this page: {history_str}

You check everything one more time with fresh eyes.""",
            llm=self.llm,
            verbose=True,
            max_iter=20,
        )

        task = Task(
            description=f"""
Perform final sign-off review of {page.name.upper()} page.

DESIGN SPECIFICATION:
{design_ref}

BUILT FILES:
{file_contents}

Use the same ---ISSUE--- format for any remaining issues.
After all issues, output:
GRADE: [number]
SIGN_OFF: YES|NO
REASON: [why you are or aren't signing off]
""",
            expected_output="Issue list (if any), GRADE, SIGN_OFF decision, and REASON",
            agent=critic,
        )

        crew = Crew(
            agents=[critic], tasks=[task], process=Process.sequential, verbose=True
        )
        result = await crew.kickoff_async()
        raw_output = str(result)

        grade = self._parse_grade(raw_output)
        issue_counts = self._count_issues(raw_output)
        signed_off = "SIGN_OFF: YES" in raw_output.upper()

        return CritiqueResult(
            page=page.name,
            cycle=999,  # Final cycle marker
            overall_grade=grade,
            issue_count=issue_counts["total"],
            critical_count=issue_counts["critical"],
            high_count=issue_counts["high"],
            medium_count=issue_counts["medium"],
            low_count=issue_counts["low"],
            raw_output=raw_output,
            can_improve=False,
            sign_off=signed_off and grade >= self.SIGN_OFF_THRESHOLD,
        )

    # =========================================================================
    # FILE READING
    # =========================================================================

    def _read_page_files(self, page: PageSpec) -> str:
        """Read all relevant files for a page."""
        parts = []

        # Main page file
        if page.path == "/":
            page_file = self.project_path / "src" / "app" / "page.tsx"
        else:
            clean = page.path.lstrip("/")
            page_file = self.project_path / "src" / "app" / clean / "page.tsx"

        if page_file.exists():
            parts.append(
                f"// FILE: {page_file.relative_to(self.project_path)}\n{page_file.read_text()}"
            )
        else:
            logger.warning("Page file not found", path=str(page_file))
            return ""

        # Any page-specific components
        page_component_dir = (
            self.project_path / "src" / "components" / page.name.lower()
        )
        if page_component_dir.exists():
            for f in sorted(page_component_dir.glob("*.tsx")):
                parts.append(
                    f"// FILE: {f.relative_to(self.project_path)}\n{f.read_text()}"
                )

        # Design system (truncated)
        globals_css = self.project_path / "src" / "styles" / "globals.css"
        if globals_css.exists():
            parts.append(
                f"// FILE: src/styles/globals.css (first 500 chars)\n{globals_css.read_text()[:500]}"
            )

        return "\n\n" + "=" * 60 + "\n\n".join(parts)

    # =========================================================================
    # SPEC REFERENCES
    # =========================================================================

    def _build_design_reference(self) -> str:
        """Build a concise design reference for the critic."""
        colors_str = "\n".join(
            f"  {c.name}: {c.hex_value} — {c.usage}" for c in self.spec.colors
        )
        return f"""
COLORS (critic must verify these exact values are used):
{colors_str}

HEADING FONT: {self.spec.typography.heading_font}
BODY FONT: {self.spec.typography.body_font}
PRIMARY CTA TEXT: {self.spec.primary_cta}
SITE NAME: {self.spec.site_name}
"""

    def _build_page_spec_reference(self, page: PageSpec) -> str:
        """Build a page-specific spec reference."""
        parts = [
            f"Page: {page.name}",
            f"Route: {page.path}",
            f"Title: {page.title}",
            f"Meta description: {page.meta_description}",
            f"Primary CTA: {page.cta_primary or self.spec.primary_cta}",
        ]

        if page.page_copy:
            parts.append(f"Copy: {json.dumps(page.page_copy, indent=2)}")

        raw = self.spec.raw_sections.get(page.name.lower().replace(" ", "_"), "")
        if raw:
            parts.append(f"Raw spec section (first 2000 chars):\n{raw[:2000]}")

        return "\n".join(parts)

    # =========================================================================
    # PARSING
    # =========================================================================

    def _parse_grade(self, output: str) -> float:
        """Extract the GRADE from critic output."""
        match = re.search(r"GRADE:\s*(\d+(?:\.\d+)?)", output, re.IGNORECASE)
        if match:
            grade = float(match.group(1))
            return min(100.0, max(0.0, grade))

        # Fallback: estimate from issue count
        issue_count = output.count("---ISSUE---")
        estimated = max(0.0, 100.0 - (issue_count * 5))
        logger.warning("Could not parse grade, estimating", estimated=estimated)
        return estimated

    def _count_issues(self, output: str) -> Dict[str, int]:
        """Count issues by severity."""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "total": 0}
        for block in re.finditer(r"---ISSUE---(.*?)---END---", output, re.DOTALL):
            severity_match = re.search(
                r"SEVERITY:\s*(\w+)", block.group(1), re.IGNORECASE
            )
            if severity_match:
                sev = severity_match.group(1).lower()
                if sev in counts:
                    counts[sev] += 1
            counts["total"] += 1
        return counts

    def _empty_critique(self, page_name: str, cycle: int) -> CritiqueResult:
        """Return an empty critique when no files exist."""
        return CritiqueResult(
            page=page_name,
            cycle=cycle,
            overall_grade=0.0,
            issue_count=0,
            critical_count=0,
            high_count=0,
            medium_count=0,
            low_count=0,
            raw_output="No files found to critique.",
            can_improve=True,
            sign_off=False,
        )
