from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ArtifactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID | None
    phase: str
    file_name: str
    file_path: str
    file_type: str
    version: int
    size_bytes: int
    uploaded_by: UUID | None
    uploaded_at: datetime
