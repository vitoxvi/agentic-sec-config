"""CLI interface for MCP DB Server."""

import typer
from rich.console import Console
from rich.table import Table

from src.mcp_servers.db_server import get_privileges, list_tables, who_can

app = typer.Typer(help="MCP DB Server CLI")
console = Console()


@app.command()
def list() -> None:
    """List all tables in the database."""
    try:
        tables = list_tables()
        if not tables:
            console.print("[yellow]No tables found[/yellow]")
            return

        table = Table(title="Database Tables")
        table.add_column("Table Name", style="cyan")

        for table_name in tables:
            table.add_row(table_name)

        console.print(table)
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def privileges(username: str = typer.Argument(..., help="Username to query")) -> None:
    """Show privileges for a user."""
    try:
        user_privileges = get_privileges(username)
        if not user_privileges:
            console.print(f"[yellow]No privileges found for user: {username}[/yellow]")
            return

        table = Table(title=f"Privileges for {username}")
        table.add_column("Table", style="cyan")
        table.add_column("Actions", style="green")

        for table_name, actions in sorted(user_privileges.items()):
            table.add_row(table_name, ", ".join(actions))

        console.print(table)
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("who-can")
def who_can_command(
    table_name: str = typer.Argument(..., help="Table name"),
    action: str = typer.Argument(..., help="Action (SELECT, INSERT, UPDATE, DELETE)"),
) -> None:
    """Show users who can perform action on table."""
    try:
        users = who_can(table_name, action)
        if not users:
            console.print(
                f"[yellow]No users found with {action} permission on {table_name}[/yellow]"
            )
            return

        table = Table(title=f"Users with {action} permission on {table_name}")
        table.add_column("Username", style="cyan")

        for user in users:
            table.add_row(user)

        console.print(table)
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
