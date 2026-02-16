"""
MCP (Model Context Protocol) Tools Adapter

Integration with MCP servers for accessing external tools.
Supports STDIO, SSE, and HTTP transports.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type
import asyncio
import os
import structlog

logger = structlog.get_logger()


class MCPTransportType(Enum):
    """MCP server transport types."""
    STDIO = "stdio"
    SSE = "sse"
    HTTP = "http"


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server connection."""

    name: str
    transport: MCPTransportType

    # STDIO transport
    command: Optional[str] = None
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)

    # SSE/HTTP transport
    url: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)

    # General settings
    timeout: int = 30
    retry_attempts: int = 3
    enabled: bool = True

    @classmethod
    def stdio(
        cls,
        name: str,
        command: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> "MCPServerConfig":
        """Create STDIO transport config."""
        return cls(
            name=name,
            transport=MCPTransportType.STDIO,
            command=command,
            args=args or [],
            env={**os.environ, **(env or {})},
            **kwargs
        )

    @classmethod
    def sse(
        cls,
        name: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> "MCPServerConfig":
        """Create SSE transport config."""
        return cls(
            name=name,
            transport=MCPTransportType.SSE,
            url=url,
            headers=headers or {},
            **kwargs
        )

    @classmethod
    def http(
        cls,
        name: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> "MCPServerConfig":
        """Create HTTP transport config."""
        return cls(
            name=name,
            transport=MCPTransportType.HTTP,
            url=url,
            headers=headers or {},
            **kwargs
        )


class MCPToolsAdapter:
    """
    Adapter for connecting to MCP servers and using their tools.

    This provides access to thousands of tools from MCP servers
    built by the community.
    """

    def __init__(self):
        self._servers: Dict[str, MCPServerConfig] = {}
        self._connected_servers: Dict[str, Any] = {}
        self._tools_cache: Dict[str, List[Any]] = {}

        # Register common MCP servers
        self._register_default_servers()

    def _register_default_servers(self):
        """Register common MCP server configurations."""

        # File system MCP
        self.register_server(MCPServerConfig.stdio(
            name="filesystem",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
        ))

        # GitHub MCP
        self.register_server(MCPServerConfig.stdio(
            name="github",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env={"GITHUB_TOKEN": os.getenv("GITHUB_TOKEN", "")},
        ))

        # PostgreSQL MCP
        self.register_server(MCPServerConfig.stdio(
            name="postgres",
            command="uvx",
            args=["mcp-postgres"],
            env={"DATABASE_URL": os.getenv("DATABASE_URL", "")},
        ))

        # Slack MCP
        self.register_server(MCPServerConfig.stdio(
            name="slack",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-slack"],
            env={
                "SLACK_BOT_TOKEN": os.getenv("SLACK_BOT_TOKEN", ""),
                "SLACK_TEAM_ID": os.getenv("SLACK_TEAM_ID", ""),
            },
        ))

        # Brave Search MCP
        self.register_server(MCPServerConfig.stdio(
            name="brave-search",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-brave-search"],
            env={"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY", "")},
        ))

        # Google Maps MCP
        self.register_server(MCPServerConfig.stdio(
            name="google-maps",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-google-maps"],
            env={"GOOGLE_MAPS_API_KEY": os.getenv("GOOGLE_MAPS_API_KEY", "")},
        ))

        # Memory MCP
        self.register_server(MCPServerConfig.stdio(
            name="memory",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-memory"],
        ))

        # Fetch MCP
        self.register_server(MCPServerConfig.stdio(
            name="fetch",
            command="uvx",
            args=["mcp-fetch"],
        ))

        # Puppeteer MCP
        self.register_server(MCPServerConfig.stdio(
            name="puppeteer",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-puppeteer"],
        ))

        # Sequential Thinking MCP
        self.register_server(MCPServerConfig.stdio(
            name="sequential-thinking",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-sequential-thinking"],
        ))

        logger.info("mcp_default_servers_registered", count=len(self._servers))

    def register_server(self, config: MCPServerConfig):
        """Register an MCP server configuration."""
        self._servers[config.name] = config
        logger.debug("mcp_server_registered", name=config.name, transport=config.transport.value)

    def get_server_config(self, name: str) -> Optional[MCPServerConfig]:
        """Get server configuration by name."""
        return self._servers.get(name)

    def list_servers(self) -> List[Dict[str, Any]]:
        """List all registered MCP servers."""
        return [
            {
                "name": config.name,
                "transport": config.transport.value,
                "enabled": config.enabled,
                "has_url": bool(config.url),
                "has_command": bool(config.command),
            }
            for config in self._servers.values()
        ]

    def get_available_servers(self) -> List[str]:
        """Get names of servers that can be connected to."""
        available = []
        for name, config in self._servers.items():
            if not config.enabled:
                continue

            if config.transport == MCPTransportType.STDIO:
                # Check if required env vars are set
                if config.command:
                    available.append(name)
            elif config.transport in (MCPTransportType.SSE, MCPTransportType.HTTP):
                if config.url:
                    available.append(name)

        return available

    async def connect_to_server(self, name: str) -> bool:
        """
        Connect to an MCP server.

        Args:
            name: Server name

        Returns:
            True if connected successfully
        """
        config = self._servers.get(name)
        if not config:
            logger.error("mcp_server_not_found", name=name)
            return False

        if name in self._connected_servers:
            logger.debug("mcp_already_connected", name=name)
            return True

        try:
            if config.transport == MCPTransportType.STDIO:
                # Use MCPServerAdapter from crewai_tools
                from mcp import StdioServerParameters
                from crewai_tools import MCPServerAdapter

                server_params = StdioServerParameters(
                    command=config.command,
                    args=config.args,
                    env=config.env,
                )

                adapter = MCPServerAdapter(server_params)
                self._connected_servers[name] = adapter
                self._tools_cache[name] = adapter.tools

                logger.info("mcp_stdio_connected", name=name, tools_count=len(adapter.tools))
                return True

            elif config.transport == MCPTransportType.SSE:
                from crewai_tools import MCPServerAdapter

                server_params = {"url": config.url}
                if config.headers:
                    server_params["headers"] = config.headers

                adapter = MCPServerAdapter(server_params)
                self._connected_servers[name] = adapter
                self._tools_cache[name] = adapter.tools

                logger.info("mcp_sse_connected", name=name, tools_count=len(adapter.tools))
                return True

            elif config.transport == MCPTransportType.HTTP:
                # HTTP transport support
                from crewai_tools import MCPServerAdapter

                server_params = {"url": config.url}
                if config.headers:
                    server_params["headers"] = config.headers

                adapter = MCPServerAdapter(server_params)
                self._connected_servers[name] = adapter
                self._tools_cache[name] = adapter.tools

                logger.info("mcp_http_connected", name=name, tools_count=len(adapter.tools))
                return True

        except ImportError as e:
            logger.error("mcp_import_error", name=name, error=str(e))
            return False
        except Exception as e:
            logger.error("mcp_connection_failed", name=name, error=str(e))
            return False

        return False

    async def disconnect_from_server(self, name: str) -> bool:
        """
        Disconnect from an MCP server.

        Args:
            name: Server name

        Returns:
            True if disconnected successfully
        """
        if name not in self._connected_servers:
            return True

        try:
            adapter = self._connected_servers[name]
            if hasattr(adapter, 'stop'):
                adapter.stop()

            del self._connected_servers[name]
            if name in self._tools_cache:
                del self._tools_cache[name]

            logger.info("mcp_disconnected", name=name)
            return True

        except Exception as e:
            logger.error("mcp_disconnect_failed", name=name, error=str(e))
            return False

    async def disconnect_all(self):
        """Disconnect from all MCP servers."""
        for name in list(self._connected_servers.keys()):
            await self.disconnect_from_server(name)

    def get_tools_from_server(self, name: str) -> List[Any]:
        """
        Get tools from a connected MCP server.

        Args:
            name: Server name

        Returns:
            List of CrewAI tools
        """
        if name not in self._connected_servers:
            logger.warning("mcp_server_not_connected", name=name)
            return []

        return self._tools_cache.get(name, [])

    def get_all_tools(self) -> List[Any]:
        """
        Get all tools from all connected MCP servers.

        Returns:
            Combined list of all tools
        """
        all_tools = []
        for name, tools in self._tools_cache.items():
            all_tools.extend(tools)
        return all_tools

    async def connect_to_multiple(self, names: List[str]) -> Dict[str, bool]:
        """
        Connect to multiple MCP servers.

        Args:
            names: List of server names

        Returns:
            Dict of server name to connection success
        """
        results = {}
        for name in names:
            results[name] = await self.connect_to_server(name)
        return results

    def get_server_tools_info(self, name: str) -> List[Dict[str, Any]]:
        """
        Get information about tools from a server.

        Args:
            name: Server name

        Returns:
            List of tool info dictionaries
        """
        tools = self.get_tools_from_server(name)
        return [
            {
                "name": tool.name if hasattr(tool, 'name') else str(tool),
                "description": tool.description if hasattr(tool, 'description') else "",
                "server": name,
            }
            for tool in tools
        ]


# Popular MCP server presets
MCP_SERVER_PRESETS = {
    "filesystem": {
        "description": "File system operations",
        "package": "@modelcontextprotocol/server-filesystem",
        "env_vars": [],
    },
    "github": {
        "description": "GitHub API operations",
        "package": "@modelcontextprotocol/server-github",
        "env_vars": ["GITHUB_TOKEN"],
    },
    "postgres": {
        "description": "PostgreSQL database operations",
        "package": "mcp-postgres",
        "env_vars": ["DATABASE_URL"],
    },
    "slack": {
        "description": "Slack messaging",
        "package": "@modelcontextprotocol/server-slack",
        "env_vars": ["SLACK_BOT_TOKEN", "SLACK_TEAM_ID"],
    },
    "brave-search": {
        "description": "Web search via Brave",
        "package": "@modelcontextprotocol/server-brave-search",
        "env_vars": ["BRAVE_API_KEY"],
    },
    "google-maps": {
        "description": "Google Maps operations",
        "package": "@modelcontextprotocol/server-google-maps",
        "env_vars": ["GOOGLE_MAPS_API_KEY"],
    },
    "memory": {
        "description": "Persistent memory for agents",
        "package": "@modelcontextprotocol/server-memory",
        "env_vars": [],
    },
    "fetch": {
        "description": "Web fetching capabilities",
        "package": "mcp-fetch",
        "env_vars": [],
    },
    "puppeteer": {
        "description": "Browser automation",
        "package": "@modelcontextprotocol/server-puppeteer",
        "env_vars": [],
    },
    "sequential-thinking": {
        "description": "Structured reasoning",
        "package": "@modelcontextprotocol/server-sequential-thinking",
        "env_vars": [],
    },
    "everart": {
        "description": "AI art generation",
        "package": "@modelcontextprotocol/server-everart",
        "env_vars": ["EVERART_API_KEY"],
    },
    "airtable": {
        "description": "Airtable database",
        "package": "@modelcontextprotocol/server-airtable",
        "env_vars": ["AIRTABLE_API_KEY", "AIRTABLE_BASE_ID"],
    },
    "stripe": {
        "description": "Stripe payments",
        "package": "@modelcontextprotocol/server-stripe",
        "env_vars": ["STRIPE_API_KEY"],
    },
    "discord": {
        "description": "Discord messaging",
        "package": "@modelcontextprotocol/server-discord",
        "env_vars": ["DISCORD_BOT_TOKEN"],
    },
    "sentry": {
        "description": "Sentry error tracking",
        "package": "@modelcontextprotocol/server-sentry",
        "env_vars": ["SENTRY_API_KEY"],
    },
}


def get_mcp_adapter() -> MCPToolsAdapter:
    """Get the global MCP adapter instance."""
    return MCPToolsAdapter()


def list_mcp_presets() -> Dict[str, Dict[str, Any]]:
    """List available MCP server presets."""
    return MCP_SERVER_PRESETS
