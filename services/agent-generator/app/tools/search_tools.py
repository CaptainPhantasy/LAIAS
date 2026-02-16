"""
Search & Research Tools Configuration

Tools for web search, code search, and research across various sources.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import os

from app.tools.registry import ToolCategory, ToolConfig


@dataclass
class SearchToolsConfig:
    """Configuration for Search & Research tools."""

    # General search settings
    max_results: int = 10
    search_timeout: int = 30
    include_snippets: bool = True

    # Serper settings
    serper_search_type: str = "search"  # search, images, videos, news

    # Google settings
    google_search_engine_id: Optional[str] = None

    # DuckDuckGo settings
    ddg_region: str = "us-en"
    ddg_safe_search: bool = True

    # Exa settings
    exa_use_autoprompt: bool = True
    exa_num_results: int = 10

    # Tavily settings
    tavily_search_depth: str = "basic"  # basic, advanced
    tavily_include_domains: List[str] = field(default_factory=list)
    tavily_exclude_domains: List[str] = field(default_factory=list)

    # GitHub settings
    github_search_type: str = "repository"  # repository, code, issues

    @staticmethod
    def get_tool_configs() -> List[ToolConfig]:
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

    def get_search_tools(self, env_vars: Optional[Dict[str, str]] = None) -> List[Any]:
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
                except Exception:
                    pass

        return tools

    def get_tavily_config(self) -> Dict[str, Any]:
        """Get Tavily configuration."""
        return {
            "search_depth": self.tavily_search_depth,
            "include_domains": self.tavily_include_domains,
            "exclude_domains": self.tavily_exclude_domains,
            "max_results": self.max_results,
        }
