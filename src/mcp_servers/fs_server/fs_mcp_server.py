"""MCP Filesystem Server: Expose filesystem operations as MCP tools."""

from mcp.server.fastmcp import FastMCP

from src.mcp_servers.fs_server.fs_service import (
    read_access_config,
    read_file,
    read_policy,
    read_users_csv,
    write_access_config,
    write_file,
    write_findings_json,
    write_report_markdown,
)

# Create FastMCP server instance
mcp = FastMCP("Filesystem Server")


@mcp.tool()
def fs_read_file(path: str) -> str:
    """Read file content.

    Args:
        path: Path to file to read

    Returns:
        File content as string
    """
    return read_file(path)


@mcp.tool()
def fs_write_file(path: str, content: str) -> str:
    """Write content to file.

    Args:
        path: Path to file to write
        content: Content to write

    Returns:
        Success message
    """
    write_file(path, content)
    return f"Successfully wrote to {path}"


@mcp.tool()
def fs_read_policy() -> str:
    """Read policy.txt file.

    Returns:
        Policy text content
    """
    return read_policy()


@mcp.tool()
def fs_write_access_config(config_yaml: str) -> str:
    """Write access_config.yaml file.

    Args:
        config_yaml: YAML content to write

    Returns:
        Success message
    """
    write_access_config(config_yaml)
    return "Successfully wrote access_config.yaml"


@mcp.tool()
def fs_read_access_config() -> str:
    """Read access_config.yaml file.

    Returns:
        Access config YAML content
    """
    return read_access_config()


@mcp.tool()
def fs_read_users_csv() -> str:
    """Read users.csv file.

    Returns:
        CSV content
    """
    return read_users_csv()


@mcp.tool()
def fs_write_findings_json(findings_json: str, path: str | None = None) -> str:
    """Write Findings JSON to file.

    Args:
        findings_json: JSON content to write
        path: Optional path for output file. Defaults to reports/findings.json

    Returns:
        Success message
    """
    write_findings_json(findings_json, path)
    output_path = path if path else "reports/findings.json"
    return f"Successfully wrote Findings JSON to {output_path}"


@mcp.tool()
def fs_write_report_markdown(markdown: str, path: str | None = None) -> str:
    """Write Markdown report to file.

    Args:
        markdown: Markdown content to write
        path: Optional path for output file. Defaults to reports/audit-YYYYMMDD.md

    Returns:
        Success message
    """
    write_report_markdown(markdown, path)
    if path:
        output_path = path
    else:
        from datetime import datetime

        output_path = f"reports/audit-{datetime.now().strftime('%Y%m%d')}.md"
    return f"Successfully wrote Markdown report to {output_path}"


def main():
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
