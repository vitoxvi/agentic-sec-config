"""MCP DB Server Interface: Query database tables and permissions."""

import sqlite3
from pathlib import Path
from typing import Dict, List

DB_PATH = Path("data/audit.db")


def get_connection() -> sqlite3.Connection:
    """Get database connection."""
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}. Run 'uv run python -m src.core.seed' first."
        )
    return sqlite3.connect(DB_PATH)


def list_tables() -> List[str]:
    """List all table names in the database.

    Returns:
        List of table names (excluding SQLite internal tables)
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        return [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()


def get_privileges(username: str) -> Dict[str, List[str]]:
    """Get user's table → actions mapping.

    Args:
        username: Username to query

    Returns:
        Dictionary mapping table names to lists of allowed actions
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT table_name, action
            FROM permissions
            WHERE username = ? AND granted = 1
            ORDER BY table_name, action
        """,
            (username,),
        )

        privileges: Dict[str, List[str]] = {}
        for table_name, action in cursor.fetchall():
            if table_name not in privileges:
                privileges[table_name] = []
            privileges[table_name].append(action)

        return privileges
    finally:
        conn.close()


def who_can(table_name: str, action: str) -> List[str]:
    """Get list of users who can perform action on table.

    Args:
        table_name: Table name
        action: Action (SELECT, INSERT, UPDATE, DELETE)

    Returns:
        List of usernames
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT username
            FROM permissions
            WHERE table_name = ? AND action = ? AND granted = 1
            ORDER BY username
        """,
            (table_name, action),
        )

        return [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()
