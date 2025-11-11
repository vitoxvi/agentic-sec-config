"""Policy Interpreter Agent MCP Server: Expose policy interpreter agent as MCP server."""

from src.core.agent_mcp_server import create_agent_mcp_server
from src.mcp_servers.policy_interpreter_agent.policy_interpreter_service import (
    create_policy_interpreter_agent,
)

# Create MCP server wrapping the policy interpreter agent
mcp = create_agent_mcp_server(
    agent_name="Policy Interpreter Agent",
    agent_factory=create_policy_interpreter_agent,
    tool_name="interpret_policy",
    tool_description="""
    Translate natural language policy from policy.txt into technical access_config.yaml format.
    Reads the policy file, translates it, and writes the result to access_config.yaml.
    Returns AccessConfig object as structured output.
    """,
)


def main():
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
