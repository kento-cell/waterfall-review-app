from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

DEFAULT_PHASES = ["要件定義", "基本設計", "詳細設計", "PG", "UT", "IT", "ST"]


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    phases: list[str] | None = Field(default=None)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    phases: list[str] | None = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID | None
    name: str
    description: str | None
    phases: list[str] | None
    created_at: datetime
    updated_at: datetime
