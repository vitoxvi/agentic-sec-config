"""MCP Server Setup: Configure MCP servers for use with OpenAI Agents SDK."""

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, Any

from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp import ClientSession

from src.core.mcp_config import load_mcp_config, get_server_info


@asynccontextmanager
async def create_mcp_server_session(server_id: str) -> AsyncIterator[ClientSession]:
    """Create an MCP server session using stdio_client.

    Args:
        server_id: Server ID from mcp_servers.yaml

    Yields:
        ClientSession for the MCP server
    """
    config = load_mcp_config()
    server_info = get_server_info(config, server_id)

    if server_info is None:
        raise ValueError(f"Server '{server_id}' not found in mcp_servers.yaml")

    # Create stdio server parameters
    server_params = StdioServerParameters(
        command=server_info.command[0],
        args=server_info.command[1:] if len(server_info.command) > 1 else [],
        env={"UV_INDEX": os.environ.get("UV_INDEX", "")},
    )

    # Create stdio client connection
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def call_mcp_tool(server_id: str, tool_name: str, arguments: dict[str, Any]) -> Any:
    """Call an MCP tool on a server.

    Args:
        server_id: Server ID from mcp_servers.yaml
        tool_name: Name of the tool to call
        arguments: Tool arguments

    Returns:
        Tool result
    """
    async with create_mcp_server_session(server_id) as session:
        result = await session.call_tool(tool_name, arguments)

        # Extract structured content if available, otherwise use text content
        if result.structuredContent:
            return result.structuredContent

        # Extract text from content blocks
        if result.content:
            text_parts = []
            for content_block in result.content:
                if hasattr(content_block, "text"):
                    text_parts.append(content_block.text)
            if text_parts:
                return "\n".join(text_parts)

        return str(result)
