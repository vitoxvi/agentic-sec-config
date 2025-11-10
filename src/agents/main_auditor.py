# src/agents/main_auditor.py
import typer
from rich.console import Console

app = typer.Typer(help="Main auditor (manager pattern)")
console = Console()

@app.command()
def health():
    """Simple health check for the auditor module."""
    console.print("[green]✅ main_auditor.py loaded successfully[/green]")

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Main auditor (manager pattern)"""
    if ctx.invoked_subcommand is None:
        health()

if __name__ == "__main__":
    app()
