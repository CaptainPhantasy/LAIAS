"""
Web Scraping & Browsing Tools Configuration

Tools for extracting data from websites and browser automation.
Implements the 7-Layer Data Collection Stealth Protocol for human-like
web scraping that avoids bot detection.
"""

import os
from dataclasses import dataclass, field
from typing import Any

import structlog

from app.tools.registry import ToolCategory, ToolConfig

logger = structlog.get_logger()


@dataclass
class WebToolsConfig:
    """Configuration for Web Scraping & Browsing tools.

    Implements the 7-Layer Data Collection Stealth Protocol:
    - Layer 1: Web Search Priority (try search/APIs before scraping)
    - Layer 2: Human Timing (5-12s delays, max 5 pages/session)
    - Layer 3: Fingerprint Protection (real browser, hide webdriver)
    - Layer 4: Session Consistency (cookies, referer, navigation)
    - Layer 5: Proxy & IP Management (residential, per-session rotation)
    - Layer 6: CAPTCHA & Block Response (stop on CAPTCHA, retry 429s)
    - Layer 7: Content Extraction (LLM-based, validate, deduplicate)
    """

    # =========================================================================
    # Layer 1: Web Search Priority
    # =========================================================================
    try_search_first: bool = True
    max_search_attempts: int = 2
    check_public_apis: bool = True

    # =========================================================================
    # Layer 2: Human Timing (HUMAN-LIKE DELAYS - CRITICAL)
    # =========================================================================
    # Old values (2-5s) were too fast and got detected.
    # New values (5-12s) mimic realistic human browsing.
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    request_timeout: int = 30
    max_retries: int = 3
    rate_limit_delay: float = 5.0  # Base delay: 5-12 seconds between requests
    rate_limit_delay_max: float = 12.0  # Maximum delay for randomization
    requests_per_minute: int = 2  # Max 2 requests/min per domain
    max_pages_per_session: int = 5  # Max 5 pages per domain per session
    break_interval_pages: int = 3  # Take a break after 3 pages
    break_duration_seconds: float = 15.0  # 15 second break duration
    backoff_base_seconds: float = 60.0  # Exponential backoff starting at 60s
    randomize_delays: bool = True  # Add ±15% jitter to simulate human variance

    # =========================================================================
    # Layer 3: Fingerprint Protection
    # =========================================================================
    use_real_browser: bool = True  # Use Playwright/Puppeteer, not raw HTTP
    hide_webdriver: bool = True  # Hide navigator.webdriver property
    randomize_canvas: bool = True  # Randomize Canvas fingerprint per session
    randomize_webgl: bool = True  # Randomize WebGL renderer/vendor per session
    consistent_within_session: bool = True  # Don't rotate mid-session
    viewport_width: int = 1920  # Must match user-agent OS
    viewport_height: int = 1080
    user_agent_strategy: str = "fixed"  # 'rotate' or 'fixed'

    # Selenium settings
    selenium_headless: bool = True
    selenium_browser: str = "chrome"  # chrome, firefox, edge
    selenium_page_load_timeout: int = 30

    # Playwright settings
    playwright_headless: bool = True
    playwright_browser: str = "chromium"  # chromium, firefox, webkit
    playwright_timeout: int = 30000  # milliseconds

    # =========================================================================
    # Layer 4: Session Consistency
    # =========================================================================
    persist_cookies: bool = True  # Persist cookies across requests
    send_referer: bool = True  # Send proper Referer headers
    natural_navigation: bool = True  # Navigate home → category → detail
    scroll_before_extract: bool = True  # Scroll before extracting data
    max_read_time_ms: int = 10000  # Simulate up to 10s "reading" time

    # =========================================================================
    # Layer 5: Proxy & IP Management
    # =========================================================================
    proxy_enabled: bool = False  # Enable for high-detection sites
    proxy_type: str = "residential"  # residential, datacenter, mobile
    proxy_rotation_strategy: str = "per_session"  # per_request, per_session, sticky
    proxy_subnet_diversity: bool = True  # Distribute across subnets/ASNs

    # =========================================================================
    # Layer 6: CAPTCHA & Block Response
    # =========================================================================
    stop_on_captcha: bool = True  # STOP immediately on CAPTCHA
    auto_retry_with_backoff: bool = True  # Auto-retry on 429/403
    block_max_retries: int = 1  # Max 1 retry on rate-limited responses
    fallback_to_search: bool = True  # Fall back to web search when blocked
    log_blocked_attempts: bool = True  # Log for monitoring

    # =========================================================================
    # Layer 7: Content Extraction
    # =========================================================================
    extraction_method: str = "llm"  # 'llm' (adaptive) or 'selector' (brittle)
    validate_output: bool = True  # Validate against expected schema
    max_extract_tokens: int = 4000  # Max tokens per page extraction
    deduplicate: bool = True  # Deduplicate across pages within session

    # Firecrawl settings
    firecrawl_formats: list[str] = field(default_factory=lambda: ["markdown", "html"])
    firecrawl_max_crawl_pages: int = 5  # Aligned with max_pages_per_session

    # Browserbase settings
    browserbase_timeout: int = 30000

    @staticmethod
    def get_tool_configs() -> list[ToolConfig]:
        """Get all Web Scraping tool configurations."""
        return [
            ToolConfig(
                name="ScrapeWebsiteTool",
                import_path="crewai_tools.ScrapeWebsiteTool",
                category=ToolCategory.WEB_SCRAPING,
                description="Scrape content from websites",
                dependencies=["beautifulsoup4", "requests"],
            ),
            ToolConfig(
                name="SeleniumScrapingTool",
                import_path="crewai_tools.SeleniumScrapingTool",
                category=ToolCategory.WEB_SCRAPING,
                description="Scrape dynamic websites using Selenium",
                dependencies=["selenium"],
            ),
            ToolConfig(
                name="FirecrawlScrapeTool",
                import_path="crewai_tools.FirecrawlScrapeTool",
                category=ToolCategory.WEB_SCRAPING,
                description="Scrape using Firecrawl API",
                required_env_vars=["FIRECRAWL_API_KEY"],
            ),
            ToolConfig(
                name="FirecrawlCrawlWebsiteTool",
                import_path="crewai_tools.FirecrawlCrawlWebsiteTool",
                category=ToolCategory.WEB_SCRAPING,
                description="Crawl entire websites using Firecrawl",
                required_env_vars=["FIRECRAWL_API_KEY"],
            ),
            ToolConfig(
                name="BrowserbaseLoadTool",
                import_path="crewai_tools.BrowserbaseLoadTool",
                category=ToolCategory.WEB_SCRAPING,
                description="Load pages using Browserbase",
                required_env_vars=["BROWSERBASE_API_KEY"],
            ),
            ToolConfig(
                name="BeautifulSoupTool",
                import_path="crewai_tools.BeautifulSoupTool",
                category=ToolCategory.WEB_SCRAPING,
                description="Parse HTML with BeautifulSoup",
                dependencies=["beautifulsoup4"],
            ),
            ToolConfig(
                name="PlaywrightBrowserTool",
                import_path="crewai_tools.PlaywrightBrowserTool",
                category=ToolCategory.WEB_SCRAPING,
                description="Browser automation with Playwright",
                dependencies=["playwright"],
            ),
            ToolConfig(
                name="StagehandTool",
                import_path="crewai_tools.StagehandTool",
                category=ToolCategory.WEB_SCRAPING,
                description="AI-powered web browsing with Stagehand",
                dependencies=["stagehand"],
            ),
            ToolConfig(
                name="SpiderTool",
                import_path="crewai_tools.SpiderTool",
                category=ToolCategory.WEB_SCRAPING,
                description="High-performance web crawler",
                dependencies=["spider-client"],
            ),
            ToolConfig(
                name="Crawl4AITool",
                import_path="crewai_tools.Crawl4AITool",
                category=ToolCategory.WEB_SCRAPING,
                description="AI-powered web crawling",
                dependencies=["crawl4ai"],
            ),
        ]

    def get_web_tools(self, env_vars: dict[str, str] | None = None) -> list[Any]:
        """
        Get instantiated web scraping tools.

        Args:
            env_vars: Environment variables for configuration

        Returns:
            List of tool instances
        """
        from app.tools.registry import get_tool_registry

        registry = get_tool_registry()
        env = env_vars or dict(os.environ)

        tools = []
        for config in self.get_tool_configs():
            if config.is_available(env):
                try:
                    tool = registry.instantiate_tool(config.name)
                    tools.append(tool)
                except Exception as e:
                    logger.warning("Failed to instantiate tool", tool=config.name, error=str(e))

        return tools

    def get_selenium_config(self) -> dict[str, Any]:
        """Get Selenium configuration."""
        return {
            "headless": self.selenium_headless,
            "browser": self.selenium_browser,
            "page_load_timeout": self.selenium_page_load_timeout,
        }

    def get_playwright_config(self) -> dict[str, Any]:
        """Get Playwright configuration."""
        return {
            "headless": self.playwright_headless,
            "browser": self.playwright_browser,
            "timeout": self.playwright_timeout,
        }
