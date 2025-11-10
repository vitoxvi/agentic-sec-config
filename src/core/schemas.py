"""Pydantic schemas for access configuration and policy structures."""

from enum import Enum
from typing import List

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
