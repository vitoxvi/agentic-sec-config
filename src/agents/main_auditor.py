"""Main Auditor Agent: Orchestrates policy interpretation and database auditing via MCP."""

import asyncio

import typer
from rich.console import Console

from agents import Agent, Runner

from src.core.mcp_tools import AGENT_TOOLS, FS_TOOLS
from src.core.schemas import Findings

app = typer.Typer(help="Main auditor (manager pattern)")
console = Console()


def create_manager_agent() -> Agent:
    """Create the main auditor manager agent.

    The manager agent discovers and calls specialist agents via MCP protocol.
    It decides which agents to call and in what order based on the task prompt.

    Returns:
        Agent configured to orchestrate the audit workflow via MCP
    """
    return Agent(
        name="Main Auditor",
        instructions="""
        You are the main security auditor orchestrating the audit workflow.

        Your role is to:
        1. Discover available specialist agents using list_agent_servers()
        2. Decide which agents to call based on the task
        3. Call specialist agents via MCP using call_agent_tool()
        4. Coordinate the workflow and generate reports

        Available specialist agents (discover via list_agent_servers):
        - policy_interpreter_agent: Translates policy.txt to access_config.yaml
        - db_auditor_agent: Audits database permissions and generates Findings

        Typical workflow:
        1. Call policy_interpreter_agent with interpret_policy tool to translate policy
        2. Call db_auditor_agent with audit_database tool to audit permissions
        3. Generate reports using fs_server tools:
           - Write Findings.json using fs_write_findings_json
           - Write Markdown report using fs_write_report_markdown

        You decide the order and which agents are needed based on the task.
        Use call_agent_tool(agent_server_id, tool_name, input) to invoke specialist agents.
        The input parameter should be a clear prompt describing what the agent should do.

        Coordinate the entire audit process and ensure all steps complete successfully.
        If any step fails, report the error clearly.
        """,
        model="gpt-4o-mini",
        tools=AGENT_TOOLS + FS_TOOLS,
    )


async def run_audit(task_prompt: str | None = None) -> Findings | None:
    """Run the audit workflow using the manager agent.

    The manager agent decides which specialist agents to call via MCP based on the task.

    Args:
        task_prompt: Optional task description. If None, uses default audit prompt.

    Returns:
        Findings object if audit completes successfully, None otherwise
    """
    if task_prompt is None:
        task_prompt = """
        Perform a complete security audit:
        1. Translate the natural language policy from policy.txt into technical access_config.yaml format
        2. Audit the database permissions by comparing expected permissions from access_config.yaml
           with actual permissions in the database
        3. Generate Findings.json and a Markdown report summarizing all violations found

        Use the specialist agents available via MCP to complete this task.
        """

    console.print("[cyan]Starting security audit workflow...[/cyan]")
    console.print("[cyan]Manager agent will orchestrate specialist agents via MCP...[/cyan]")

    # Create manager agent
    manager = create_manager_agent()

    # Run manager agent - it decides which specialists to call
    try:
        await Runner.run(manager, input=task_prompt)

        console.print("[green]✓[/green] Audit workflow completed")

        # Manager handles reporting via fs_server tools
        # Return None as manager coordinates the workflow
        return None

    except Exception as e:
        console.print(f"[red]Error during audit: {e}[/red]")
        raise


async def generate_reports(findings: Findings) -> None:
    """Generate Findings.json and Markdown report.

    Args:
        findings: Findings object to report
    """
    from src.mcp_servers.fs_server.fs_service import write_findings_json, write_report_markdown

    # Generate JSON
    findings_json = findings.model_dump_json(indent=2)
    write_findings_json(findings_json)

    # Generate Markdown
    markdown = generate_markdown_report(findings)
    write_report_markdown(markdown)


def generate_markdown_report(findings: Findings) -> str:
    """Generate Markdown report from findings.

    Args:
        findings: Findings object

    Returns:
        Markdown report content
    """
    lines = [
        "# Security Audit Report",
        "",
        f"**Date:** {findings.audit_date.isoformat()}",
        f"**Total Findings:** {len(findings.findings)}",
        "",
    ]

    # Severity breakdown
    severity_counts = {}
    for finding in findings.findings:
        severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1

    if severity_counts:
        lines.append("**Severity Breakdown:**")
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = severity_counts.get(severity, 0)
            if count > 0:
                lines.append(f"- {severity}: {count}")
        lines.append("")

    # Findings
    lines.append("## Findings")
    lines.append("")

    if len(findings.findings) == 0:
        lines.append("No violations found. Database configuration is compliant.")
    else:
        for finding in findings.findings:
            lines.append(f"### {finding.id}: {finding.type}")
            lines.append(f"- **Severity:** {finding.severity}")
            lines.append(f"- **User:** {finding.user}")
            lines.append(f"- **Resource:** {finding.resource}")
            lines.append(f"- **Action:** {finding.action}")
            lines.append(f"- **Description:** {finding.description}")
            lines.append(f"- **Recommendation:** {finding.recommendation}")
            if finding.affected_resources:
                lines.append(f"- **Affected Resources:** {', '.join(finding.affected_resources)}")
            lines.append("")

    return "\n".join(lines)


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

    The manager agent orchestrates specialist agents via MCP to:
    - Translate policy.txt to access_config.yaml
    - Audit database permissions
    - Generate Findings.json and Markdown report

    Args:
        dry_run: If True, only report findings without applying changes
    """
    try:
        task_prompt = """
        Perform a complete security audit:
        1. Translate the natural language policy from policy.txt into technical access_config.yaml format
        2. Audit the database permissions by comparing expected permissions from access_config.yaml
           with actual permissions in the database
        3. Generate Findings.json and a Markdown report summarizing all violations found

        Use the specialist agents available via MCP to complete this task.
        """

        asyncio.run(run_audit(task_prompt=task_prompt))

        console.print("\n[bold]Audit Summary:[/bold]")
        console.print("  Audit workflow completed via manager agent")
        console.print("  Check reports/ directory for Findings.json and Markdown report")

        if dry_run:
            console.print("\n[yellow]Dry run mode: No changes applied[/yellow]")
        else:
            console.print("\n[yellow]Apply mode: Changes would be applied here[/yellow]")

    except Exception as e:
        console.print(f"[red]Audit failed: {e}[/red]")
        raise typer.Exit(1)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Main auditor (manager pattern)"""
    if ctx.invoked_subcommand is None:
        health()


if __name__ == "__main__":
    app()
