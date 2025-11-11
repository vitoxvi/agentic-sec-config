"""CLI for filesystem MCP server operations."""

import typer
from rich.console import Console

from src.mcp_servers.fs_server.fs_service import (
    read_access_config,
    read_policy,
    read_users_csv,
    write_access_config,
)

app = typer.Typer(help="Filesystem server CLI")
console = Console()


@app.command()
def read_policy_cmd():
    """Read policy.txt file."""
    try:
        content = read_policy()
        console.print("[green]Policy content:[/green]")
        console.print(content)
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")


@app.command()
def read_config():
    """Read access_config.yaml file."""
    try:
        content = read_access_config()
        console.print("[green]Access config content:[/green]")
        console.print(content)
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")


@app.command()
def read_users():
    """Read users.csv file."""
    try:
        content = read_users_csv()
        console.print("[green]Users CSV content:[/green]")
        console.print(content)
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")


@app.command()
def write_config(
    content: str = typer.Argument(..., help="YAML content to write"),
):
    """Write access_config.yaml file."""
    try:
        write_access_config(content)
        console.print("[green]Successfully wrote access_config.yaml[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    app()
