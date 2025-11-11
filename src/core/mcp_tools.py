"""MCP Tools Wrapper: Expose MCP server tools as function_tool for Agents SDK."""

import asyncio
from typing import Any

from agents import function_tool

from src.core.mcp_config import load_mcp_config
from src.core.mcp_setup import call_mcp_tool


def _run_async(coro):
    """Run async function, handling event loop properly."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, we need to use a different approach
            # For now, create a new thread with a new event loop
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop, create one
        return asyncio.run(coro)


# Filesystem server tools
@function_tool
def fs_read_file(path: str) -> str:
    """Read file content.

    Args:
        path: Path to file to read

    Returns:
        File content as string
    """
    return _run_async(call_mcp_tool("fs_server", "fs_read_file", {"path": path}))


@function_tool
def fs_write_file(path: str, content: str) -> str:
    """Write content to file.

    Args:
        path: Path to file to write
        content: Content to write

    Returns:
        Success message
    """
    return _run_async(
        call_mcp_tool("fs_server", "fs_write_file", {"path": path, "content": content})
    )


@function_tool
def fs_read_policy() -> str:
    """Read policy.txt file.

    Returns:
        Policy text content
    """
    return _run_async(call_mcp_tool("fs_server", "fs_read_policy", {}))


@function_tool
def fs_write_access_config(config_yaml: str) -> str:
    """Write access_config.yaml file.

    Args:
        config_yaml: YAML content to write

    Returns:
        Success message
    """
    return _run_async(
        call_mcp_tool("fs_server", "fs_write_access_config", {"config_yaml": config_yaml})
    )


@function_tool
def fs_read_access_config() -> str:
    """Read access_config.yaml file.

    Returns:
        Access config YAML content
    """
    return _run_async(call_mcp_tool("fs_server", "fs_read_access_config", {}))


@function_tool
def fs_read_users_csv() -> str:
    """Read users.csv file.

    Returns:
        CSV content
    """
    return _run_async(call_mcp_tool("fs_server", "fs_read_users_csv", {}))


@function_tool
def fs_write_findings_json(findings_json: str, path: str | None = None) -> str:
    """Write Findings JSON to file.

    Args:
        findings_json: JSON content to write
        path: Optional path for output file. Defaults to reports/findings.json

    Returns:
        Success message
    """
    args = {"findings_json": findings_json}
    if path:
        args["path"] = path
    return _run_async(call_mcp_tool("fs_server", "fs_write_findings_json", args))


@function_tool
def fs_write_report_markdown(markdown: str, path: str | None = None) -> str:
    """Write Markdown report to file.

    Args:
        markdown: Markdown content to write
        path: Optional path for output file. Defaults to reports/audit-YYYYMMDD.md

    Returns:
        Success message
    """
    args = {"markdown": markdown}
    if path:
        args["path"] = path
    return _run_async(call_mcp_tool("fs_server", "fs_write_report_markdown", args))


# Database server tools
@function_tool
def db_list_tables() -> list[str]:
    """List all tables in the database.

    Returns:
        List of table names
    """
    result = _run_async(call_mcp_tool("db_server", "db_list_tables", {}))
    if isinstance(result, list):
        return result
    return []


@function_tool
def db_get_privileges(username: str) -> dict[str, list[str]]:
    """Get user's table permissions.

    Args:
        username: Username to query

    Returns:
        Dictionary mapping table names to lists of allowed actions
    """
    result = _run_async(call_mcp_tool("db_server", "db_get_privileges", {"username": username}))
    if isinstance(result, dict):
        return result
    return {}


@function_tool
def db_who_can(table_name: str, action: str) -> list[str]:
    """Get list of users who can perform action on table.

    Args:
        table_name: Table name
        action: Action (SELECT, INSERT, UPDATE, DELETE)

    Returns:
        List of usernames with the specified permission
    """
    result = _run_async(
        call_mcp_tool("db_server", "db_who_can", {"table_name": table_name, "action": action})
    )
    if isinstance(result, list):
        return result
    return []


# Agent discovery and calling tools
@function_tool
def list_agent_servers() -> list[dict[str, Any]]:
    """List all agent MCP servers from mcp_servers.yaml configuration.

    Returns:
        List of dictionaries containing server_id, name, description, and tools for each agent server
    """
    config = load_mcp_config()

    # Filter for agent servers (servers with "_agent" in their ID)
    agent_servers = []
    for server_id, server_config in config.servers.items():
        if "_agent" in server_id:
            agent_servers.append(
                {
                    "server_id": server_id,
                    "name": server_config.name,
                    "description": server_config.description,
                    "tools": server_config.tools,
                }
            )

    return agent_servers


@function_tool
def get_agent_capabilities(agent_server_id: str) -> dict[str, Any]:
    """Get agent's available tools and capabilities via MCP.

    Args:
        agent_server_id: Server ID of the agent (e.g., "policy_interpreter_agent")

    Returns:
        Dictionary containing agent capabilities including available tools
    """
    config = load_mcp_config()
    server_info = config.servers.get(agent_server_id)

    if server_info is None:
        return {"error": f"Agent server '{agent_server_id}' not found"}

    # Try to connect and list tools via MCP
    try:
        # Use call_mcp_tool to get tool list (we'd need a list_tools MCP call)
        # For now, return config-based info
        return {
            "server_id": agent_server_id,
            "name": server_info.name,
            "description": server_info.description,
            "tools": server_info.tools,
        }
    except Exception as e:
        return {
            "server_id": agent_server_id,
            "name": server_info.name,
            "description": server_info.description,
            "tools": server_info.tools,
            "error": f"Could not connect to agent: {e}",
        }


@function_tool
def call_agent_tool(agent_server_id: str, tool_name: str, input: str) -> dict[str, Any]:
    """Call an agent tool via MCP protocol.

    Args:
        agent_server_id: Server ID of the agent (e.g., "policy_interpreter_agent")
        tool_name: Name of the tool to call (e.g., "interpret_policy")
        input: Input prompt/arguments for the agent tool

    Returns:
        Dictionary containing the agent's response (structured output or result)
    """
    result = _run_async(call_mcp_tool(agent_server_id, tool_name, {"input": input}))

    # Ensure result is a dict
    if isinstance(result, dict):
        return result
    return {"result": str(result)}


# Tool lists for agents
FS_TOOLS = [
    fs_read_file,
    fs_write_file,
    fs_read_policy,
    fs_write_access_config,
    fs_read_access_config,
    fs_read_users_csv,
    fs_write_findings_json,
    fs_write_report_markdown,
]

DB_TOOLS = [
    db_list_tables,
    db_get_privileges,
    db_who_can,
]

# Agent discovery and calling tools
AGENT_TOOLS = [
    list_agent_servers,
    get_agent_capabilities,
    call_agent_tool,
]

ALL_TOOLS = FS_TOOLS + DB_TOOLS + AGENT_TOOLS
