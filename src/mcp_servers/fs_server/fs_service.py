"""MCP Filesystem Server Interface: Read and write files for policy and reports."""

from pathlib import Path
from typing import Optional

# Default paths
POLICY_PATH = Path("data/policy/policy.txt")
ACCESS_CONFIG_PATH = Path("data/policy/access_config.yaml")
USERS_CSV_PATH = Path("data/users/users.csv")
REPORTS_DIR = Path("reports")


def read_file(file_path: str | Path) -> str:
    """Read file content.

    Args:
        file_path: Path to file to read

    Returns:
        File content as string

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return path.read_text(encoding="utf-8")


def write_file(file_path: str | Path, content: str) -> None:
    """Write content to file.

    Args:
        file_path: Path to file to write
        content: Content to write

    Raises:
        IOError: If file cannot be written
    """
    path = Path(file_path)
    # Create parent directories if they don't exist
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_policy() -> str:
    """Read policy.txt file.

    Returns:
        Policy text content

    Raises:
        FileNotFoundError: If policy.txt doesn't exist
    """
    return read_file(POLICY_PATH)


def write_access_config(config_yaml: str) -> None:
    """Write access_config.yaml file.

    Args:
        config_yaml: YAML content to write

    Raises:
        IOError: If file cannot be written
    """
    write_file(ACCESS_CONFIG_PATH, config_yaml)


def read_access_config() -> str:
    """Read access_config.yaml file.

    Returns:
        Access config YAML content

    Raises:
        FileNotFoundError: If access_config.yaml doesn't exist
    """
    return read_file(ACCESS_CONFIG_PATH)


def read_users_csv() -> str:
    """Read users.csv file.

    Returns:
        CSV content

    Raises:
        FileNotFoundError: If users.csv doesn't exist
    """
    return read_file(USERS_CSV_PATH)


def write_findings_json(findings_json: str, output_path: Optional[str | Path] = None) -> None:
    """Write Findings JSON to file.

    Args:
        findings_json: JSON content to write
        output_path: Optional path for output file. Defaults to reports/findings.json
    """
    if output_path is None:
        output_path = REPORTS_DIR / "findings.json"
    write_file(output_path, findings_json)


def write_report_markdown(markdown: str, output_path: Optional[str | Path] = None) -> None:
    """Write Markdown report to file.

    Args:
        markdown: Markdown content to write
        output_path: Optional path for output file. Defaults to reports/audit-YYYYMMDD.md
    """
    if output_path is None:
        from datetime import datetime

        output_path = REPORTS_DIR / f"audit-{datetime.now().strftime('%Y%m%d')}.md"
    write_file(output_path, markdown)
