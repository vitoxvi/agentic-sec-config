"""Agent MCP Server Helper: Wrap Python Agent objects as MCP servers."""

from typing import Callable, Any

from agents import Agent, Runner
from mcp.server.fastmcp import FastMCP


def create_agent_mcp_server(
    agent_name: str,
    agent_factory: Callable[[], Agent],
    tool_name: str,
    tool_description: str,
) -> FastMCP:
    """Create an MCP server that wraps a Python Agent object.

    Args:
        agent_name: Name for the MCP server
        agent_factory: Function that creates the Agent instance
        tool_name: Name of the tool to expose
        tool_description: Description of what the tool does

    Returns:
        FastMCP server instance that wraps the agent
    """
    mcp = FastMCP(agent_name)

    # Create the tool function with proper name and docstring
    async def agent_tool(input: str) -> dict[str, Any]:
        """Execute the agent with the given input.

        Args:
            input: Input prompt for the agent

        Returns:
            Dictionary containing the agent's structured output or result
        """
        # Create the agent instance
        agent = agent_factory()

        # Run the agent
        result = await Runner.run(agent, input=input)

        # Extract structured output
        if hasattr(result, "final_output") and result.final_output is not None:
            # If it's a Pydantic model, convert to dict
            if hasattr(result.final_output, "model_dump"):
                return result.final_output.model_dump()
            # If it's already a dict
            if isinstance(result.final_output, dict):
                return result.final_output
            # Otherwise convert to dict
            return {"result": str(result.final_output)}

        # Fallback: return text output
        return {
            "result": str(result.final_output) if hasattr(result, "final_output") else "No output"
        }

    # Set the tool name and description
    agent_tool.__name__ = tool_name
    agent_tool.__doc__ = tool_description

    # Register the tool
    mcp.tool()(agent_tool)

    return mcp
