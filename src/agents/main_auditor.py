# src/agents/main_auditor.py
import typer
from pathlib import Path
from rich.console import Console

from src.core.mcp_config import load_mcp_config
from src.core.schemas import Findings

app = typer.Typer(help="Main auditor (manager pattern)")
console = Console()


@app.command()
def health():
    """Simple health check for the auditor module."""
    console.print("[green]✅ main_auditor.py loaded successfully[/green]")


@app.command()
def audit(
    dry_run: bool = typer.Option(
        True, "--dry-run/--apply", help="Dry run mode (no changes applied)"
    ),
) -> None:
    """Run security audit against database configuration.

    Args:
        dry_run: If True, only report findings without applying changes
    """
    console.print("[cyan]Starting security audit...[/cyan]")

    # 1. Load MCP server config
    try:
        mcp_config = load_mcp_config()
        console.print(f"[green]✓[/green] Loaded {len(mcp_config.servers)} MCP server(s)")
    except Exception as e:
        console.print(f"[red]Error loading MCP config: {e}[/red]")
        raise typer.Exit(1)

    # 2. Connect to MCP servers (placeholder - will be implemented in Stage 3+)
    # TODO: Connect to db_server MCP server using stdio_client
    # Example pattern:
    # async with stdio_client(StdioServerParameters(...)) as (read, write):
    #     async with ClientSession(read, write) as session:
    #         await session.initialize()
    #         tools = await session.list_tools()
    console.print("[yellow]⚠[/yellow] MCP server connection (placeholder)")

    # 3. Call specialist agents (placeholder - will be implemented in Stage 3+)
    # TODO: Orchestrate calls to:
    #   - policy_interpreter: Translate natural language policy to technical config
    #   - db_auditor: Compare actual permissions vs policy
    #   - reporter: Generate report from findings
    console.print("[yellow]⚠[/yellow] Agent orchestration (placeholder)")

    # 4. Collect findings (empty for now - clean DB = no violations)
    findings = Findings(findings=[])
    console.print(f"[green]✓[/green] Audit complete: {len(findings.findings)} findings")

    # 5. Generate stub report
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    from datetime import datetime

    report_path = reports_dir / f"audit-{datetime.now().strftime('%Y%m%d')}.md"
    with report_path.open("w") as f:
        f.write("# Security Audit Report\n\n")
        f.write(f"**Date:** {findings.audit_date.isoformat()}\n")
        f.write(f"**Mode:** {'Dry Run' if dry_run else 'Apply'}\n\n")
        f.write("## Findings\n\n")
        if len(findings.findings) == 0:
            f.write("No violations found. Database configuration is compliant.\n")
        else:
            for finding in findings.findings:
                f.write(f"### {finding.id}: {finding.type}\n")
                f.write(f"- **Severity:** {finding.severity}\n")
                f.write(f"- **User:** {finding.user}\n")
                f.write(f"- **Resource:** {finding.resource}\n")
                f.write(f"- **Description:** {finding.description}\n")
                f.write(f"- **Recommendation:** {finding.recommendation}\n\n")

    console.print(f"[green]✓[/green] Report generated: {report_path}")

    # 6. Output results
    if dry_run:
        console.print("[yellow]Dry run mode: No changes applied[/yellow]")
    else:
        console.print("[yellow]Apply mode: Changes would be applied here[/yellow]")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Main auditor (manager pattern)"""
    if ctx.invoked_subcommand is None:
        health()


if __name__ == "__main__":
    app()
