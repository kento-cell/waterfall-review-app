from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

Severity = Literal["high", "mid", "low"]
ResponseStatus = Literal["not_started", "in_progress", "done", "not_applicable"]


class FindingListItem(BaseModel):
    id: UUID
    review_id: UUID | None
    artifact_id: UUID | None
    location: str | None
    severity: Severity
    aspect_id: UUID | None
    aspect_name: str | None = None
    content: str
    suggestion: str | None
    created_at: datetime
    response_status: ResponseStatus


class FindingResponsePayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    finding_id: UUID | None
    status: ResponseStatus
    comment: str | None
    updated_by: UUID | None
    updated_at: datetime


class FindingDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    review_id: UUID | None
    artifact_id: UUID | None
    location: str | None
    severity: Severity
    aspect_id: UUID | None
    content: str
    suggestion: str | None
    created_at: datetime
    response: FindingResponsePayload | None


class FindingResponseUpdate(BaseModel):
    status: ResponseStatus
    comment: str | None = None
