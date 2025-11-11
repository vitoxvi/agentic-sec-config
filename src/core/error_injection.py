"""Error Injection: Create deterministic misconfigurations for testing."""

import csv
import sqlite3
from pathlib import Path

from src.core.policy_io import load_access_config

DB_PATH = Path("data/audit.db")
ACCESS_CONFIG_YAML = Path("data/policy/access_config.yaml")
USERS_CSV = Path("data/users/users.csv")


def get_connection() -> sqlite3.Connection:
    """Get database connection."""
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}. Run 'uv run python -m src.core.seed' first."
        )
    return sqlite3.connect(DB_PATH)


def inject_unauthorized_access(username: str, table: str, action: str) -> None:
    """Grant permission that violates policy (unauthorized access).

    Args:
        username: Username to grant permission to
        table: Table name
        action: Action (SELECT, INSERT, UPDATE, DELETE)
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Get user's team from permissions table
        cursor.execute(
            "SELECT DISTINCT team FROM permissions WHERE username = ? LIMIT 1",
            (username,),
        )
        result = cursor.fetchone()
        if not result:
            raise ValueError(f"User '{username}' not found in permissions table")
        team = result[0]

        # Insert or update permission
        cursor.execute(
            """
            INSERT OR REPLACE INTO permissions (username, team, table_name, action, granted)
            VALUES (?, ?, ?, ?, 1)
        """,
            (username, team, table, action),
        )
        conn.commit()
    finally:
        conn.close()


def inject_missing_permission(username: str, table: str, action: str) -> None:
    """Revoke required permission (missing permission violation).

    Args:
        username: Username to revoke permission from
        table: Table name
        action: Action (SELECT, INSERT, UPDATE, DELETE)
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Revoke permission by setting granted = 0
        cursor.execute(
            """
            UPDATE permissions
            SET granted = 0
            WHERE username = ? AND table_name = ? AND action = ?
        """,
            (username, table, action),
        )
        conn.commit()
    finally:
        conn.close()


def reset_permissions() -> None:
    """Reset permissions to clean state (re-seed from config).

    This clears all permissions and repopulates them based on access_config.yaml
    and users.csv, matching the seed.py behavior.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Load access config
        access_config = load_access_config(ACCESS_CONFIG_YAML)

        # Load users
        users = []
        with USERS_CSV.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                users.append(row)

        # Clear all permissions
        cursor.execute("DELETE FROM permissions")

        # Map users to permissions based on their team
        for user in users:
            username = user["username"]
            team = user["team"]

            if team not in access_config.teams:
                continue

            # Get permissions for this team
            team_permissions = access_config.teams[team]

            for table_perm in team_permissions:
                table_name = table_perm.table
                for action in table_perm.actions:
                    cursor.execute(
                        """
                        INSERT INTO permissions (username, team, table_name, action, granted)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (username, team, table_name, action.value, 1),
                    )

        conn.commit()
    finally:
        conn.close()
