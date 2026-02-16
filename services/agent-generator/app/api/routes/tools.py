"""
Tool Management API Routes

Endpoints for discovering, configuring, and managing CrewAI tools.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.tools import (
    ToolRegistry,
    ToolCategory,
    get_tool_registry,
    list_available_tools,
    get_tools_by_category,
    MCPToolsAdapter,
    get_mcp_adapter,
    list_mcp_presets,
)

router = APIRouter(prefix="/tools", tags=["tools"])


# === Request/Response Models ===

class ToolInfo(BaseModel):
    """Information about a tool."""
    name: str
    category: str
    description: str
    available: bool
    missing_config: List[str]
    dependencies: List[str]


class ToolCategorySummary(BaseModel):
    """Summary of tools in a category."""
    category: str
    total_tools: int
    available_tools: int


class MCPServerInfo(BaseModel):
    """Information about an MCP server."""
    name: str
    transport: str
    enabled: bool
    connected: bool
    tools_count: int


class ConnectMCPServerRequest(BaseModel):
    """Request to connect to an MCP server."""
    server_name: str


class InstantiateToolRequest(BaseModel):
    """Request to instantiate a tool."""
    tool_name: str
    config: Dict[str, Any] = Field(default_factory=dict)


# === Tool Registry Endpoints ===

@router.get("/", response_model=Dict[str, Any])
async def list_tools():
    """
    List all available tools with their status.

    Returns categorized tools with availability information.
    """
    import os
    tools = list_available_tools(dict(os.environ))
    registry = get_tool_registry()

    return {
        "total_tools": len(tools),
        "available_tools": sum(1 for t in tools if t["available"]),
        "categories": registry.get_category_summary(),
        "tools": tools,
    }


@router.get("/categories", response_model=List[ToolCategorySummary])
async def list_categories():
    """
    List all tool categories with counts.
    """
    import os
    registry = get_tool_registry()
    env = dict(os.environ)

    summaries = []
    for category in ToolCategory:
        tools = registry.get_tools_by_category(category)
        available = sum(1 for t in tools if t.is_available(env))
        summaries.append(ToolCategorySummary(
            category=category.value,
            total_tools=len(tools),
            available_tools=available,
        ))

    return summaries


@router.get("/category/{category}", response_model=List[ToolInfo])
async def get_tools_in_category(category: str):
    """
    Get all tools in a specific category.

    Args:
        category: Category name (file_document, web_scraping, etc.)
    """
    import os
    tools = get_tools_by_category(category)
    env = dict(os.environ)

    return [
        ToolInfo(
            name=tool.name,
            category=tool.category.value,
            description=tool.description,
            available=tool.is_available(env),
            missing_config=tool.get_missing_config(env),
            dependencies=tool.dependencies,
        )
        for tool in tools
    ]


@router.get("/available", response_model=List[ToolInfo])
async def list_available():
    """
    List only tools that are available with current configuration.
    """
    import os
    registry = get_tool_registry()
    env = dict(os.environ)

    tools = registry.get_available_tools(env)

    return [
        ToolInfo(
            name=tool.name,
            category=tool.category.value,
            description=tool.description,
            available=True,
            missing_config=[],
            dependencies=tool.dependencies,
        )
        for tool in tools
    ]


@router.get("/unavailable", response_model=Dict[str, List[str]])
async def list_unavailable():
    """
    List tools that are unavailable due to missing configuration.

    Returns tool names with their missing environment variables.
    """
    import os
    registry = get_tool_registry()
    env = dict(os.environ)

    return registry.get_unavailable_tools(env)


@router.get("/{tool_name}", response_model=ToolInfo)
async def get_tool_info(tool_name: str):
    """
    Get detailed information about a specific tool.
    """
    import os
    registry = get_tool_registry()
    tool = registry.get_tool(tool_name)

    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    env = dict(os.environ)

    return ToolInfo(
        name=tool.name,
        category=tool.category.value,
        description=tool.description,
        available=tool.is_available(env),
        missing_config=tool.get_missing_config(env),
        dependencies=tool.dependencies,
    )


@router.post("/instantiate")
async def instantiate_tool(request: InstantiateToolRequest):
    """
    Instantiate a tool with the given configuration.

    Returns the tool instance information.
    """
    registry = get_tool_registry()

    try:
        tool = registry.instantiate_tool(request.tool_name, **request.config)
        return {
            "success": True,
            "tool_name": request.tool_name,
            "tool_type": type(tool).__name__,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ImportError as e:
        raise HTTPException(status_code=400, detail=f"Failed to import tool: {e}")


# === MCP Server Endpoints ===

@router.get("/mcp/servers", response_model=List[Dict[str, Any]])
async def list_mcp_servers():
    """
    List all registered MCP servers.
    """
    adapter = get_mcp_adapter()
    servers = adapter.list_servers()

    result = []
    for server in servers:
        connected = server["name"] in adapter._connected_servers
        tools_count = len(adapter._tools_cache.get(server["name"], []))
        result.append({
            **server,
            "connected": connected,
            "tools_count": tools_count,
        })

    return result


@router.get("/mcp/presets", response_model=Dict[str, Dict[str, Any]])
async def list_mcp_server_presets():
    """
    List available MCP server presets with configuration requirements.
    """
    return list_mcp_presets()


@router.get("/mcp/available")
async def list_available_mcp_servers():
    """
    List MCP servers that can be connected to with current configuration.
    """
    adapter = get_mcp_adapter()
    return {"servers": adapter.get_available_servers()}


@router.post("/mcp/connect")
async def connect_mcp_server(request: ConnectMCPServerRequest):
    """
    Connect to an MCP server.

    Args:
        request: Server connection request
    """
    adapter = get_mcp_adapter()

    success = await adapter.connect_to_server(request.server_name)

    if success:
        tools = adapter.get_tools_from_server(request.server_name)
        return {
            "success": True,
            "server_name": request.server_name,
            "tools_count": len(tools),
            "tools": [t.name if hasattr(t, 'name') else str(t) for t in tools],
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to connect to MCP server '{request.server_name}'"
        )


@router.post("/mcp/disconnect")
async def disconnect_mcp_server(request: ConnectMCPServerRequest):
    """
    Disconnect from an MCP server.

    Args:
        request: Server disconnection request
    """
    adapter = get_mcp_adapter()

    success = await adapter.disconnect_from_server(request.server_name)

    return {"success": success, "server_name": request.server_name}


@router.get("/mcp/{server_name}/tools")
async def get_mcp_server_tools(server_name: str):
    """
    Get tools from a connected MCP server.
    """
    adapter = get_mcp_adapter()

    if server_name not in adapter._connected_servers:
        raise HTTPException(
            status_code=400,
            detail=f"Not connected to MCP server '{server_name}'"
        )

    tools_info = adapter.get_server_tools_info(server_name)
    return {"server_name": server_name, "tools": tools_info}


@router.post("/mcp/connect-all")
async def connect_all_mcp_servers():
    """
    Connect to all available MCP servers.
    """
    adapter = get_mcp_adapter()
    available = adapter.get_available_servers()

    results = await adapter.connect_to_multiple(available)

    return {
        "total": len(available),
        "results": results,
        "successful": sum(1 for v in results.values() if v),
        "failed": sum(1 for v in results.values() if not v),
    }
