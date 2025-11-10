"""Seed script: Create database schema and populate with deterministic data."""

import csv
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import typer
from rich.console import Console

from src.core.policy_io import load_access_config

app = typer.Typer(help="Seed database with initial data")
console = Console()

# Database path
DB_PATH = Path("data/audit.db")
USERS_CSV = Path("data/users/users.csv")
ACCESS_CONFIG_YAML = Path("data/policy/access_config.yaml")

# Fixed seed for reproducibility
RANDOM_SEED = 42


def create_tables(conn: sqlite3.Connection) -> None:
    """Create all database tables."""
    cursor = conn.cursor()

    # Business tables
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_name TEXT NOT NULL,
            balance REAL NOT NULL,
            created_at TEXT NOT NULL
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            total REAL NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS procurement (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            supplier TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            cost REAL NOT NULL,
            order_date TEXT NOT NULL
        )
    """
    )

    # Permissions table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            team TEXT NOT NULL,
            table_name TEXT NOT NULL,
            action TEXT NOT NULL,
            granted INTEGER NOT NULL,
            UNIQUE(username, table_name, action)
        )
    """
    )

    conn.commit()


def populate_business_tables(conn: sqlite3.Connection) -> None:
    """Populate business tables with deterministic sample data."""
    cursor = conn.cursor()
    random.seed(RANDOM_SEED)

    # Accounts
    accounts_data = [
        ("Main Operating Account", 50000.0),
        ("Savings Account", 100000.0),
        ("Payroll Account", 25000.0),
        ("Vendor Account", 15000.0),
        ("Petty Cash", 5000.0),
    ]
    base_date = datetime(2024, 1, 1)
    for name, balance in accounts_data:
        cursor.execute(
            "INSERT INTO accounts (account_name, balance, created_at) VALUES (?, ?, ?)",
            (
                name,
                balance,
                (base_date + timedelta(days=random.randint(0, 30))).isoformat(),
            ),
        )

    account_ids = [row[0] for row in cursor.execute("SELECT id FROM accounts").fetchall()]

    # Transactions
    transaction_types = ["deposit", "withdrawal", "transfer"]
    for _ in range(10):
        account_id = random.choice(account_ids)
        amount = round(random.uniform(100, 5000), 2)
        txn_type = random.choice(transaction_types)
        cursor.execute(
            "INSERT INTO transactions (account_id, amount, type, timestamp) VALUES (?, ?, ?, ?)",
            (
                account_id,
                amount,
                txn_type,
                (base_date + timedelta(days=random.randint(0, 60))).isoformat(),
            ),
        )

    # Customers
    customers_data = [
        ("Acme Corp", "contact@acme.com", "active"),
        ("TechStart Inc", "info@techstart.com", "active"),
        ("Global Services", "sales@global.com", "active"),
        ("Local Business", "hello@local.com", "pending"),
        ("Enterprise Ltd", "contact@enterprise.com", "active"),
    ]
    for name, email, status in customers_data:
        cursor.execute(
            "INSERT INTO customers (name, email, status) VALUES (?, ?, ?)",
            (name, email, status),
        )

    customer_ids = [row[0] for row in cursor.execute("SELECT id FROM customers").fetchall()]

    # Orders
    order_statuses = ["pending", "processing", "completed", "cancelled"]
    for _ in range(8):
        customer_id = random.choice(customer_ids)
        total = round(random.uniform(100, 2000), 2)
        status = random.choice(order_statuses)
        cursor.execute(
            "INSERT INTO orders (customer_id, total, status, created_at) VALUES (?, ?, ?, ?)",
            (
                customer_id,
                total,
                status,
                (base_date + timedelta(days=random.randint(0, 45))).isoformat(),
            ),
        )

    # Stock
    stock_data = [
        ("Widget A", 100, 10.50),
        ("Widget B", 50, 25.00),
        ("Gadget X", 200, 5.75),
        ("Gadget Y", 75, 15.00),
        ("Tool Z", 30, 45.00),
    ]
    for product_name, quantity, unit_price in stock_data:
        cursor.execute(
            "INSERT INTO stock (product_name, quantity, unit_price) VALUES (?, ?, ?)",
            (product_name, quantity, unit_price),
        )

    # Procurement
    suppliers = ["Supplier A", "Supplier B", "Supplier C"]
    for _ in range(6):
        product_name = random.choice(["Widget A", "Widget B", "Gadget X", "Gadget Y"])
        supplier = random.choice(suppliers)
        quantity = random.randint(10, 100)
        cost = round(random.uniform(50, 500), 2)
        cursor.execute(
            "INSERT INTO procurement (product_name, supplier, quantity, cost, order_date) VALUES (?, ?, ?, ?, ?)",
            (
                product_name,
                supplier,
                quantity,
                cost,
                (base_date + timedelta(days=random.randint(0, 30))).isoformat(),
            ),
        )

    conn.commit()


def load_users() -> list[dict[str, str]]:
    """Load users from CSV file."""
    users = []
    with USERS_CSV.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            users.append(row)
    return users


def populate_permissions(conn: sqlite3.Connection) -> None:
    """Populate permissions table based on access config and users."""
    cursor = conn.cursor()

    # Load access config
    access_config = load_access_config(ACCESS_CONFIG_YAML)

    # Load users
    users = load_users()

    # Clear existing permissions
    cursor.execute("DELETE FROM permissions")

    # Map users to permissions based on their team
    for user in users:
        username = user["username"]
        team = user["team"]

        if team not in access_config.teams:
            console.print(f"[yellow]Warning: Team '{team}' not found in access config[/yellow]")
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


@app.command()
def seed(
    reset: bool = typer.Option(False, "--reset", help="Reset database (delete existing data)"),
) -> None:
    """Seed database with initial data."""
    # Reset if requested
    if reset and DB_PATH.exists():
        DB_PATH.unlink()
        console.print("[green]Database reset[/green]")

    # Ensure data directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    try:
        # Create tables
        console.print("[cyan]Creating tables...[/cyan]")
        create_tables(conn)

        # Check if data already exists
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM accounts")
        if cursor.fetchone()[0] > 0 and not reset:
            console.print("[yellow]Database already seeded. Use --reset to reseed.[/yellow]")
            return

        # Populate business tables
        console.print("[cyan]Populating business tables...[/cyan]")
        populate_business_tables(conn)

        # Populate permissions
        console.print("[cyan]Populating permissions...[/cyan]")
        populate_permissions(conn)

        console.print("[green]Database seeded successfully![/green]")
    finally:
        conn.close()


if __name__ == "__main__":
    app()
