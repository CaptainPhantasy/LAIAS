"""
Search & Research Tools Configuration

Tools for web search, code search, and research across various sources.
Implements Layer 1 (Web Search Priority) of the 7-Layer Data Collection Protocol.
"""

import os
from dataclasses import dataclass, field
from typing import Any

import structlog

from app.tools.registry import ToolCategory, ToolConfig

logger = structlog.get_logger()


@dataclass
class SearchToolsConfig:
    """Configuration for Search & Research tools.

    Layer 1 — Web Search Priority (MANDATORY FIRST STEP):
    - ALWAYS try web search first (up to 2 attempts) before scraping any website.
    - Check for public APIs before resorting to browser scraping.
    - Web search is faster, safer, and doesn't trigger bot detection.
    - Only scrape when search and API approaches both fail.

    Full 7-Layer Protocol Reference:
    1. Web Search Priority (this layer) - search first, scrape last resort
    2. Human Timing - 5-12s delays, max 5 pages/session, 15s breaks
    3. Fingerprint Protection - real browser, hide webdriver, randomize canvas
    4. Session Consistency - cookies, referer headers, natural navigation
    5. Proxy & IP Management - residential proxies, per-session rotation
    6. CAPTCHA & Block Response - stop on CAPTCHA, retry 429s once
    7. Content Extraction - LLM-based extraction, validate, deduplicate

    Decision Tree: 1. Web search → 2. Public API → 3. Scrape (LAST RESORT ONLY)
    """

    # =========================================================================
    # Layer 1: Web Search Priority (ALWAYS TRY FIRST)
    # =========================================================================
    try_search_first: bool = True  # ALWAYS try search before scraping
    max_search_attempts: int = 2  # Up to 2 search attempts before fallback
    check_public_apis: bool = True  # Check APIs (GitHub, arXiv, NVD, etc.)
    search_before_scrape: bool = True  # Enforce search-first policy

    # General search settings
    max_results: int = 10
    search_timeout: int = 30
    include_snippets: bool = True

    # Serper settings
    serper_search_type: str = "search"  # search, images, videos, news

    # Google settings
    google_search_engine_id: str | None = None

    # DuckDuckGo settings
    ddg_region: str = "us-en"
    ddg_safe_search: bool = True

    # Exa settings
    exa_use_autoprompt: bool = True
    exa_num_results: int = 10

    # Tavily settings
    tavily_search_depth: str = "basic"  # basic, advanced
    tavily_include_domains: list[str] = field(default_factory=list)
    tavily_exclude_domains: list[str] = field(default_factory=list)

    # GitHub settings
    github_search_type: str = "repository"  # repository, code, issues

    @staticmethod
    def get_tool_configs() -> list[ToolConfig]:
        """Get all Search & Research tool configurations."""
        return [
            ToolConfig(
                name="SerperDevTool",
                import_path="crewai_tools.SerperDevTool",
                category=ToolCategory.SEARCH_RESEARCH,
                description="Google search via Serper API",
                required_env_vars=["SERPER_API_KEY"],
            ),
            ToolConfig(
                name="GoogleSearchTool",
                import_path="crewai_tools.GoogleSearchTool",
                category=ToolCategory.SEARCH_RESEARCH,
                description="Google Custom Search API",
                required_env_vars=["GOOGLE_API_KEY", "GOOGLE_CSE_ID"],
            ),
            ToolConfig(
                name="BingSearchTool",
                import_path="crewai_tools.BingSearchTool",
                category=ToolCategory.SEARCH_RESEARCH,
                description="Bing Search API",
                required_env_vars=["BING_SUBSCRIPTION_KEY"],
            ),
            ToolConfig(
                name="DuckDuckGoSearchTool",
                import_path="crewai_tools.DuckDuckGoSearchTool",
                category=ToolCategory.SEARCH_RESEARCH,
                description="Search via DuckDuckGo (no API key needed)",
                dependencies=["duckduckgo-search"],
            ),
            ToolConfig(
                name="SearxSearchTool",
                import_path="crewai_tools.SearxSearchTool",
                category=ToolCategory.SEARCH_RESEARCH,
                description="Privacy-focused metasearch engine",
            ),
            ToolConfig(
                name="EXASearchTool",
                import_path="crewai_tools.EXASearchTool",
                category=ToolCategory.SEARCH_RESEARCH,
                description="Exa AI neural search",
                required_env_vars=["EXA_API_KEY"],
            ),
            ToolConfig(
                name="TavilySearchTool",
                import_path="crewai_tools.TavilySearchTool",
                category=ToolCategory.SEARCH_RESEARCH,
                description="Tavily AI-powered search",
                required_env_vars=["TAVILY_API_KEY"],
            ),
            ToolConfig(
                name="GithubSearchTool",
                import_path="crewai_tools.GithubSearchTool",
                category=ToolCategory.SEARCH_RESEARCH,
                description="Search GitHub repositories",
                required_env_vars=["GITHUB_TOKEN"],
            ),
            ToolConfig(
                name="CodeDocsSearchTool",
                import_path="crewai_tools.CodeDocsSearchTool",
                category=ToolCategory.SEARCH_RESEARCH,
                description="Search code documentation",
            ),
            ToolConfig(
                name="CodeSearchTool",
                import_path="crewai_tools.CodeSearchTool",
                category=ToolCategory.SEARCH_RESEARCH,
                description="Search through codebases",
            ),
            ToolConfig(
                name="YouTubeSearchTool",
                import_path="crewai_tools.YouTubeSearchTool",
                category=ToolCategory.SEARCH_RESEARCH,
                description="Search YouTube videos",
                dependencies=["youtube-search"],
            ),
            ToolConfig(
                name="YouTubeVideoSearchTool",
                import_path="crewai_tools.YouTubeVideoSearchTool",
                category=ToolCategory.SEARCH_RESEARCH,
                description="Search within YouTube video content",
                dependencies=["youtube-transcript-api"],
            ),
            ToolConfig(
                name="ArxivSearchTool",
                import_path="crewai_tools.ArxivSearchTool",
                category=ToolCategory.SEARCH_RESEARCH,
                description="Search arXiv academic papers",
                dependencies=["arxiv"],
            ),
            ToolConfig(
                name="PubmedSearchTool",
                import_path="crewai_tools.PubmedSearchTool",
                category=ToolCategory.SEARCH_RESEARCH,
                description="Search PubMed medical literature",
                dependencies=["biopython"],
            ),
            ToolConfig(
                name="WikipediaSearchTool",
                import_path="crewai_tools.WikipediaSearchTool",
                category=ToolCategory.SEARCH_RESEARCH,
                description="Search Wikipedia articles",
                dependencies=["wikipedia"],
            ),
        ]

    def get_search_tools(self, env_vars: dict[str, str] | None = None) -> list[Any]:
        """
        Get instantiated search tools.

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

    def get_tavily_config(self) -> dict[str, Any]:
        """Get Tavily configuration."""
        return {
            "search_depth": self.tavily_search_depth,
            "include_domains": self.tavily_include_domains,
            "exclude_domains": self.tavily_exclude_domains,
            "max_results": self.max_results,
        }
