"""Policy I/O: Load natural language policy and technical access configuration."""

from pathlib import Path

import yaml
from pydantic import ValidationError

from src.core.schemas import AccessConfig


def load_policy_text(path: str | Path) -> str:
    """Load natural language policy from text file.

    Args:
        path: Path to policy.txt file

    Returns:
        Policy text content

    Raises:
        FileNotFoundError: If policy file doesn't exist
        IOError: If file cannot be read
    """
    policy_path = Path(path)
    if not policy_path.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")

    return policy_path.read_text(encoding="utf-8")


def load_access_config(path: str | Path) -> AccessConfig:
    """Load and validate technical access configuration from YAML.

    Args:
        path: Path to access_config.yaml file

    Returns:
        Validated AccessConfig object

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML is invalid
        ValidationError: If config doesn't match schema
    """
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Access config file not found: {path}")

    with config_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        raise ValueError(f"Access config file is empty: {path}")

    try:
        return AccessConfig(**data)
    except ValidationError:
        # Re-raise ValidationError as-is
        raise


def validate_access_config(config: AccessConfig) -> bool:
    """Validate access configuration structure.

    Args:
        config: AccessConfig to validate

    Returns:
        True if valid

    Raises:
        ValidationError: If config is invalid
    """
    # Pydantic models validate on creation, so if we have an AccessConfig
    # object, it's already valid. This function is mainly for explicit checks.
    if not isinstance(config, AccessConfig):
        raise TypeError(f"Expected AccessConfig, got {type(config)}")

    # Additional business logic validation could go here
    # For now, Pydantic validation is sufficient
    return True
