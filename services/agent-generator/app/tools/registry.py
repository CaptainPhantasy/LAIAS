"""
Tool Registry for LAIAS Agent Generator

Central registry for managing CrewAI tools across all categories.
Provides tool discovery, configuration, and instantiation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type
import structlog

logger = structlog.get_logger()

# Flag to track if crewai is available
CREWAI_AVAILABLE = False
try:
    import crewai
    import crewai_tools
    CREWAI_AVAILABLE = True
except ImportError as e:
    logger.warning("crewai_tools not available", error=str(e))
except Exception as e:
    # Catches Pydantic V1 incompatibility with Python 3.14+
    logger.warning("crewai_tools import failed - Python 3.14+ may not be supported", error=str(e))


class ToolCategory(Enum):
    """CrewAI tool categories."""
    FILE_DOCUMENT = "file_document"
    WEB_SCRAPING = "web_scraping"
    SEARCH_RESEARCH = "search_research"
    DATABASE_DATA = "database_data"
    AI_ML = "ai_ml"
    CLOUD_STORAGE = "cloud_storage"
    AUTOMATION = "automation"
    INTEGRATION = "integration"


@dataclass
class ToolConfig:
    """Configuration for a single tool."""
    name: str
    import_path: str
    category: ToolCategory
    description: str
    required_env_vars: List[str] = field(default_factory=list)
    optional_env_vars: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    default_config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    max_usage_count: Optional[int] = None

    def is_available(self, env_vars: Dict[str, str]) -> bool:
        """Check if all required environment variables are set."""
        return all(env_vars.get(var) for var in self.required_env_vars)

    def get_missing_config(self, env_vars: Dict[str, str]) -> List[str]:
        """Get list of missing required environment variables."""
        return [var for var in self.required_env_vars if not env_vars.get(var)]


class ToolRegistry:
    """
    Central registry for all CrewAI tools.

    Manages tool discovery, configuration, and instantiation.
    """

    def __init__(self):
        self._tools: Dict[str, ToolConfig] = {}
        self._categories: Dict[ToolCategory, List[str]] = {
            cat: [] for cat in ToolCategory
        }
        self._register_all_tools()

    def _register_all_tools(self):
        """Register all available CrewAI tools."""

        # === FILE & DOCUMENT TOOLS ===
        self.register(ToolConfig(
            name="FileReadTool",
            import_path="crewai_tools.FileReadTool",
            category=ToolCategory.FILE_DOCUMENT,
            description="Read content from various file formats (txt, pdf, docx, etc.)",
            dependencies=["pypdf", "python-docx"],
        ))

        self.register(ToolConfig(
            name="FileWriteTool",
            import_path="crewai_tools.FileWriteTool",
            category=ToolCategory.FILE_DOCUMENT,
            description="Write content to files with various formats",
        ))

        self.register(ToolConfig(
            name="DirectoryReadTool",
            import_path="crewai_tools.DirectoryReadTool",
            category=ToolCategory.FILE_DOCUMENT,
            description="Read and list directory contents",
        ))

        self.register(ToolConfig(
            name="DirectorySearchTool",
            import_path="crewai_tools.DirectorySearchTool",
            category=ToolCategory.FILE_DOCUMENT,
            description="Search for files within directories",
        ))

        self.register(ToolConfig(
            name="CSVSearchTool",
            import_path="crewai_tools.CSVSearchTool",
            category=ToolCategory.FILE_DOCUMENT,
            description="Search and query CSV files",
            dependencies=["pandas"],
        ))

        self.register(ToolConfig(
            name="JSONSearchTool",
            import_path="crewai_tools.JSONSearchTool",
            category=ToolCategory.FILE_DOCUMENT,
            description="Search and query JSON files",
        ))

        self.register(ToolConfig(
            name="XMLSearchTool",
            import_path="crewai_tools.XMLSearchTool",
            category=ToolCategory.FILE_DOCUMENT,
            description="Search and query XML files",
            dependencies=["lxml"],
        ))

        self.register(ToolConfig(
            name="PDFSearchTool",
            import_path="crewai_tools.PDFSearchTool",
            category=ToolCategory.FILE_DOCUMENT,
            description="Search and extract content from PDF files",
            dependencies=["pypdf"],
        ))

        self.register(ToolConfig(
            name="DocxSearchTool",
            import_path="crewai_tools.DocxSearchTool",
            category=ToolCategory.FILE_DOCUMENT,
            description="Search and extract content from DOCX files",
            dependencies=["python-docx"],
        ))

        self.register(ToolConfig(
            name="ExcelSearchTool",
            import_path="crewai_tools.ExcelSearchTool",
            category=ToolCategory.FILE_DOCUMENT,
            description="Search and query Excel files",
            dependencies=["openpyxl", "pandas"],
        ))

        # === WEB SCRAPING & BROWSING TOOLS ===
        self.register(ToolConfig(
            name="ScrapeWebsiteTool",
            import_path="crewai_tools.ScrapeWebsiteTool",
            category=ToolCategory.WEB_SCRAPING,
            description="Scrape content from websites",
            dependencies=["beautifulsoup4", "requests"],
        ))

        self.register(ToolConfig(
            name="SeleniumScrapingTool",
            import_path="crewai_tools.SeleniumScrapingTool",
            category=ToolCategory.WEB_SCRAPING,
            description="Scrape dynamic websites using Selenium",
            dependencies=["selenium"],
        ))

        self.register(ToolConfig(
            name="FirecrawlScrapeTool",
            import_path="crewai_tools.FirecrawlScrapeTool",
            category=ToolCategory.WEB_SCRAPING,
            description="Scrape using Firecrawl API",
            required_env_vars=["FIRECRAWL_API_KEY"],
        ))

        self.register(ToolConfig(
            name="FirecrawlCrawlWebsiteTool",
            import_path="crewai_tools.FirecrawlCrawlWebsiteTool",
            category=ToolCategory.WEB_SCRAPING,
            description="Crawl entire websites using Firecrawl",
            required_env_vars=["FIRECRAWL_API_KEY"],
        ))

        self.register(ToolConfig(
            name="BrowserbaseLoadTool",
            import_path="crewai_tools.BrowserbaseLoadTool",
            category=ToolCategory.WEB_SCRAPING,
            description="Load pages using Browserbase",
            required_env_vars=["BROWSERBASE_API_KEY"],
        ))

        self.register(ToolConfig(
            name="BeautifulSoupTool",
            import_path="crewai_tools.BeautifulSoupTool",
            category=ToolCategory.WEB_SCRAPING,
            description="Parse HTML with BeautifulSoup",
            dependencies=["beautifulsoup4"],
        ))

        self.register(ToolConfig(
            name="PlaywrightBrowserTool",
            import_path="crewai_tools.PlaywrightBrowserTool",
            category=ToolCategory.WEB_SCRAPING,
            description="Browser automation with Playwright",
            dependencies=["playwright"],
        ))

        self.register(ToolConfig(
            name="StagehandTool",
            import_path="crewai_tools.StagehandTool",
            category=ToolCategory.WEB_SCRAPING,
            description="AI-powered web browsing with Stagehand",
            dependencies=["stagehand"],
        ))

        # === SEARCH & RESEARCH TOOLS ===
        self.register(ToolConfig(
            name="SerperDevTool",
            import_path="crewai_tools.SerperDevTool",
            category=ToolCategory.SEARCH_RESEARCH,
            description="Google search via Serper API",
            required_env_vars=["SERPER_API_KEY"],
        ))

        self.register(ToolConfig(
            name="GoogleSearchTool",
            import_path="crewai_tools.GoogleSearchTool",
            category=ToolCategory.SEARCH_RESEARCH,
            description="Google Custom Search API",
            required_env_vars=["GOOGLE_API_KEY", "GOOGLE_CSE_ID"],
        ))

        self.register(ToolConfig(
            name="BingSearchTool",
            import_path="crewai_tools.BingSearchTool",
            category=ToolCategory.SEARCH_RESEARCH,
            description="Bing Search API",
            required_env_vars=["BING_SUBSCRIPTION_KEY"],
        ))

        self.register(ToolConfig(
            name="DuckDuckGoSearchTool",
            import_path="crewai_tools.DuckDuckGoSearchTool",
            category=ToolCategory.SEARCH_RESEARCH,
            description="Search via DuckDuckGo (no API key needed)",
            dependencies=["duckduckgo-search"],
        ))

        self.register(ToolConfig(
            name="SearxSearchTool",
            import_path="crewai_tools.SearxSearchTool",
            category=ToolCategory.SEARCH_RESEARCH,
            description="Privacy-focused metasearch engine",
        ))

        self.register(ToolConfig(
            name="EXASearchTool",
            import_path="crewai_tools.EXASearchTool",
            category=ToolCategory.SEARCH_RESEARCH,
            description="Exa AI neural search",
            required_env_vars=["EXA_API_KEY"],
        ))

        self.register(ToolConfig(
            name="TavilySearchTool",
            import_path="crewai_tools.TavilySearchTool",
            category=ToolCategory.SEARCH_RESEARCH,
            description="Tavily AI-powered search",
            required_env_vars=["TAVILY_API_KEY"],
        ))

        self.register(ToolConfig(
            name="GithubSearchTool",
            import_path="crewai_tools.GithubSearchTool",
            category=ToolCategory.SEARCH_RESEARCH,
            description="Search GitHub repositories",
            required_env_vars=["GITHUB_TOKEN"],
        ))

        self.register(ToolConfig(
            name="CodeDocsSearchTool",
            import_path="crewai_tools.CodeDocsSearchTool",
            category=ToolCategory.SEARCH_RESEARCH,
            description="Search code documentation",
        ))

        self.register(ToolConfig(
            name="CodeSearchTool",
            import_path="crewai_tools.CodeSearchTool",
            category=ToolCategory.SEARCH_RESEARCH,
            description="Search through codebases",
        ))

        self.register(ToolConfig(
            name="YouTubeSearchTool",
            import_path="crewai_tools.YouTubeSearchTool",
            category=ToolCategory.SEARCH_RESEARCH,
            description="Search YouTube videos",
            dependencies=["youtube-search"],
        ))

        self.register(ToolConfig(
            name="YouTubeVideoSearchTool",
            import_path="crewai_tools.YouTubeVideoSearchTool",
            category=ToolCategory.SEARCH_RESEARCH,
            description="Search within YouTube video content",
            dependencies=["youtube-transcript-api"],
        ))

        # === DATABASE & DATA TOOLS ===
        self.register(ToolConfig(
            name="MySQLSearchTool",
            import_path="crewai_tools.MySQLSearchTool",
            category=ToolCategory.DATABASE_DATA,
            description="Query MySQL databases",
            required_env_vars=["MYSQL_HOST", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE"],
            dependencies=["mysql-connector-python"],
        ))

        self.register(ToolConfig(
            name="PGSearchTool",
            import_path="crewai_tools.PGSearchTool",
            category=ToolCategory.DATABASE_DATA,
            description="Query PostgreSQL databases",
            required_env_vars=["PG_HOST", "PG_USER", "PG_PASSWORD", "PG_DATABASE"],
            dependencies=["psycopg2-binary"],
        ))

        self.register(ToolConfig(
            name="SnowflakeSearchTool",
            import_path="crewai_tools.SnowflakeSearchTool",
            category=ToolCategory.DATABASE_DATA,
            description="Query Snowflake data warehouse",
            required_env_vars=["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD"],
            dependencies=["snowflake-connector-python"],
        ))

        self.register(ToolConfig(
            name="SQLiteSearchTool",
            import_path="crewai_tools.SQLiteSearchTool",
            category=ToolCategory.DATABASE_DATA,
            description="Query SQLite databases",
            dependencies=["sqlite3"],
        ))

        self.register(ToolConfig(
            name="MongoDBSearchTool",
            import_path="crewai_tools.MongoDBSearchTool",
            category=ToolCategory.DATABASE_DATA,
            description="Query MongoDB databases",
            required_env_vars=["MONGODB_URI"],
            dependencies=["pymongo"],
        ))

        self.register(ToolConfig(
            name="QdrantVectorSearchTool",
            import_path="crewai_tools.QdrantVectorSearchTool",
            category=ToolCategory.DATABASE_DATA,
            description="Vector search with Qdrant",
            required_env_vars=["QDRANT_URL"],
            optional_env_vars=["QDRANT_API_KEY"],
            dependencies=["qdrant-client"],
        ))

        self.register(ToolConfig(
            name="WeaviateVectorSearchTool",
            import_path="crewai_tools.WeaviateVectorSearchTool",
            category=ToolCategory.DATABASE_DATA,
            description="Vector search with Weaviate",
            required_env_vars=["WEAVIATE_URL"],
            optional_env_vars=["WEAVIATE_API_KEY"],
            dependencies=["weaviate-client"],
        ))

        self.register(ToolConfig(
            name="PineconeQueryTool",
            import_path="crewai_tools.PineconeQueryTool",
            category=ToolCategory.DATABASE_DATA,
            description="Vector search with Pinecone",
            required_env_vars=["PINECONE_API_KEY", "PINECONE_ENVIRONMENT"],
            dependencies=["pinecone-client"],
        ))

        self.register(ToolConfig(
            name="ChromaDBSearchTool",
            import_path="crewai_tools.ChromaDBSearchTool",
            category=ToolCategory.DATABASE_DATA,
            description="Vector search with ChromaDB",
            dependencies=["chromadb"],
        ))

        # === AI & MACHINE LEARNING TOOLS ===
        self.register(ToolConfig(
            name="DallETool",
            import_path="crewai_tools.DallETool",
            category=ToolCategory.AI_ML,
            description="Generate images with DALL-E",
            required_env_vars=["OPENAI_API_KEY"],
        ))

        self.register(ToolConfig(
            name="VisionTool",
            import_path="crewai_tools.VisionTool",
            category=ToolCategory.AI_ML,
            description="Computer vision with AI models",
            required_env_vars=["OPENAI_API_KEY"],
        ))

        self.register(ToolConfig(
            name="CodeInterpreterTool",
            import_path="crewai_tools.CodeInterpreterTool",
            category=ToolCategory.AI_ML,
            description="Execute Python code safely",
        ))

        self.register(ToolConfig(
            name="CodeDocsSearchTool",
            import_path="crewai_tools.CodeDocsSearchTool",
            category=ToolCategory.AI_ML,
            description="Search code documentation with embeddings",
        ))

        self.register(ToolConfig(
            name="RagTool",
            import_path="crewai_tools.RagTool",
            category=ToolCategory.AI_ML,
            description="Retrieval-Augmented Generation",
            dependencies=["langchain", "chromadb"],
        ))

        self.register(ToolConfig(
            name="LlamaIndexTool",
            import_path="crewai_tools.LlamaIndexTool",
            category=ToolCategory.AI_ML,
            description="LlamaIndex integration for RAG",
            dependencies=["llama-index"],
        ))

        self.register(ToolConfig(
            name="LangchainTool",
            import_path="crewai_tools.LangchainTool",
            category=ToolCategory.AI_ML,
            description="Use LangChain tools in CrewAI",
            dependencies=["langchain"],
        ))

        self.register(ToolConfig(
            name="HuggingFaceSearchTool",
            import_path="crewai_tools.HuggingFaceSearchTool",
            category=ToolCategory.AI_ML,
            description="Search Hugging Face models and datasets",
            dependencies=["huggingface-hub"],
        ))

        # === CLOUD & STORAGE TOOLS ===
        self.register(ToolConfig(
            name="S3ReaderTool",
            import_path="crewai_tools.S3ReaderTool",
            category=ToolCategory.CLOUD_STORAGE,
            description="Read files from AWS S3",
            required_env_vars=["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
            dependencies=["boto3"],
        ))

        self.register(ToolConfig(
            name="S3WriterTool",
            import_path="crewai_tools.S3WriterTool",
            category=ToolCategory.CLOUD_STORAGE,
            description="Write files to AWS S3",
            required_env_vars=["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
            dependencies=["boto3"],
        ))

        self.register(ToolConfig(
            name="AmazonBedrockTool",
            import_path="crewai_tools.AmazonBedrockTool",
            category=ToolCategory.CLOUD_STORAGE,
            description="Use Amazon Bedrock AI services",
            required_env_vars=["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"],
            dependencies=["boto3"],
        ))

        self.register(ToolConfig(
            name="AzureBlobStorageTool",
            import_path="crewai_tools.AzureBlobStorageTool",
            category=ToolCategory.CLOUD_STORAGE,
            description="Access Azure Blob Storage",
            required_env_vars=["AZURE_STORAGE_CONNECTION_STRING"],
            dependencies=["azure-storage-blob"],
        ))

        self.register(ToolConfig(
            name="GCSTool",
            import_path="crewai_tools.GCSTool",
            category=ToolCategory.CLOUD_STORAGE,
            description="Access Google Cloud Storage",
            required_env_vars=["GOOGLE_APPLICATION_CREDENTIALS"],
            dependencies=["google-cloud-storage"],
        ))

        self.register(ToolConfig(
            name="CloudflareR2Tool",
            import_path="crewai_tools.CloudflareR2Tool",
            category=ToolCategory.CLOUD_STORAGE,
            description="Access Cloudflare R2 storage",
            required_env_vars=["CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_ACCESS_KEY", "CLOUDFLARE_SECRET_KEY"],
            dependencies=["boto3"],
        ))

        # === AUTOMATION TOOLS ===
        self.register(ToolConfig(
            name="ApifyActorTool",
            import_path="crewai_tools.ApifyActorTool",
            category=ToolCategory.AUTOMATION,
            description="Run Apify actors for web automation",
            required_env_vars=["APIFY_API_KEY"],
            dependencies=["apify-client"],
        ))

        self.register(ToolConfig(
            name="ComposioTool",
            import_path="crewai_tools.ComposioTool",
            category=ToolCategory.AUTOMATION,
            description="Integrate with 100+ apps via Composio",
            required_env_vars=["COMPOSIO_API_KEY"],
            dependencies=["composio-client"],
        ))

        self.register(ToolConfig(
            name="MultiOnTool",
            import_path="crewai_tools.MultiOnTool",
            category=ToolCategory.AUTOMATION,
            description="Browser automation with MultiOn",
            required_env_vars=["MULTION_API_KEY"],
        ))

        self.register(ToolConfig(
            name="ZapierActionsTool",
            import_path="crewai_tools.ZapierActionsTool",
            category=ToolCategory.AUTOMATION,
            description="Connect to Zapier actions",
            required_env_vars=["ZAPIER_NLA_API_KEY"],
        ))

        self.register(ToolConfig(
            name="N8nTool",
            import_path="crewai_tools.N8nTool",
            category=ToolCategory.AUTOMATION,
            description="Trigger n8n workflows",
            required_env_vars=["N8N_WEBHOOK_URL"],
        ))

        self.register(ToolConfig(
            name="MakeTool",
            import_path="crewai_tools.MakeTool",
            category=ToolCategory.AUTOMATION,
            description="Integrate with Make.com scenarios",
            required_env_vars=["MAKE_API_KEY"],
        ))

        # === INTEGRATION TOOLS ===
        self.register(ToolConfig(
            name="SlackTool",
            import_path="crewai_tools.SlackTool",
            category=ToolCategory.INTEGRATION,
            description="Interact with Slack",
            required_env_vars=["SLACK_BOT_TOKEN"],
            dependencies=["slack-sdk"],
        ))

        self.register(ToolConfig(
            name="DiscordTool",
            import_path="crewai_tools.DiscordTool",
            category=ToolCategory.INTEGRATION,
            description="Interact with Discord",
            required_env_vars=["DISCORD_BOT_TOKEN"],
            dependencies=["discord.py"],
        ))

        self.register(ToolConfig(
            name="TelegramTool",
            import_path="crewai_tools.TelegramTool",
            category=ToolCategory.INTEGRATION,
            description="Interact with Telegram",
            required_env_vars=["TELEGRAM_BOT_TOKEN"],
            dependencies=["python-telegram-bot"],
        ))

        self.register(ToolConfig(
            name="EmailTool",
            import_path="crewai_tools.EmailTool",
            category=ToolCategory.INTEGRATION,
            description="Send and read emails",
            required_env_vars=["SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"],
        ))

        self.register(ToolConfig(
            name="NotionTool",
            import_path="crewai_tools.NotionTool",
            category=ToolCategory.INTEGRATION,
            description="Interact with Notion",
            required_env_vars=["NOTION_API_KEY"],
            dependencies=["notion-client"],
        ))

        self.register(ToolConfig(
            name="JiraTool",
            import_path="crewai_tools.JiraTool",
            category=ToolCategory.INTEGRATION,
            description="Interact with Jira",
            required_env_vars=["JIRA_API_TOKEN", "JIRA_EMAIL", "JIRA_DOMAIN"],
            dependencies=["atlassian-python-api"],
        ))

        self.register(ToolConfig(
            name="LinearTool",
            import_path="crewai_tools.LinearTool",
            category=ToolCategory.INTEGRATION,
            description="Interact with Linear",
            required_env_vars=["LINEAR_API_KEY"],
            dependencies=["linear-client"],
        ))

        self.register(ToolConfig(
            name="AsanaTool",
            import_path="crewai_tools.AsanaTool",
            category=ToolCategory.INTEGRATION,
            description="Interact with Asana",
            required_env_vars=["ASANA_ACCESS_TOKEN"],
            dependencies=["asana"],
        ))

        self.register(ToolConfig(
            name="TrelloTool",
            import_path="crewai_tools.TrelloTool",
            category=ToolCategory.INTEGRATION,
            description="Interact with Trello",
            required_env_vars=["TRELLO_API_KEY", "TRELLO_TOKEN"],
            dependencies=["trello"],
        ))

        self.register(ToolConfig(
            name="HubspotTool",
            import_path="crewai_tools.HubspotTool",
            category=ToolCategory.INTEGRATION,
            description="Interact with HubSpot CRM",
            required_env_vars=["HUBSPOT_API_KEY"],
            dependencies=["hubspot-api-client"],
        ))

        self.register(ToolConfig(
            name="SalesforceTool",
            import_path="crewai_tools.SalesforceTool",
            category=ToolCategory.INTEGRATION,
            description="Interact with Salesforce",
            required_env_vars=["SALESFORCE_USERNAME", "SALESFORCE_PASSWORD", "SALESFORCE_SECURITY_TOKEN"],
            dependencies=["simple-salesforce"],
        ))

        self.register(ToolConfig(
            name="ZendeskTool",
            import_path="crewai_tools.ZendeskTool",
            category=ToolCategory.INTEGRATION,
            description="Interact with Zendesk",
            required_env_vars=["ZENDESK_EMAIL", "ZENDESK_API_TOKEN", "ZENDESK_DOMAIN"],
            dependencies=["zendesk"],
        ))

        self.register(ToolConfig(
            name="StripeTool",
            import_path="crewai_tools.StripeTool",
            category=ToolCategory.INTEGRATION,
            description="Interact with Stripe payments",
            required_env_vars=["STRIPE_API_KEY"],
            dependencies=["stripe"],
        ))

        self.register(ToolConfig(
            name="TwitterTool",
            import_path="crewai_tools.TwitterTool",
            category=ToolCategory.INTEGRATION,
            description="Interact with Twitter/X",
            required_env_vars=["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_SECRET"],
            dependencies=["tweepy"],
        ))

        self.register(ToolConfig(
            name="LinkedInTool",
            import_path="crewai_tools.LinkedInTool",
            category=ToolCategory.INTEGRATION,
            description="Interact with LinkedIn",
            required_env_vars=["LINKEDIN_ACCESS_TOKEN"],
            dependencies=["linkedin-api"],
        ))

        logger.info("tool_registry_initialized", total_tools=len(self._tools))

    def register(self, config: ToolConfig):
        """Register a tool configuration."""
        self._tools[config.name] = config
        self._categories[config.category].append(config.name)

    def get_tool(self, name: str) -> Optional[ToolConfig]:
        """Get a tool configuration by name."""
        return self._tools.get(name)

    def get_all_tools(self) -> List[ToolConfig]:
        """Get all registered tools."""
        return list(self._tools.values())

    def get_tools_by_category(self, category: ToolCategory) -> List[ToolConfig]:
        """Get all tools in a category."""
        return [self._tools[name] for name in self._categories[category]]

    def get_available_tools(self, env_vars: Dict[str, str]) -> List[ToolConfig]:
        """Get tools that can be used with current environment."""
        return [t for t in self._tools.values() if t.is_available(env_vars) and t.enabled]

    def get_unavailable_tools(self, env_vars: Dict[str, str]) -> Dict[str, List[str]]:
        """Get tools with their missing configuration."""
        result = {}
        for tool in self._tools.values():
            missing = tool.get_missing_config(env_vars)
            if missing:
                result[tool.name] = missing
        return result

    def instantiate_tool(self, name: str, **kwargs) -> Any:
        """
        Instantiate a tool by name with optional configuration.

        Args:
            name: Tool name
            **kwargs: Tool-specific configuration

        Returns:
            Tool instance
        """
        if not CREWAI_AVAILABLE:
            raise ImportError(
                f"Cannot instantiate tool '{name}': crewai_tools is not available. "
                "This may be due to Python version incompatibility (requires <3.14). "
                "The tool registry is still functional for discovery and configuration."
            )

        config = self._tools.get(name)
        if not config:
            raise ValueError(f"Unknown tool: {name}")

        try:
            # Dynamic import
            module_path, class_name = config.import_path.rsplit(".", 1)
            module = __import__(module_path, fromlist=[class_name])
            tool_class = getattr(module, class_name)

            # Merge default config with provided kwargs
            final_config = {**config.default_config, **kwargs}
            if config.max_usage_count:
                final_config["max_usage_count"] = config.max_usage_count

            return tool_class(**final_config)

        except ImportError as e:
            logger.error("tool_import_failed", tool=name, error=str(e))
            raise ImportError(f"Failed to import tool {name}: {e}")

    def get_category_summary(self) -> Dict[str, int]:
        """Get count of tools per category."""
        return {
            cat.value: len(tools)
            for cat, tools in self._categories.items()
        }


# Singleton registry instance
_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def list_available_tools(env_vars: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    """
    List all available tools with their status.

    Args:
        env_vars: Environment variables to check availability

    Returns:
        List of tool info dictionaries
    """
    registry = get_tool_registry()
    env = env_vars or {}

    return [
        {
            "name": tool.name,
            "category": tool.category.value,
            "description": tool.description,
            "available": tool.is_available(env),
            "missing_config": tool.get_missing_config(env),
            "dependencies": tool.dependencies,
        }
        for tool in registry.get_all_tools()
    ]


def get_tools_by_category(category: str) -> List[ToolConfig]:
    """Get tools by category name."""
    registry = get_tool_registry()
    try:
        cat = ToolCategory(category)
        return registry.get_tools_by_category(cat)
    except ValueError:
        return []
