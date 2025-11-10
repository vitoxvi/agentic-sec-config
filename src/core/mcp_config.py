"""MCP Server Configuration: Load and manage MCP server definitions."""

from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, Field

MCP_CONFIG_PATH = Path("data/mcp_servers.yaml")


class ServerConfig(BaseModel):
    """Configuration for a single MCP server."""

    name: str = Field(..., description="Server display name")
    description: str = Field(..., description="Server description")
    command: List[str] = Field(..., description="Command to start the server")
    tools: List[str] = Field(
        default_factory=list, description="List of tool names exposed by this server"
    )


class MCPConfig(BaseModel):
    """Root model for MCP server configuration."""

    servers: Dict[str, ServerConfig] = Field(
        ..., description="Mapping of server IDs to configurations"
    )


def load_mcp_config(path: Path = MCP_CONFIG_PATH) -> MCPConfig:
    """Load and validate MCP server configuration from YAML.

    Args:
        path: Path to mcp_servers.yaml file

    Returns:
        Validated MCPConfig object

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML is invalid
        ValidationError: If config doesn't match schema
    """
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"MCP config file not found: {path}")

    with config_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        raise ValueError(f"MCP config file is empty: {path}")

    return MCPConfig(**data)


def get_server_info(config: MCPConfig, server_id: str) -> Optional[ServerConfig]:
    """Get server configuration by ID.

    Args:
        config: MCPConfig object
        server_id: Server identifier

    Returns:
        ServerConfig if found, None otherwise
    """
    return config.servers.get(server_id)


def list_servers(config: MCPConfig) -> List[tuple[str, ServerConfig]]:
    """List all configured servers.

    Args:
        config: MCPConfig object

    Returns:
        List of (server_id, ServerConfig) tuples
    """
    return list(config.servers.items())
