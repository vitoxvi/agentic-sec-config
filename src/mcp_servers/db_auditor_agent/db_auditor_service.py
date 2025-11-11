"""Database Auditor Agent Service: Core agent logic."""

from agents import Agent

from src.core.mcp_tools import DB_TOOLS, FS_TOOLS
from src.core.schemas import Findings


def create_db_auditor_agent() -> Agent:
    """Create the database auditor agent.

    Returns:
        Agent configured to audit database permissions
    """
    return Agent(
        name="Database Auditor",
        instructions="""
        You are a security auditor. Your task is to compare expected permissions
        (from access_config.yaml) with actual database permissions.

        Steps:
        1. Read access_config.yaml using fs_read_access_config tool to get expected permissions per team
        2. Read users.csv using fs_read_users_csv tool to map users to teams
        3. Parse the CSV to understand which users belong to which teams
        4. For each user:
           - Get their team from the CSV
           - Get expected permissions for that team from access_config.yaml
           - Query actual permissions using db_get_privileges(username) tool
           - Compare expected vs actual and identify violations:
             * Unauthorized access: user has permission not in policy (user has action on table that their team shouldn't have)
             * Missing permission: user missing required permission (user's team should have action on table but user doesn't)
        5. Generate Findings with stable IDs using format: find-{user}-{resource}-{action}-{type}
           where type is either "unauthorized" or "missing"
        6. Assign severity based on:
           - CRITICAL: DELETE permission on sensitive tables (accounts, transactions)
           - HIGH: Unauthorized access to sensitive tables (accounts, transactions) with any action
           - MEDIUM: Missing required permissions
           - LOW: Extra permissions on non-sensitive tables (customers, orders, stock, procurement)
        7. For each finding, provide:
           - id: stable ID in format find-{user}-{resource}-{action}-{type}
           - severity: CRITICAL, HIGH, MEDIUM, or LOW
           - type: "unauthorized_access" or "missing_permission"
           - user: username
           - resource: table name
           - action: action name (SELECT, INSERT, UPDATE, DELETE)
           - description: clear explanation of the violation
           - recommendation: suggested fix
           - affected_resources: list of related resources (can be empty)

        Return Findings object with all violations found. If no violations, return Findings with empty findings list.

        Be thorough and check all users against their team's expected permissions.
        """,
        model="gpt-4o-mini",
        tools=DB_TOOLS + FS_TOOLS,
        output_type=Findings,
    )
