"""
================================================================================
            WEBSITE FACTORY — TODO MANAGER
            "The shared contract. The external brain. The source of truth."
================================================================================

This is not a convenience class. This is the mechanism that makes the builder
work like DeepAgent.

Every agent in the build loop reads from and writes to this todo list.
The critic writes issues here. The fixer reads them here and marks them done.
The orchestrator reads it to know where we are. The verifier checks it before
signing off.

The todo list lives on disk as JSON — it persists between agent invocations,
across context window resets, and through failures.

Nobody improvises. If it's not on the list, it doesn't get done.
If it's on the list, it gets done.

Author: LAIAS
Version: 1.0.0
================================================================================
"""

import json
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger()


# =============================================================================
# ENUMS
# =============================================================================


class TodoStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"
    FAILED = "failed"
    SKIPPED = "skipped"


class TodoPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TodoCategory(str, Enum):
    BUILD = "build"  # Actual file creation/editing
    FIX = "fix"  # Critic-identified issues
    VERIFY = "verify"  # Verification tasks
    INTERACTION = "interaction"  # Button/link/form wiring
    ACCESSIBILITY = "accessibility"  # a11y fixes
    PERFORMANCE = "performance"  # Perf fixes
    SIGNOFF = "signoff"  # Final sign-off tasks


# =============================================================================
# TODO ITEM MODEL
# =============================================================================


class TodoItem(BaseModel):
    """A single item on the todo list."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    category: TodoCategory
    priority: TodoPriority = TodoPriority.MEDIUM
    status: TodoStatus = TodoStatus.PENDING

    # What needs to be done
    title: str
    description: str = ""

    # Context
    page: Optional[str] = None  # Which page this is for
    file_path: Optional[str] = None  # Which file to edit
    selector: Optional[str] = None  # CSS selector (for interactions/fixes)
    element: Optional[str] = None  # Element description

    # Critic metadata (populated by critic agent)
    severity: Optional[str] = None  # critical / high / medium / low
    expected: Optional[str] = None  # What it should look like
    actual: Optional[str] = None  # What it currently looks like
    fix_suggestion: Optional[str] = None  # How to fix it

    # Resolution
    resolved_by: Optional[str] = None  # Which agent resolved it
    resolution_notes: Optional[str] = None

    # Timing
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    # Iteration tracking
    cycle: int = 0  # Which build cycle this was found in
    attempts: int = 0  # How many times fix was attempted


# =============================================================================
# TODO LIST MODEL
# =============================================================================


class TodoList(BaseModel):
    """The complete todo list for a build."""

    project_name: str
    project_path: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    items: List[TodoItem] = Field(default_factory=list)

    # Build progress tracking
    current_phase: str = "planning"
    current_page: Optional[str] = None
    current_cycle: int = 0

    # Grade history per page — for the 2% convergence check
    grade_history: Dict[str, List[float]] = Field(default_factory=dict)

    # Build metadata
    total_files_created: int = 0
    total_fixes_applied: int = 0
    total_cycles_run: int = 0


# =============================================================================
# TODO MANAGER
# =============================================================================


class TodoManager:
    """
    Manages the persistent todo list for a website build.

    This is the shared contract between all agents. Every agent that
    participates in the build loop uses this manager.

    Thread-safe via file locking (simple implementation — single-process
    builds don't need distributed locking).
    """

    def __init__(self, project_path: str, project_name: str):
        self.project_path = Path(project_path)
        self.todo_path = self.project_path / "docs" / "build-receipts" / "todo.json"
        self.todo_path.parent.mkdir(parents=True, exist_ok=True)

        if self.todo_path.exists():
            self._list = TodoList.model_validate_json(self.todo_path.read_text())
            logger.info(
                "Todo list loaded",
                path=str(self.todo_path),
                items=len(self._list.items),
            )
        else:
            self._list = TodoList(
                project_name=project_name,
                project_path=str(project_path),
            )
            self._save()
            logger.info("New todo list created", path=str(self.todo_path))

    # =========================================================================
    # PERSISTENCE
    # =========================================================================

    def _save(self):
        """Save the todo list to disk."""
        self._list.updated_at = datetime.utcnow().isoformat()
        self.todo_path.write_text(self._list.model_dump_json(indent=2))

    def reload(self):
        """Reload from disk (in case another agent wrote to it)."""
        if self.todo_path.exists():
            self._list = TodoList.model_validate_json(self.todo_path.read_text())

    # =========================================================================
    # ADDING ITEMS
    # =========================================================================

    def add(self, item: TodoItem) -> TodoItem:
        """Add a new item to the list."""
        self._list.items.append(item)
        self._save()
        logger.debug("Todo added", id=item.id, title=item.title, category=item.category)
        return item

    def add_build_task(
        self,
        title: str,
        page: str,
        file_path: str,
        description: str = "",
        priority: TodoPriority = TodoPriority.HIGH,
        cycle: int = 0,
    ) -> TodoItem:
        """Add a build task (file creation/editing)."""
        return self.add(
            TodoItem(
                category=TodoCategory.BUILD,
                priority=priority,
                title=title,
                description=description,
                page=page,
                file_path=file_path,
                cycle=cycle,
            )
        )

    def add_fix(
        self,
        title: str,
        page: str,
        file_path: str,
        severity: str,
        expected: str,
        actual: str,
        fix_suggestion: str,
        selector: Optional[str] = None,
        cycle: int = 0,
    ) -> TodoItem:
        """Add a fix item from critic feedback."""
        priority_map = {
            "critical": TodoPriority.CRITICAL,
            "high": TodoPriority.HIGH,
            "medium": TodoPriority.MEDIUM,
            "low": TodoPriority.LOW,
        }
        return self.add(
            TodoItem(
                category=TodoCategory.FIX,
                priority=priority_map.get(severity.lower(), TodoPriority.MEDIUM),
                title=title,
                page=page,
                file_path=file_path,
                severity=severity,
                expected=expected,
                actual=actual,
                fix_suggestion=fix_suggestion,
                selector=selector,
                cycle=cycle,
            )
        )

    def add_interaction_task(
        self,
        title: str,
        page: str,
        file_path: str,
        element: str,
        selector: str,
        description: str = "",
    ) -> TodoItem:
        """Add an interaction wiring task."""
        return self.add(
            TodoItem(
                category=TodoCategory.INTERACTION,
                priority=TodoPriority.HIGH,
                title=title,
                description=description,
                page=page,
                file_path=file_path,
                element=element,
                selector=selector,
            )
        )

    def add_from_critic_output(
        self,
        critic_output: str,
        page: str,
        cycle: int,
        project_path: str,
    ) -> List[TodoItem]:
        """
        Parse critic output text and add fix items.

        The critic is instructed to output issues in a structured format.
        This method parses that format and creates TodoItems.

        Expected critic format (enforced via task description):
        ---ISSUE---
        SEVERITY: critical|high|medium|low
        FILE: src/app/page.tsx
        SELECTOR: .hero-section
        TITLE: Hero background color doesn't match spec
        EXPECTED: #0369a1 (Primary 700)
        ACTUAL: #0ea5e9 (Primary 500)
        FIX: Change background-color from sky-400 to sky-700 in hero div
        ---END---
        """
        items: List[TodoItem] = []

        # Split by issue markers
        import re

        issue_blocks = re.findall(
            r"---ISSUE---(.*?)---END---", critic_output, re.DOTALL
        )

        for block in issue_blocks:

            def extract(field: str) -> str:
                match = re.search(rf"{field}:\s*(.+?)(?:\n|$)", block, re.IGNORECASE)
                return match.group(1).strip() if match else ""

            severity = extract("SEVERITY") or "medium"
            file_path = extract("FILE") or ""
            selector = extract("SELECTOR") or None
            title = extract("TITLE") or "Unspecified issue"
            expected = extract("EXPECTED") or ""
            actual = extract("ACTUAL") or ""
            fix = extract("FIX") or ""

            # Make file path absolute
            if file_path and not file_path.startswith("/"):
                file_path = str(Path(project_path) / file_path)

            item = self.add_fix(
                title=title,
                page=page,
                file_path=file_path,
                severity=severity,
                expected=expected,
                actual=actual,
                fix_suggestion=fix,
                selector=selector,
                cycle=cycle,
            )
            items.append(item)

        if not items:
            logger.warning(
                "No structured issues found in critic output",
                page=page,
                cycle=cycle,
                output_length=len(critic_output),
            )

        return items

    # =========================================================================
    # QUERYING
    # =========================================================================

    def get_pending(
        self,
        category: Optional[TodoCategory] = None,
        page: Optional[str] = None,
        priority: Optional[TodoPriority] = None,
    ) -> List[TodoItem]:
        """Get all pending items, optionally filtered."""
        items = [i for i in self._list.items if i.status == TodoStatus.PENDING]
        if category:
            items = [i for i in items if i.category == category]
        if page:
            items = [i for i in items if i.page == page]
        if priority:
            items = [i for i in items if i.priority == priority]

        # Sort: critical first, then high, then by creation time
        priority_order = {
            TodoPriority.CRITICAL: 0,
            TodoPriority.HIGH: 1,
            TodoPriority.MEDIUM: 2,
            TodoPriority.LOW: 3,
        }
        return sorted(
            items, key=lambda i: (priority_order.get(i.priority, 99), i.created_at)
        )

    def get_open_fixes(
        self, page: Optional[str] = None, cycle: Optional[int] = None
    ) -> List[TodoItem]:
        """Get all open fix items."""
        items = [
            i
            for i in self._list.items
            if i.category == TodoCategory.FIX
            and i.status in (TodoStatus.PENDING, TodoStatus.IN_PROGRESS)
        ]
        if page:
            items = [i for i in items if i.page == page]
        if cycle is not None:
            items = [i for i in items if i.cycle == cycle]
        return items

    def get_by_id(self, item_id: str) -> Optional[TodoItem]:
        """Get a specific item by ID."""
        for item in self._list.items:
            if item.id == item_id:
                return item
        return None

    def count_open_fixes(self, page: Optional[str] = None) -> int:
        """Count open fix items."""
        return len(self.get_open_fixes(page=page))

    def count_by_status(self) -> Dict[str, int]:
        """Count items by status."""
        counts: Dict[str, int] = {}
        for item in self._list.items:
            counts[item.status] = counts.get(item.status, 0) + 1
        return counts

    # =========================================================================
    # UPDATING STATUS
    # =========================================================================

    def start(self, item_id: str, agent: str = "") -> Optional[TodoItem]:
        """Mark an item as in progress."""
        item = self.get_by_id(item_id)
        if item:
            item.status = TodoStatus.IN_PROGRESS
            item.started_at = datetime.utcnow().isoformat()
            item.resolved_by = agent
            item.attempts += 1
            self._save()
        return item

    def complete(
        self,
        item_id: str,
        agent: str = "",
        notes: str = "",
    ) -> Optional[TodoItem]:
        """Mark an item as done."""
        item = self.get_by_id(item_id)
        if item:
            item.status = TodoStatus.DONE
            item.completed_at = datetime.utcnow().isoformat()
            item.resolved_by = agent
            item.resolution_notes = notes
            self._save()
            logger.info("Todo completed", id=item_id, title=item.title)
        return item

    def fail(self, item_id: str, reason: str = "") -> Optional[TodoItem]:
        """Mark an item as failed."""
        item = self.get_by_id(item_id)
        if item:
            item.status = TodoStatus.FAILED
            item.completed_at = datetime.utcnow().isoformat()
            item.resolution_notes = reason
            self._save()
            logger.warning("Todo failed", id=item_id, title=item.title, reason=reason)
        return item

    def block(self, item_id: str, reason: str = "") -> Optional[TodoItem]:
        """Mark an item as blocked."""
        item = self.get_by_id(item_id)
        if item:
            item.status = TodoStatus.BLOCKED
            item.resolution_notes = reason
            self._save()
        return item

    # =========================================================================
    # GRADE TRACKING (2% CONVERGENCE)
    # =========================================================================

    def record_grade(self, page: str, grade: float, cycle: int):
        """Record a critic grade for convergence checking."""
        if page not in self._list.grade_history:
            self._list.grade_history[page] = []
        self._list.grade_history[page].append(grade)
        self._list.current_cycle = cycle
        self._list.total_cycles_run += 1
        self._save()

        logger.info(
            "Grade recorded",
            page=page,
            grade=grade,
            cycle=cycle,
            history=self._list.grade_history[page],
        )

    def should_continue_cycle(
        self, page: str, current_grade: float, threshold: float = 2.0, max_cycles: int = 10
    ) -> bool:
        """
        Check if another improvement cycle is warranted.

        Returns True if improvement from last cycle >= threshold%.
        Returns False if we've converged (improvement < threshold).
        Returns False if max cycles exceeded.
        """
        history = self._list.grade_history.get(page, [])

        if len(history) < 2:
            # Always do at least 2 cycles
            return True

        if len(history) >= max_cycles:
            logger.warning(
                "Max cycles exceeded",
                page=page,
                cycles=len(history),
                max_cycles=max_cycles,
            )
            return False

        last_grade = history[-2]  # Second to last (last was just recorded)
        improvement = current_grade - last_grade

        logger.info(
            "Convergence check",
            page=page,
            current_grade=current_grade,
            last_grade=last_grade,
            improvement=improvement,
            threshold=threshold,
            continuing=improvement >= threshold,
        )

        return improvement >= threshold

    def get_grade_history(self, page: str) -> List[float]:
        """Get the grade history for a page."""
        return self._list.grade_history.get(page, [])

    # =========================================================================
    # PHASE / PROGRESS TRACKING
    # =========================================================================

    def set_phase(self, phase: str, page: Optional[str] = None):
        """Update current phase."""
        self._list.current_phase = phase
        self._list.current_page = page
        self._save()

    def increment_files(self):
        """Track file creation."""
        self._list.total_files_created += 1
        self._save()

    def increment_fixes(self):
        """Track fixes applied."""
        self._list.total_fixes_applied += 1
        self._save()

    # =========================================================================
    # REPORTING
    # =========================================================================

    def print_summary(self):
        """Print a human-readable summary of the todo list."""
        counts = self.count_by_status()
        pending = counts.get(TodoStatus.PENDING, 0)
        in_progress = counts.get(TodoStatus.IN_PROGRESS, 0)
        done = counts.get(TodoStatus.DONE, 0)
        failed = counts.get(TodoStatus.FAILED, 0)

        print(f"\n{'=' * 60}")
        print(f"TODO LIST: {self._list.project_name}")
        print(f"{'=' * 60}")
        print(f"  Phase    : {self._list.current_phase}")
        print(f"  Page     : {self._list.current_page or 'N/A'}")
        print(f"  Cycle    : {self._list.current_cycle}")
        print(f"")
        print(f"  Pending  : {pending}")
        print(f"  Active   : {in_progress}")
        print(f"  Done     : {done}")
        print(f"  Failed   : {failed}")
        print(f"  Total    : {len(self._list.items)}")
        print(f"")
        print(f"  Files created : {self._list.total_files_created}")
        print(f"  Fixes applied : {self._list.total_fixes_applied}")
        print(f"  Cycles run    : {self._list.total_cycles_run}")

        if self._list.grade_history:
            print(f"\n  GRADE HISTORY:")
            for page, grades in self._list.grade_history.items():
                trend = " → ".join(f"{g:.1f}%" for g in grades)
                print(f"    {page}: {trend}")

        # Show open critical/high items
        open_critical = [
            i
            for i in self._list.items
            if i.status in (TodoStatus.PENDING, TodoStatus.IN_PROGRESS)
            and i.priority in (TodoPriority.CRITICAL, TodoPriority.HIGH)
        ]
        if open_critical:
            print(f"\n  OPEN HIGH-PRIORITY ITEMS:")
            for item in open_critical[:10]:
                print(f"    [{item.priority.upper():8s}] {item.title[:60]}")

        print(f"{'=' * 60}\n")

    def export_markdown(self, output_path: Optional[str] = None) -> str:
        """Export the todo list as a markdown file."""
        lines = [
            f"# Build Todo List: {self._list.project_name}",
            f"",
            f"**Updated:** {self._list.updated_at}",
            f"**Phase:** {self._list.current_phase}",
            f"**Cycle:** {self._list.current_cycle}",
            f"",
        ]

        # Group by category
        by_category: Dict[str, List[TodoItem]] = {}
        for item in self._list.items:
            cat = item.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(item)

        for category, items in sorted(by_category.items()):
            lines.append(f"## {category.title()}")
            lines.append("")
            for item in items:
                status_emoji = {
                    TodoStatus.PENDING: "⬜",
                    TodoStatus.IN_PROGRESS: "🔄",
                    TodoStatus.DONE: "✅",
                    TodoStatus.FAILED: "❌",
                    TodoStatus.BLOCKED: "🚫",
                    TodoStatus.SKIPPED: "⏭️",
                }.get(item.status, "⬜")

                lines.append(
                    f"- {status_emoji} **[{item.priority.upper()}]** {item.title}"
                )
                if item.page:
                    lines.append(f"  - Page: `{item.page}`")
                if item.file_path:
                    lines.append(f"  - File: `{item.file_path}`")
                if item.fix_suggestion:
                    lines.append(f"  - Fix: {item.fix_suggestion}")
                if item.resolution_notes:
                    lines.append(f"  - Notes: {item.resolution_notes}")

            lines.append("")

        content = "\n".join(lines)

        if output_path:
            Path(output_path).write_text(content)
        elif self.project_path:
            md_path = self.project_path / "docs" / "build-receipts" / "todo.md"
            md_path.write_text(content)

        return content

    @property
    def todo_list(self) -> TodoList:
        """Access the underlying todo list."""
        return self._list
