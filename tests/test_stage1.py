"""Tests for Stage 1: Baseline Data & Policy Surface."""

import pytest
import yaml
from pydantic import ValidationError

from src.core.policy_io import (
    load_access_config,
    load_policy_text,
    validate_access_config,
)
from src.core.schemas import AccessConfig
from src.core.seed import seed
from src.mcp_servers.db_server import get_privileges, list_tables, who_can


@pytest.fixture
def temp_db(tmp_path):
    """Create temporary database for testing."""
    import sqlite3

    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    yield db_path, conn
    conn.close()
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def sample_access_config():
    """Sample valid access config."""
    return {
        "teams": {
            "finance": [
                {"table": "accounts", "actions": ["SELECT", "INSERT", "UPDATE"]},
                {"table": "transactions", "actions": ["SELECT"]},
            ],
            "sales": [
                {"table": "customers", "actions": ["SELECT", "INSERT", "UPDATE"]},
            ],
        }
    }


class TestPolicyIO:
    """Test policy I/O functions."""

    def test_load_policy_text_exists(self, tmp_path):
        """Test loading existing policy text."""
        policy_file = tmp_path / "policy.txt"
        policy_file.write_text("Test policy content")

        content = load_policy_text(policy_file)
        assert content == "Test policy content"

    def test_load_policy_text_not_found(self, tmp_path):
        """Test loading non-existent policy text."""
        policy_file = tmp_path / "nonexistent.txt"

        with pytest.raises(FileNotFoundError):
            load_policy_text(policy_file)

    def test_load_access_config_valid(self, tmp_path, sample_access_config):
        """Test loading valid access config."""
        config_file = tmp_path / "config.yaml"
        with config_file.open("w") as f:
            yaml.dump(sample_access_config, f)

        config = load_access_config(config_file)
        assert isinstance(config, AccessConfig)
        assert "finance" in config.teams
        assert "sales" in config.teams

    def test_load_access_config_invalid_yaml(self, tmp_path):
        """Test loading invalid YAML."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("invalid: yaml: content: [unclosed")

        with pytest.raises(yaml.YAMLError):
            load_access_config(config_file)

    def test_load_access_config_invalid_schema(self, tmp_path):
        """Test loading config with invalid schema."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("invalid: structure")

        with pytest.raises((ValidationError, TypeError)):
            load_access_config(config_file)

    def test_validate_access_config_valid(self, sample_access_config):
        """Test validating valid access config."""
        config = AccessConfig(**sample_access_config)
        assert validate_access_config(config) is True

    def test_validate_access_config_invalid_type(self):
        """Test validating invalid type."""
        with pytest.raises(TypeError):
            validate_access_config("not a config")


class TestSeed:
    """Test seed script functionality."""

    def test_seed_creates_tables(self, tmp_path, monkeypatch):
        """Test that seed creates all tables."""
        # Mock DB path
        db_path = tmp_path / "audit.db"
        monkeypatch.setattr("src.core.seed.DB_PATH", db_path)

        # Run seed
        seed(reset=True)

        # Verify database exists
        assert db_path.exists()

        # Verify tables exist
        import sqlite3

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        expected_tables = [
            "accounts",
            "transactions",
            "customers",
            "orders",
            "stock",
            "procurement",
            "permissions",
        ]
        assert set(tables) == set(expected_tables)

    def test_seed_populates_data(self, tmp_path, monkeypatch):
        """Test that seed populates business tables."""
        db_path = tmp_path / "audit.db"
        monkeypatch.setattr("src.core.seed.DB_PATH", db_path)

        seed(reset=True)

        import sqlite3

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check accounts table has data
        cursor.execute("SELECT COUNT(*) FROM accounts")
        assert cursor.fetchone()[0] > 0

        # Check customers table has data
        cursor.execute("SELECT COUNT(*) FROM customers")
        assert cursor.fetchone()[0] > 0

        # Check stock table has data
        cursor.execute("SELECT COUNT(*) FROM stock")
        assert cursor.fetchone()[0] > 0

        conn.close()

    def test_seed_populates_permissions(self, tmp_path, monkeypatch):
        """Test that seed populates permissions table."""
        db_path = tmp_path / "audit.db"
        monkeypatch.setattr("src.core.seed.DB_PATH", db_path)

        seed(reset=True)

        import sqlite3

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check permissions table has data
        cursor.execute("SELECT COUNT(*) FROM permissions")
        permission_count = cursor.fetchone()[0]
        assert permission_count > 0

        # Check specific user permissions exist
        cursor.execute("SELECT COUNT(*) FROM permissions WHERE username = 'alice'")
        assert cursor.fetchone()[0] > 0

        conn.close()


class TestMCPDBServer:
    """Test MCP DB server interface."""

    def test_list_tables(self, tmp_path, monkeypatch):
        """Test list_tables returns expected tables."""
        db_path = tmp_path / "audit.db"
        monkeypatch.setattr("src.core.seed.DB_PATH", db_path)
        monkeypatch.setattr("src.mcp_servers.db_server.DB_PATH", db_path)

        seed(reset=True)

        tables = list_tables()
        expected_tables = [
            "accounts",
            "transactions",
            "customers",
            "orders",
            "stock",
            "procurement",
            "permissions",
        ]
        assert set(tables) == set(expected_tables)

    def test_get_privileges(self, tmp_path, monkeypatch):
        """Test get_privileges returns correct permissions."""
        db_path = tmp_path / "audit.db"
        monkeypatch.setattr("src.core.seed.DB_PATH", db_path)
        monkeypatch.setattr("src.mcp_servers.db_server.DB_PATH", db_path)

        seed(reset=True)

        # Alice is in finance team, should have access to accounts, transactions, stock
        privileges = get_privileges("alice")
        assert "accounts" in privileges
        assert "SELECT" in privileges["accounts"]
        assert "INSERT" in privileges["accounts"]
        assert "UPDATE" in privileges["accounts"]

    def test_who_can(self, tmp_path, monkeypatch):
        """Test who_can returns correct users."""
        db_path = tmp_path / "audit.db"
        monkeypatch.setattr("src.core.seed.DB_PATH", db_path)
        monkeypatch.setattr("src.mcp_servers.db_server.DB_PATH", db_path)

        seed(reset=True)

        # Finance team members should be able to SELECT from accounts
        users = who_can("accounts", "SELECT")
        assert "alice" in users or "diana" in users  # Finance team members

        # Sales team members should be able to SELECT from customers
        users = who_can("customers", "SELECT")
        assert "bob" in users or "eve" in users  # Sales team members
