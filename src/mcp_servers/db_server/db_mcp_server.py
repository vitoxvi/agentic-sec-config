"""MCP DB Server: Expose database query functions as MCP tools."""

from mcp.server.fastmcp import FastMCP

from src.mcp_servers.db_server.db_service import get_privileges, list_tables, who_can

# Create FastMCP server instance
mcp = FastMCP("Database Server")


@mcp.tool()
def db_list_tables() -> list[str]:
    """List all tables in the database.

    Returns:
        List of table names (excluding SQLite internal tables)
    """
    return list_tables()


@mcp.tool()
def db_get_privileges(username: str) -> dict[str, list[str]]:
    """Get user's table permissions.

    Args:
        username: Username to query

    Returns:
        Dictionary mapping table names to lists of allowed actions
    """
    return get_privileges(username)


@mcp.tool()
def db_who_can(table_name: str, action: str) -> list[str]:
    """Get list of users who can perform action on table.

    Args:
        table_name: Table name
        action: Action (SELECT, INSERT, UPDATE, DELETE)

    Returns:
        List of usernames with the specified permission
    """
    return who_can(table_name, action)


def main():
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
