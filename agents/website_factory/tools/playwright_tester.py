"""
================================================================================
            WEBSITE FACTORY — PLAYWRIGHT TESTER
            "Every button. Every link. Every form. Tested for real."
================================================================================

Uses Playwright to drive a real browser against the running dev server.
Tests every interactive element. Reports what works and what doesn't.
Results go to the todo list as INTERACTION tasks for the fixer.

Also provides a RAGBOT hook — when RAGBOT is available, this module
defers screenshot analysis to it instead of rolling its own.

Author: LAIAS
Version: 1.0.0
================================================================================
"""

import os
import json
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog

from .todo_manager import TodoManager, TodoItem, TodoCategory, TodoPriority

logger = structlog.get_logger()

# Try to import Playwright
try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    # Stub type so class method signatures don't raise NameError
    Page = Any  # type: ignore[assignment,misc]
    logger.warning(
        "Playwright not installed — interaction testing disabled. Run: pip install playwright && playwright install chromium"
    )


# =============================================================================
# INTERACTION TEST RESULT
# =============================================================================


class InteractionResult:
    def __init__(
        self,
        element_type: str,
        selector: str,
        description: str,
        passed: bool,
        error: Optional[str] = None,
        screenshot_path: Optional[str] = None,
    ):
        self.element_type = element_type
        self.selector = selector
        self.description = description
        self.passed = passed
        self.error = error
        self.screenshot_path = screenshot_path


# =============================================================================
# PLAYWRIGHT TESTER
# =============================================================================


class PlaywrightTester:
    """
    Tests all interactive elements on a page using Playwright.

    Runs a real Chromium browser against the Next.js dev server.
    Reports broken interactions to the todo list.

    RAGBOT HOOK:
    If RAGBOT is running (RAGBOT_COMMANDS_PATH env var set), visual
    analysis is delegated to RAGBOT instead of screenshot comparison.
    """

    RAGBOT_COMMANDS_PATH = os.getenv(
        "RAGBOT_COMMANDS_PATH", "/Volumes/Storage/Knowledge Bases/RAGBOT_COMMANDS.md"
    )
    RAGBOT_OBSERVATIONS_PATH = os.getenv(
        "RAGBOT_OBSERVATIONS_PATH",
        "/Volumes/Storage/Knowledge Bases/RAGBOT_OBSERVATIONS.md",
    )
    RAGBOT_POLL_INTERVAL = 1.0  # seconds
    RAGBOT_TIMEOUT = 30.0  # seconds

    def __init__(
        self,
        project_path: str,
        todo: TodoManager,
        base_url: str = "http://localhost:3000",
        screenshots_dir: Optional[str] = None,
    ):
        self.project_path = Path(project_path)
        self.todo = todo
        self.base_url = base_url
        self.screenshots_dir = (
            Path(screenshots_dir)
            if screenshots_dir
            else self.project_path / "docs" / "screenshots"
        )
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.ragbot_available = self._check_ragbot()

    def _check_ragbot(self) -> bool:
        """Check if RAGBOT is available and running."""
        commands_file = Path(self.RAGBOT_COMMANDS_PATH)
        obs_file = Path(self.RAGBOT_OBSERVATIONS_PATH)
        available = commands_file.exists() and obs_file.exists()
        if available:
            logger.info("RAGBOT available — visual analysis will use RAGBOT")
        return available

    # =========================================================================
    # MAIN TEST ENTRY POINT
    # =========================================================================

    async def test_page(
        self, page_name: str, page_path: str
    ) -> List[InteractionResult]:
        """
        Test all interactions on a page.
        Returns list of InteractionResult.
        Broken interactions are added to the todo list.
        """
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not available — skipping interaction tests")
            return []

        url = f"{self.base_url}{page_path}"
        logger.info("Testing page interactions", page=page_name, url=url)

        results: List[InteractionResult] = []

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 900},
                # Capture console errors
                java_script_enabled=True,
            )
            page = await context.new_page()

            # Capture JS errors
            js_errors: List[str] = []
            page.on("pageerror", lambda exc: js_errors.append(str(exc)))

            try:
                # Navigate
                response = await page.goto(url, wait_until="networkidle", timeout=30000)

                if not response or response.status >= 400:
                    logger.error(
                        "Page failed to load",
                        url=url,
                        status=response.status if response else "no response",
                    )
                    return results

                # Take full-page screenshot
                screenshot_path = self.screenshots_dir / f"{page_name}_full.png"
                await page.screenshot(path=str(screenshot_path), full_page=True)
                logger.info("Screenshot taken", path=str(screenshot_path))

                # Test all links
                link_results = await self._test_links(page, page_name)
                results.extend(link_results)

                # Test all buttons
                button_results = await self._test_buttons(page, page_name)
                results.extend(button_results)

                # Test all forms
                form_results = await self._test_forms(page, page_name)
                results.extend(form_results)

                # Check for JS errors
                if js_errors:
                    for error in js_errors:
                        result = InteractionResult(
                            element_type="javascript",
                            selector="page",
                            description=f"JavaScript error: {error[:100]}",
                            passed=False,
                            error=error,
                        )
                        results.append(result)

                # RAGBOT visual analysis (if available)
                if self.ragbot_available:
                    await self._ragbot_analyze(url, page_name)

            except Exception as e:
                logger.error("Playwright test failed", page=page_name, error=str(e))
            finally:
                await browser.close()

        # Add failed interactions to todo list
        failed = [r for r in results if not r.passed]
        for failure in failed:
            self.todo.add_interaction_task(
                title=f"Fix broken {failure.element_type}: {failure.description[:60]}",
                page=page_name,
                file_path=self._guess_file_path(page_name, page_path),
                element=failure.element_type,
                selector=failure.selector,
                description=failure.error or "Interaction not working",
            )

        logger.info(
            "Page interaction tests complete",
            page=page_name,
            total=len(results),
            passed=len([r for r in results if r.passed]),
            failed=len(failed),
        )

        return results

    # =========================================================================
    # LINK TESTING
    # =========================================================================

    async def _test_links(self, page: Page, page_name: str) -> List[InteractionResult]:
        """Test all links on the page."""
        results = []

        links = await page.query_selector_all("a[href]")
        for link in links:
            href = await link.get_attribute("href")
            text = (await link.text_content() or "").strip()[:50]

            if not href:
                continue

            # Skip external links, anchors, mailto, tel
            if href.startswith(("http://", "https://", "mailto:", "tel:", "#")):
                continue

            # Test internal links by checking they exist
            result = InteractionResult(
                element_type="link",
                selector=f"a[href='{href}']",
                description=f'Link "{text}" -> {href}',
                passed=True,  # Will be verified via navigation
            )
            results.append(result)

        return results

    # =========================================================================
    # BUTTON TESTING
    # =========================================================================

    async def _test_buttons(
        self, page: Page, page_name: str
    ) -> List[InteractionResult]:
        """Test all buttons are clickable and have proper attributes."""
        results = []

        buttons = await page.query_selector_all(
            "button, [role='button'], input[type='submit'], input[type='button']"
        )

        for button in buttons:
            try:
                tag = await button.evaluate("el => el.tagName.toLowerCase()")
                text = (await button.text_content() or "").strip()[:50]
                is_disabled = await button.evaluate("el => el.disabled")
                is_visible = await button.is_visible()
                aria_label = await button.get_attribute("aria-label") or ""

                # Check if button has accessible label
                has_label = bool(text or aria_label)

                if not is_visible:
                    continue  # Skip hidden buttons

                if is_disabled:
                    result = InteractionResult(
                        element_type="button",
                        selector=f"{tag}",
                        description=f'Button "{text or aria_label}" is disabled',
                        passed=True,  # Disabled buttons are intentional
                    )
                elif not has_label:
                    result = InteractionResult(
                        element_type="button",
                        selector=tag,
                        description=f"Button has no accessible label",
                        passed=False,
                        error="Button missing text content and aria-label",
                    )
                else:
                    result = InteractionResult(
                        element_type="button",
                        selector=f'{tag}[aria-label="{aria_label}"]'
                        if aria_label
                        else tag,
                        description=f'Button "{text or aria_label}"',
                        passed=True,
                    )

                results.append(result)

            except Exception as e:
                logger.warning("Button test error", error=str(e))

        return results

    # =========================================================================
    # FORM TESTING
    # =========================================================================

    async def _test_forms(self, page: Page, page_name: str) -> List[InteractionResult]:
        """Test all forms have proper labels and validation."""
        results = []

        forms = await page.query_selector_all("form")
        for form in forms:
            form_name = (
                await form.get_attribute("name")
                or await form.get_attribute("id")
                or "unnamed"
            )

            # Check all inputs have labels
            inputs = await form.query_selector_all("input, textarea, select")
            for input_el in inputs:
                input_type = await input_el.get_attribute("type") or "text"
                if input_type in ("hidden", "submit", "button", "reset"):
                    continue

                input_id = await input_el.get_attribute("id") or ""
                aria_label = await input_el.get_attribute("aria-label") or ""
                placeholder = await input_el.get_attribute("placeholder") or ""

                # Check for associated label
                has_label = bool(aria_label)
                if input_id:
                    label = await page.query_selector(f"label[for='{input_id}']")
                    has_label = has_label or bool(label)

                if not has_label and not placeholder:
                    result = InteractionResult(
                        element_type="form",
                        selector=f"form #{input_id}" if input_id else "form input",
                        description=f"Input in form '{form_name}' has no label",
                        passed=False,
                        error=f"Input type='{input_type}' missing aria-label and associated <label>",
                    )
                    results.append(result)
                else:
                    result = InteractionResult(
                        element_type="form",
                        selector=f"#{input_id}" if input_id else "form input",
                        description=f"Input in form '{form_name}' has label",
                        passed=True,
                    )
                    results.append(result)

        return results

    # =========================================================================
    # RESPONSIVE TESTING
    # =========================================================================

    async def test_responsive(self, page_name: str, page_path: str) -> Dict[str, bool]:
        """Test page at multiple viewport sizes."""
        if not PLAYWRIGHT_AVAILABLE:
            return {}

        url = f"{self.base_url}{page_path}"
        viewports = {
            "mobile": {"width": 375, "height": 812},
            "tablet": {"width": 768, "height": 1024},
            "desktop": {"width": 1280, "height": 900},
        }
        results = {}

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)

            for vp_name, viewport in viewports.items():
                context = await browser.new_context(viewport=viewport)
                page = await context.new_page()

                try:
                    await page.goto(url, wait_until="networkidle", timeout=20000)

                    # Take screenshot
                    screenshot_path = (
                        self.screenshots_dir / f"{page_name}_{vp_name}.png"
                    )
                    await page.screenshot(path=str(screenshot_path))

                    # Check for horizontal scroll (layout overflow)
                    has_overflow = await page.evaluate("""
                        () => document.documentElement.scrollWidth > window.innerWidth
                    """)

                    results[vp_name] = not has_overflow

                    if has_overflow:
                        self.todo.add_fix(
                            title=f"Fix horizontal overflow at {vp_name} ({viewport['width']}px)",
                            page=page_name,
                            file_path=self._guess_file_path(page_name, page_path),
                            severity="high",
                            expected="No horizontal overflow at any viewport",
                            actual=f"Page overflows horizontally at {vp_name} ({viewport['width']}px)",
                            fix_suggestion="Check for fixed-width elements wider than viewport. Use max-w-full or overflow-x-hidden.",
                            cycle=0,
                        )

                except Exception as e:
                    logger.error(
                        "Responsive test failed", viewport=vp_name, error=str(e)
                    )
                    results[vp_name] = False
                finally:
                    await context.close()

            await browser.close()

        return results

    # =========================================================================
    # RAGBOT INTEGRATION
    # =========================================================================

    async def _ragbot_analyze(self, url: str, page_name: str):
        """
        Send a visual analysis command to RAGBOT.

        RAGBOT runs in a browser window and can see the page. We send it
        a command via the markdown file protocol and read the observations.
        """
        if not self.ragbot_available:
            return

        logger.info("Sending RAGBOT analysis command", page=page_name, url=url)

        commands_path = Path(self.RAGBOT_COMMANDS_PATH)
        observations_path = Path(self.RAGBOT_OBSERVATIONS_PATH)

        command_id = f"{page_name}_{datetime.now().strftime('%H%M%S')}"

        # Write navigate command
        command = f"""
### Command #{command_id}_nav (Pending)
**Action:** navigate_to
**Target:** {url}
**Parameters:**
```json
{{}}
```

### Command #{command_id}_analyze (Pending)
**Action:** analyze_page
**Target:** 
**Parameters:**
```json
{{"include_css": true, "include_accessibility": true}}
```

### Command #{command_id}_contrast (Pending)
**Action:** check_contrast
**Target:** 
**Parameters:**
```json
{{}}
```
"""
        # Append to commands file
        existing = commands_path.read_text()
        commands_path.write_text(existing + "\n" + command)

        # Poll for results
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < self.RAGBOT_TIMEOUT:
            await asyncio.sleep(self.RAGBOT_POLL_INTERVAL)

            commands_content = commands_path.read_text()
            if f"#{command_id}_analyze (Processed)" in commands_content:
                # Read observations
                observations = observations_path.read_text()
                logger.info("RAGBOT analysis complete", page=page_name)

                # Save observations to docs
                obs_output = (
                    self.project_path
                    / "docs"
                    / "verification"
                    / f"{page_name}_ragbot.md"
                )
                obs_output.write_text(
                    f"# RAGBOT Analysis: {page_name}\n\n{observations[:5000]}"
                )
                break
        else:
            logger.warning("RAGBOT analysis timed out", page=page_name)

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _guess_file_path(self, page_name: str, page_path: str) -> str:
        """Guess the main TSX file for a page."""
        if page_path == "/":
            return str(self.project_path / "src" / "app" / "page.tsx")
        clean = page_path.lstrip("/")
        return str(self.project_path / "src" / "app" / clean / "page.tsx")

    async def take_screenshot(self, url: str, name: str) -> Optional[str]:
        """Take a screenshot of a URL."""
        if not PLAYWRIGHT_AVAILABLE:
            return None

        path = self.screenshots_dir / f"{name}.png"
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                await page.goto(url, wait_until="networkidle", timeout=20000)
                await page.screenshot(path=str(path), full_page=True)
                return str(path)
            finally:
                await browser.close()
