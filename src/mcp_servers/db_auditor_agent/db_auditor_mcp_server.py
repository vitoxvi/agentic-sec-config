"""Database Auditor Agent MCP Server: Expose db auditor agent as MCP server."""

from src.core.agent_mcp_server import create_agent_mcp_server
from src.mcp_servers.db_auditor_agent.db_auditor_service import create_db_auditor_agent

# Create MCP server wrapping the db auditor agent
mcp = create_agent_mcp_server(
    agent_name="Database Auditor Agent",
    agent_factory=create_db_auditor_agent,
    tool_name="audit_database",
    tool_description="""
    Audit database permissions by comparing expected permissions from access_config.yaml
    with actual permissions in the database. Reads the access config and users CSV, then
    queries actual permissions for each user and identifies any violations.

    Generates Findings with stable IDs and appropriate severity levels.
    Returns Findings object as structured output.
    """,
)


def main():
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
