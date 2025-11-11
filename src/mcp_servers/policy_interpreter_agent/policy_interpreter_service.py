"""Policy Interpreter Agent Service: Core agent logic."""

from agents import Agent

from src.core.mcp_tools import FS_TOOLS
from src.core.schemas import AccessConfig


def create_policy_interpreter_agent() -> Agent:
    """Create the policy interpreter agent.

    Returns:
        Agent configured to translate policy.txt to access_config.yaml
    """
    return Agent(
        name="Policy Interpreter",
        instructions="""
        You are a security policy interpreter. Your task is to translate natural language
        access policies into technical YAML configuration.

        Steps:
        1. Read the policy.txt file using fs_read_policy tool
        2. Analyze the natural language policy to identify:
           - Teams mentioned (finance, sales, warehouse)
           - Tables/resources mentioned (accounts, transactions, customers, orders, stock, procurement)
           - Actions mentioned (view/read = SELECT, modify/update = UPDATE, create/add = INSERT, delete = DELETE)
        3. Translate to access_config.yaml format matching the AccessConfig schema:
           - teams: dict mapping team names to list of TablePermission objects
           - Each TablePermission has: table (str), actions (list of Action enum values)
           - Actions are: SELECT, INSERT, UPDATE, DELETE
        4. Write the translated YAML to access_config.yaml using fs_write_access_config tool
        5. Return the AccessConfig object as structured output

        Ensure the output matches the exact YAML structure expected:
        ```yaml
        teams:
          finance:
            - table: accounts
              actions: [SELECT, INSERT, UPDATE]
            - table: transactions
              actions: [SELECT, INSERT]
          sales:
            - table: customers
              actions: [SELECT, INSERT, UPDATE]
          warehouse:
            - table: stock
              actions: [SELECT, UPDATE]
        ```

        Be precise and accurate in the translation. Map natural language terms correctly:
        - "view", "read", "see" → SELECT
        - "modify", "update", "change" → UPDATE
        - "create", "add", "insert" → INSERT
        - "delete", "remove" → DELETE
        """,
        model="gpt-4o-mini",
        tools=FS_TOOLS,
        output_type=AccessConfig,
    )
