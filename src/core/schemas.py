"""Pydantic schemas for access configuration and policy structures."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Action(str, Enum):
    """Database actions that can be granted."""

    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class TablePermission(BaseModel):
    """Permission for a specific table."""

    table: str = Field(..., description="Table name")
    actions: List[Action] = Field(..., description="List of allowed actions")


class TeamAccess(BaseModel):
    """Access configuration for a team."""

    team: str = Field(..., description="Team name")
    permissions: List[TablePermission] = Field(..., description="List of table permissions")


class AccessConfig(BaseModel):
    """Root model for technical access configuration."""

    teams: dict[str, List[TablePermission]] = Field(
        ..., description="Mapping of team names to their table permissions"
    )


class FindingSeverity(str, Enum):
    """Severity levels for findings."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Finding(BaseModel):
    """Individual violation/issue found during audit."""

    id: str = Field(..., description="Unique identifier")
    severity: FindingSeverity = Field(..., description="Severity level")
    type: str = Field(
        ..., description="Type of finding (e.g., 'unauthorized_access', 'missing_permission')"
    )
    user: str = Field(..., description="Affected username")
    resource: str = Field(..., description="Table name or resource")
    action: str = Field(..., description="Action that's problematic")
    description: str = Field(..., description="Human-readable explanation")
    recommendation: str = Field(..., description="Suggested fix")
    affected_resources: List[str] = Field(default_factory=list, description="Related resources")


class Findings(BaseModel):
    """Root model containing list of findings."""

    findings: List[Finding] = Field(default_factory=list, description="List of findings")
    audit_date: datetime = Field(
        default_factory=datetime.now, description="When the audit was performed"
    )


class ChangeOperation(str, Enum):
    """Operation types for configuration changes."""

    GRANT = "GRANT"
    REVOKE = "REVOKE"


class Change(BaseModel):
    """Individual change operation in a configuration plan."""

    id: str = Field(..., description="Unique identifier")
    target: str = Field(..., description="User/resource being changed")
    operation: ChangeOperation = Field(..., description="Type of operation")
    resource: str = Field(..., description="Table name")
    action: str = Field(..., description="Action (SELECT, INSERT, etc.)")
    rationale: str = Field(..., description="Why this change is needed")


class ConfigPlan(BaseModel):
    """Root model for configuration change plan."""

    changes: List[Change] = Field(..., description="List of changes")
    created_at: datetime = Field(
        default_factory=datetime.now, description="When the plan was created"
    )
    created_by: Optional[str] = Field(None, description="Who created the plan")
