"""
Web Scraping & Browsing Tools Configuration

Tools for extracting data from websites and browser automation.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import os

from app.tools.registry import ToolCategory, ToolConfig


@dataclass
class WebToolsConfig:
    """Configuration for Web Scraping & Browsing tools."""

    # General scraping settings
    user_agent: str = "LAIAS-Agent/1.0 (+https://github.com/laias)"
    request_timeout: int = 30
    max_retries: int = 3
    rate_limit_delay: float = 1.0  # seconds between requests

    # Selenium settings
    selenium_headless: bool = True
    selenium_browser: str = "chrome"  # chrome, firefox, edge
    selenium_page_load_timeout: int = 30

    # Playwright settings
    playwright_headless: bool = True
    playwright_browser: str = "chromium"  # chromium, firefox, webkit
    playwright_timeout: int = 30000  # milliseconds

    # Firecrawl settings
    firecrawl_formats: List[str] = field(default_factory=lambda: ["markdown", "html"])
    firecrawl_max_crawl_pages: int = 100

    # Browserbase settings
    browserbase_timeout: int = 30000

    @staticmethod
    def get_tool_configs() -> List[ToolConfig]:
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

    def get_web_tools(self, env_vars: Optional[Dict[str, str]] = None) -> List[Any]:
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
                except Exception:
                    pass

        return tools

    def get_selenium_config(self) -> Dict[str, Any]:
        """Get Selenium configuration."""
        return {
            "headless": self.selenium_headless,
            "browser": self.selenium_browser,
            "page_load_timeout": self.selenium_page_load_timeout,
        }

    def get_playwright_config(self) -> Dict[str, Any]:
        """Get Playwright configuration."""
        return {
            "headless": self.playwright_headless,
            "browser": self.playwright_browser,
            "timeout": self.playwright_timeout,
        }
