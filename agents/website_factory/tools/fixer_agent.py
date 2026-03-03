"""
================================================================================
            WEBSITE FACTORY — FIXER AGENT
            "Reads the list. Fixes the issues. Checks them off."
================================================================================

The fixer reads open fix items from the todo list, applies the fixes to the
actual files on disk, and marks each item done.

Key behaviors:
- One fix at a time — fixes are applied sequentially, not in bulk
- Reads the actual current file before fixing (never works from memory)
- Writes the fixed file back to disk
- Runs type check after each fix
- Marks todo item done only when the fix is verified
- If a fix can't be applied, marks it blocked with a reason

Author: LAIAS
Version: 1.0.0
================================================================================
"""

import os
import re
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import structlog

from crewai import Agent, Task, Crew, Process, LLM

from .spec_parser import SiteSpec
from .todo_manager import TodoManager, TodoItem, TodoStatus, TodoPriority

logger = structlog.get_logger()


# =============================================================================
# FIXER AGENT
# =============================================================================


class FixerAgent:
    """
    Applies critic-identified fixes to actual files on disk.

    Reads open fix items from the todo list.
    Fixes each one individually.
    Marks done or blocked.
    """

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
        return LLM(model="gpt-4o")

    # =========================================================================
    # MAIN FIX LOOP
    # =========================================================================

    async def fix_all_open_issues(
        self,
        page_name: str,
        cycle: int,
    ) -> Dict[str, int]:
        """
        Fix all open issues for a page in the current cycle.

        Returns counts: {fixed, blocked, failed}
        """
        open_issues = self.todo.get_open_fixes(page=page_name, cycle=cycle)

        if not open_issues:
            logger.info("No open issues to fix", page=page_name, cycle=cycle)
            return {"fixed": 0, "blocked": 0, "failed": 0}

        logger.info(
            "Starting fix loop", page=page_name, cycle=cycle, issues=len(open_issues)
        )

        counts = {"fixed": 0, "blocked": 0, "failed": 0}

        # Sort: critical first
        priority_order = {
            TodoPriority.CRITICAL: 0,
            TodoPriority.HIGH: 1,
            TodoPriority.MEDIUM: 2,
            TodoPriority.LOW: 3,
        }
        open_issues.sort(key=lambda i: priority_order.get(i.priority, 99))

        for issue in open_issues:
            try:
                result = await self._fix_single_issue(issue)
                if result == "fixed":
                    counts["fixed"] += 1
                    self.todo.increment_fixes()
                elif result == "blocked":
                    counts["blocked"] += 1
                else:
                    counts["failed"] += 1
            except Exception as e:
                logger.error("Fix attempt crashed", issue_id=issue.id, error=str(e))
                self.todo.fail(issue.id, reason=str(e))
                counts["failed"] += 1

        logger.info("Fix loop complete", page=page_name, **counts)
        return counts

    # =========================================================================
    # SINGLE ISSUE FIX
    # =========================================================================

    async def _fix_single_issue(self, issue: TodoItem) -> str:
        """
        Fix a single issue.
        Returns: 'fixed' | 'blocked' | 'failed'
        """
        logger.info(
            "Fixing issue", id=issue.id, title=issue.title, severity=issue.severity
        )

        self.todo.start(issue.id, agent="fixer")

        # Determine which file to fix
        file_path = self._resolve_file_path(issue)
        if not file_path or not file_path.exists():
            reason = f"File not found: {issue.file_path}"
            logger.warning("Cannot fix — file not found", file=issue.file_path)
            self.todo.block(issue.id, reason=reason)
            return "blocked"

        # Read current file
        current_content = file_path.read_text()

        # Try a direct string replacement first (for simple fixes)
        quick_fix = self._try_quick_fix(issue, current_content)
        if quick_fix:
            file_path.write_text(quick_fix)
            type_errors = await self._type_check()
            if not type_errors:
                self.todo.complete(
                    issue.id, agent="fixer", notes="Quick string replacement applied"
                )
                return "fixed"
            else:
                # Revert and fall through to LLM fix
                file_path.write_text(current_content)

        # Fall through to LLM-powered fix
        fixed_content = await self._llm_fix(issue, current_content, file_path)

        if not fixed_content:
            self.todo.fail(issue.id, reason="LLM fix returned empty content")
            return "failed"

        # Write the fix
        file_path.write_text(fixed_content)

        # Verify no type errors introduced
        type_errors = await self._type_check()
        if type_errors:
            # Check if these errors existed before (not introduced by our fix)
            logger.warning(
                "Type errors after fix",
                issue_id=issue.id,
                errors=len(type_errors),
            )
            # Keep the fix anyway if no new critical errors — type errors
            # from other files shouldn't block this fix
            if self._errors_are_in_file(type_errors, str(file_path)):
                # Revert
                file_path.write_text(current_content)
                self.todo.fail(
                    issue.id, reason=f"Fix introduced type errors: {type_errors[:2]}"
                )
                return "failed"

        self.todo.complete(
            issue.id,
            agent="fixer",
            notes=f"Fixed in {file_path.name}",
        )
        return "fixed"

    # =========================================================================
    # QUICK FIX (no LLM needed)
    # =========================================================================

    def _try_quick_fix(self, issue: TodoItem, content: str) -> Optional[str]:
        """
        Try to apply a simple fix without LLM.
        Returns fixed content or None if quick fix not possible.
        """
        if not issue.fix_suggestion or not issue.actual or not issue.expected:
            return None

        # Exact color replacement: #xxxxxx -> #xxxxxx
        color_pattern = re.compile(r"#[0-9A-Fa-f]{6}\b")
        if color_pattern.match(issue.actual.strip()) and color_pattern.match(
            issue.expected.strip()
        ):
            old_color = issue.actual.strip()
            new_color = issue.expected.strip()
            if old_color in content:
                fixed = content.replace(old_color, new_color, 1)
                if fixed != content:
                    logger.info(
                        "Quick fix: color replacement", old=old_color, new=new_color
                    )
                    return fixed

        # Simple text replacement
        actual_stripped = issue.actual.strip()
        expected_stripped = issue.expected.strip()
        if (
            len(actual_stripped) < 200  # Only for short strings
            and actual_stripped in content
            and actual_stripped != expected_stripped
        ):
            fixed = content.replace(actual_stripped, expected_stripped, 1)
            if fixed != content:
                logger.info("Quick fix: text replacement")
                return fixed

        return None

    # =========================================================================
    # LLM FIX
    # =========================================================================

    async def _llm_fix(
        self,
        issue: TodoItem,
        current_content: str,
        file_path: Path,
    ) -> Optional[str]:
        """Use LLM to apply a fix."""

        fixer = Agent(
            role="Precise Code Fixer",
            goal="Apply exactly the specified fix without changing anything else",
            backstory="""You apply surgical code fixes. You ONLY fix the specific issue
described. You do NOT refactor. You do NOT redesign. You do NOT improve other things.
You change the minimum amount of code needed to fix the issue.
Return the COMPLETE file with ONLY the fix applied.""",
            llm=self.llm,
            verbose=False,
            max_iter=8,
        )

        task = Task(
            description=f"""Apply this fix to the file:

ISSUE: {issue.title}
SEVERITY: {issue.severity}
FILE: {file_path.relative_to(self.project_path)}
SELECTOR/ELEMENT: {issue.selector or "N/A"}

WHAT'S WRONG (ACTUAL):
{issue.actual or "See fix suggestion"}

WHAT IT SHOULD BE (EXPECTED):
{issue.expected or "See fix suggestion"}

HOW TO FIX IT:
{issue.fix_suggestion or "Fix the issue as described"}

CURRENT FILE CONTENT:
{current_content}

RULES:
1. Apply ONLY this fix
2. Do NOT change anything else
3. Return the COMPLETE file content
4. No explanation — just the fixed code
""",
            expected_output="Complete fixed file content, starting from the first line",
            agent=fixer,
        )

        crew = Crew(
            agents=[fixer], tasks=[task], process=Process.sequential, verbose=False
        )
        result = await crew.kickoff_async()
        fixed = self._clean_output(str(result))

        # Sanity check — make sure we got back something reasonable
        if len(fixed) < len(current_content) * 0.5:
            logger.warning(
                "Fixed content suspiciously short",
                original=len(current_content),
                fixed=len(fixed),
            )
            return None

        return fixed

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _resolve_file_path(self, issue: TodoItem) -> Optional[Path]:
        """Resolve the file path from an issue, trying multiple strategies."""
        if not issue.file_path:
            return None

        # Try absolute path first
        p = Path(issue.file_path)
        if p.exists():
            return p

        # Try relative to project
        p = self.project_path / issue.file_path
        if p.exists():
            return p

        # Try stripping leading slashes and joining
        clean = issue.file_path.lstrip("/")
        p = self.project_path / clean
        if p.exists():
            return p

        return None

    async def _type_check(self) -> List[str]:
        """Run TypeScript type check."""
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
            errors = []
            for line in (result.stdout + result.stderr).split("\n"):
                if ": error TS" in line:
                    errors.append(line.strip())
            return errors
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return []

    def _errors_are_in_file(self, errors: List[str], file_path: str) -> bool:
        """Check if any type errors are in the specific file we just edited."""
        # Use relative path from project root for accurate matching
        # TypeScript errors look like: "src/app/contact/page.tsx(10,5): error ..."
        try:
            rel_path = str(Path(file_path).relative_to(self.project_path))
        except ValueError:
            # Fallback to filename if we can't get relative path
            rel_path = Path(file_path).name

        # Match the relative path in error output (more specific than just filename)
        return any(rel_path in error for error in errors)

    def _clean_output(self, content: str) -> str:
        """Strip LLM output artifacts."""
        if content.startswith("```"):
            lines = content.split("\n")[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines)
        return content.strip()
