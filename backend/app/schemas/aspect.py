from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

Severity = Literal["high", "mid", "low"]


class AspectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    target_phases: list[str] | None = None
    prompt_template: str = Field(min_length=1)
    default_severity: Severity = "mid"
    is_active: bool = True


class AspectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    target_phases: list[str] | None = None
    prompt_template: str | None = Field(default=None, min_length=1)
    default_severity: Severity | None = None
    is_active: bool | None = None


class AspectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    target_phases: list[str] | None
    prompt_template: str
    default_severity: Severity
    is_active: bool
    created_by: UUID | None
