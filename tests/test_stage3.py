"""Tests for Stage 3: Auditor MVP with Agentic LLM Agents."""

import os
import pytest
from pathlib import Path

from src.core.error_injection import (
    inject_unauthorized_access,
    inject_missing_permission,
    reset_permissions,
)
from src.core.schemas import AccessConfig, Findings
from src.core.seed import seed
from src.agents.policy_interpreter import interpret_policy, create_policy_interpreter_agent
from src.agents.db_auditor import audit_database, create_db_auditor_agent
from src.agents.main_auditor import run_audit_workflow


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Create temporary database for testing."""
    db_path = tmp_path / "audit.db"
    monkeypatch.setattr("src.core.seed.DB_PATH", db_path)
    monkeypatch.setattr("src.mcp_servers.db_server.db_service.DB_PATH", db_path)
    monkeypatch.setattr("src.core.error_injection.DB_PATH", db_path)

    # Seed database
    seed(reset=True)

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def temp_policy_files(tmp_path, monkeypatch):
    """Create temporary policy files."""
    policy_dir = tmp_path / "policy"
    policy_dir.mkdir(parents=True)

    policy_file = policy_dir / "policy.txt"
    policy_file.write_text(
        "Employees of the finance team have access to view and modify account balances, "
        "view transaction history, and view stock levels.\n\n"
        "Employees working in sales have access to manage customer information and process orders.\n\n"
        "Employees in the warehouse team have access to view and update stock levels, "
        "and manage procurement orders."
    )

    config_file = policy_dir / "access_config.yaml"
    config_file.write_text(
        """teams:
  finance:
    - table: accounts
      actions: [SELECT, INSERT, UPDATE]
    - table: transactions
      actions: [SELECT, INSERT]
    - table: stock
      actions: [SELECT]
  sales:
    - table: customers
      actions: [SELECT, INSERT, UPDATE]
    - table: orders
      actions: [SELECT, INSERT, UPDATE]
  warehouse:
    - table: stock
      actions: [SELECT, UPDATE]
    - table: procurement
      actions: [SELECT, INSERT, UPDATE]
"""
    )

    users_dir = tmp_path / "users"
    users_dir.mkdir(parents=True)
    users_file = users_dir / "users.csv"
    users_file.write_text("username,team,role\nalice,finance,analyst\nbob,sales,representative\n")

    # Patch paths
    monkeypatch.setattr("src.mcp_servers.fs_server.fs_service.POLICY_PATH", policy_file)
    monkeypatch.setattr("src.mcp_servers.fs_server.fs_service.ACCESS_CONFIG_PATH", config_file)
    monkeypatch.setattr("src.mcp_servers.fs_server.fs_service.USERS_CSV_PATH", users_file)
    monkeypatch.setattr(
        "src.core.policy_io.Path",
        lambda x: (
            policy_file
            if "policy.txt" in str(x)
            else config_file if "access_config.yaml" in str(x) else Path(x)
        ),
    )

    return policy_file, config_file, users_file


class TestErrorInjection:
    """Test error injection functions."""

    def test_inject_unauthorized_access(self, temp_db):
        """Test injecting unauthorized access."""
        # Inject DELETE permission for alice on accounts (should violate policy)
        inject_unauthorized_access("alice", "accounts", "DELETE")

        # Verify permission was added
        from src.mcp_servers.db_server.db_service import get_privileges

        privileges = get_privileges("alice")
        assert "DELETE" in privileges.get("accounts", [])

    def test_inject_missing_permission(self, temp_db):
        """Test injecting missing permission."""
        # Revoke SELECT permission for alice on accounts
        inject_missing_permission("alice", "accounts", "SELECT")

        # Verify permission was revoked
        from src.mcp_servers.db_server.db_service import get_privileges

        privileges = get_privileges("alice")
        assert "SELECT" not in privileges.get("accounts", [])

    def test_reset_permissions(self, temp_db):
        """Test resetting permissions to clean state."""
        # Inject an error
        inject_unauthorized_access("alice", "accounts", "DELETE")

        # Reset
        reset_permissions()

        # Verify DELETE is gone
        from src.mcp_servers.db_server.db_service import get_privileges

        privileges = get_privileges("alice")
        assert "DELETE" not in privileges.get("accounts", [])


class TestPolicyInterpreterAgent:
    """Test policy interpreter agent."""

    @pytest.mark.skipif(
        "OPENAI_API_KEY" not in os.environ,
        reason="LLM tests require OPENAI_API_KEY environment variable",
    )
    @pytest.mark.asyncio
    async def test_policy_interpreter_translates_policy(self, temp_policy_files):
        """Test that policy interpreter translates policy.txt to access_config.yaml."""
        # This test requires OPENAI_API_KEY and will make actual LLM calls
        config = await interpret_policy()

        assert isinstance(config, AccessConfig)
        assert "finance" in config.teams
        assert "sales" in config.teams
        assert "warehouse" in config.teams

    def test_policy_interpreter_agent_creation(self):
        """Test that policy interpreter agent can be created."""
        agent = create_policy_interpreter_agent()
        assert agent.name == "Policy Interpreter"
        assert agent.model == "gpt-4o-mini"
        assert agent.output_type == AccessConfig


class TestDBAuditorAgent:
    """Test database auditor agent."""

    @pytest.mark.skipif(
        "OPENAI_API_KEY" not in os.environ,
        reason="LLM tests require OPENAI_API_KEY environment variable",
    )
    @pytest.mark.asyncio
    async def test_db_auditor_detects_violations(self, temp_db, temp_policy_files):
        """Test that db auditor detects violations."""
        # Inject an unauthorized access
        inject_unauthorized_access("alice", "accounts", "DELETE")

        # Run audit
        findings = await audit_database()

        assert isinstance(findings, Findings)
        # Should find at least one violation
        assert len(findings.findings) > 0

    @pytest.mark.skipif(
        "OPENAI_API_KEY" not in os.environ,
        reason="LLM tests require OPENAI_API_KEY environment variable",
    )
    @pytest.mark.asyncio
    async def test_audit_clean_db_produces_no_findings(self, temp_db, temp_policy_files):
        """Test that audit produces no findings on clean DB."""
        # Ensure clean state
        reset_permissions()

        # Run audit
        findings = await audit_database()

        assert isinstance(findings, Findings)
        # Clean DB should have no violations
        assert len(findings.findings) == 0

    def test_db_auditor_agent_creation(self):
        """Test that db auditor agent can be created."""
        agent = create_db_auditor_agent()
        assert agent.name == "Database Auditor"
        assert agent.model == "gpt-4o-mini"
        assert agent.output_type == Findings


class TestMainAuditor:
    """Test main auditor orchestration."""

    @pytest.mark.skipif(
        "OPENAI_API_KEY" not in os.environ,
        reason="LLM tests require OPENAI_API_KEY environment variable",
    )
    @pytest.mark.asyncio
    async def test_main_auditor_orchestrates_workflow(self, temp_db, temp_policy_files):
        """Test that main auditor orchestrates the workflow."""
        findings = await run_audit_workflow(dry_run=True)

        assert isinstance(findings, Findings)
        # Workflow should complete successfully

    @pytest.mark.skipif(
        "OPENAI_API_KEY" not in os.environ,
        reason="LLM tests require OPENAI_API_KEY environment variable",
    )
    @pytest.mark.asyncio
    async def test_audit_with_injected_errors(self, temp_db, temp_policy_files):
        """Test audit with injected errors."""
        # Inject errors
        inject_unauthorized_access("alice", "accounts", "DELETE")
        inject_missing_permission("bob", "customers", "SELECT")

        # Run audit
        findings = await run_audit_workflow(dry_run=True)

        assert isinstance(findings, Findings)
        assert len(findings.findings) > 0

    def test_reports_generated(self, tmp_path, monkeypatch):
        """Test that reports are generated."""
        reports_dir = tmp_path / "reports"
        monkeypatch.setattr("src.mcp_servers.fs_server.fs_service.REPORTS_DIR", reports_dir)

        # Create sample findings
        findings = Findings(findings=[])

        # Generate reports
        from src.agents.main_auditor import generate_reports
        import asyncio

        asyncio.run(generate_reports(findings))

        # Check reports were created
        json_file = reports_dir / "findings.json"
        assert json_file.exists()

        markdown_files = list(reports_dir.glob("audit-*.md"))
        assert len(markdown_files) > 0
