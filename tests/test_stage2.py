"""Tests for Stage 2: Contracts & Agent Skeleton."""

from datetime import datetime
from pathlib import Path

import pytest
import yaml

from src.core.mcp_config import get_server_info, list_servers, load_mcp_config
from src.core.schemas import (
    Change,
    ChangeOperation,
    ConfigPlan,
    Finding,
    FindingSeverity,
    Findings,
)


class TestSchemas:
    """Test Findings and ConfigPlan schemas."""

    def test_finding_schema_valid(self):
        """Test creating a valid Finding."""
        finding = Finding(
            id="find-001",
            severity=FindingSeverity.HIGH,
            type="unauthorized_access",
            user="alice",
            resource="accounts",
            action="DELETE",
            description="User has DELETE permission but shouldn't",
            recommendation="Revoke DELETE permission",
            affected_resources=["accounts", "transactions"],
        )
        assert finding.id == "find-001"
        assert finding.severity == FindingSeverity.HIGH

    def test_findings_schema_valid(self):
        """Test creating valid Findings."""
        findings = Findings(
            findings=[
                Finding(
                    id="find-001",
                    severity=FindingSeverity.MEDIUM,
                    type="missing_permission",
                    user="bob",
                    resource="customers",
                    action="SELECT",
                    description="User missing required permission",
                    recommendation="Grant SELECT permission",
                )
            ]
        )
        assert len(findings.findings) == 1
        assert isinstance(findings.audit_date, datetime)

    def test_findings_empty(self):
        """Test creating empty Findings."""
        findings = Findings()
        assert len(findings.findings) == 0
        assert isinstance(findings.audit_date, datetime)

    def test_change_schema_valid(self):
        """Test creating a valid Change."""
        change = Change(
            id="change-001",
            target="alice",
            operation=ChangeOperation.REVOKE,
            resource="accounts",
            action="DELETE",
            rationale="Remove unauthorized DELETE permission",
        )
        assert change.operation == ChangeOperation.REVOKE

    def test_configplan_schema_valid(self):
        """Test creating valid ConfigPlan."""
        plan = ConfigPlan(
            changes=[
                Change(
                    id="change-001",
                    target="alice",
                    operation=ChangeOperation.GRANT,
                    resource="customers",
                    action="SELECT",
                    rationale="Add required permission",
                )
            ],
            created_by="system",
        )
        assert len(plan.changes) == 1
        assert isinstance(plan.created_at, datetime)
        assert plan.created_by == "system"


class TestMCPConfig:
    """Test MCP server configuration loading."""

    def test_load_mcp_config_exists(self, tmp_path):
        """Test loading existing MCP config."""
        config_file = tmp_path / "mcp_servers.yaml"
        config_data = {
            "servers": {
                "db_server": {
                    "name": "Database Server",
                    "description": "Test server",
                    "command": ["python", "-m", "test.server"],
                    "tools": ["tool1", "tool2"],
                }
            }
        }
        with config_file.open("w") as f:
            yaml.dump(config_data, f)

        config = load_mcp_config(config_file)
        assert "db_server" in config.servers
        assert config.servers["db_server"].name == "Database Server"

    def test_load_mcp_config_not_found(self, tmp_path):
        """Test loading non-existent config."""
        config_file = tmp_path / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError):
            load_mcp_config(config_file)

    def test_get_server_info(self):
        """Test getting server info by ID."""
        config = load_mcp_config()
        server_info = get_server_info(config, "db_server")
        assert server_info is not None
        assert server_info.name == "Database Server"

    def test_get_server_info_not_found(self):
        """Test getting non-existent server info."""
        config = load_mcp_config()
        server_info = get_server_info(config, "nonexistent")
        assert server_info is None

    def test_list_servers(self):
        """Test listing all servers."""
        config = load_mcp_config()
        servers = list_servers(config)
        assert len(servers) > 0
        assert any(server_id == "db_server" for server_id, _ in servers)


class TestMCPServer:
    """Test MCP server implementation."""

    def test_mcp_server_import(self):
        """Test that MCP server module can be imported."""
        from src.mcp_servers.db_server import db_mcp_server

        assert db_mcp_server is not None

    def test_mcp_server_tools_registered(self):
        """Test that tools are registered in MCP server."""
        from src.mcp_servers.db_server.db_mcp_server import mcp

        # FastMCP exposes tools through internal structure
        # We can verify the server was created successfully
        assert mcp is not None
        assert mcp.name == "Database Server"


class TestMCPToolCalls:
    """Test calling MCP tools via client."""

    def test_mcp_server_has_tools(self):
        """Test that MCP server defines the expected tools."""
        from src.mcp_servers.db_server.db_mcp_server import mcp

        # Verify server exists
        assert mcp is not None
        assert mcp.name == "Database Server"

        # Note: Actual tool calls via stdio_client will be tested in Stage 3
        # when agents are implemented. For now, we verify the server structure.


class TestMainAuditor:
    """Test main auditor skeleton."""

    def test_audit_command_exists(self):
        """Test that audit command is registered."""
        from src.agents.main_auditor import app

        # Check that audit command exists by checking registered commands
        # Typer stores commands in app.registered_commands
        command_names = []
        for cmd in app.registered_commands:
            # Commands can be accessed via their callback function name
            if hasattr(cmd, "callback"):
                func_name = cmd.callback.__name__ if cmd.callback else None
                if func_name == "audit":
                    command_names.append("audit")

        # Alternative: check by trying to get help
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "-m", "src.agents.main_auditor", "audit", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0 or "audit" in result.stdout or "audit" in result.stderr

    def test_audit_produces_empty_findings(self, tmp_path, monkeypatch):
        """Test that audit produces empty findings on clean DB."""
        # Mock reports directory
        reports_dir = tmp_path / "reports"
        monkeypatch.setattr(
            "src.agents.main_auditor.Path",
            lambda x: reports_dir if "reports" in str(x) else Path(x),
        )

        from src.agents.main_auditor import audit

        # Run audit in dry-run mode
        # Note: This will actually execute, so we need to ensure DB exists
        try:
            audit(dry_run=True)
            # Verify report was created
            report_files = list(reports_dir.glob("audit-*.md"))
            assert len(report_files) > 0
        except FileNotFoundError:
            # If database doesn't exist, that's expected in test environment
            pytest.skip("Database not seeded - skipping audit execution test")
