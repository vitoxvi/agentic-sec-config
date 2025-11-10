import typer
from rich.console import Console

app = typer.Typer(help="Agentic Security Audit – root entrypoint")
console = Console()


@app.command()
def health():
    """Quick system health check."""
    console.print("[green]✅ main.py is reachable and CLI works[/green]")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Agentic Security Audit – root entrypoint"""
    if ctx.invoked_subcommand is None:
        health()


if __name__ == "__main__":
    app()
