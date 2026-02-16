"""
LAIAS Tools Integration Module

Comprehensive CrewAI tools integration with MCP server support.
Categories: File & Document, Web Scraping, Search & Research,
Database & Data, AI/ML, Cloud & Storage, Automation, Integrations.
"""

from app.tools.registry import (
    ToolRegistry,
    ToolCategory,
    ToolConfig,
    get_tool_registry,
    list_available_tools,
    get_tools_by_category,
)

from app.tools.file_tools import FileToolsConfig
from app.tools.web_tools import WebToolsConfig
from app.tools.search_tools import SearchToolsConfig
from app.tools.database_tools import DatabaseToolsConfig
from app.tools.ai_tools import AIToolsConfig
from app.tools.cloud_tools import CloudToolsConfig
from app.tools.automation_tools import AutomationToolsConfig
from app.tools.integration_tools import IntegrationToolsConfig
from app.tools.mcp_adapter import MCPToolsAdapter, MCPServerConfig, get_mcp_adapter, list_mcp_presets

__all__ = [
    # Registry
    "ToolRegistry",
    "ToolCategory",
    "ToolConfig",
    "get_tool_registry",
    "list_available_tools",
    "get_tools_by_category",
    # Tool Configurations
    "FileToolsConfig",
    "WebToolsConfig",
    "SearchToolsConfig",
    "DatabaseToolsConfig",
    "AIToolsConfig",
    "CloudToolsConfig",
    "AutomationToolsConfig",
    "IntegrationToolsConfig",
    # MCP Support
    "MCPToolsAdapter",
    "MCPServerConfig",
    "get_mcp_adapter",
    "list_mcp_presets",
]
