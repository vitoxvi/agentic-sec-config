# src/main.py
import typer
from rich.console import Console

app = typer.Typer(help="Agentic Security Audit – entrypoint")
console = Console()

@app.command()
def health():
    """Quick system health check."""
    console.print("[green]✅ main.py is reachable and CLI works[/green]")

if __name__ == "__main__":
    app()
