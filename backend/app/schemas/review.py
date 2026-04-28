from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

PdfStatus = str


class ReviewCreate(BaseModel):
    # 旧API互換: 単一 artifact + 既存 aspect IDs
    artifact_id: UUID | None = None
    aspect_ids: list[UUID] = Field(default_factory=list)
    # 新API (Phase 3.5+): D&D 1画面投入対応
    review_type: str = "single"  # single / cross
    target_artifact_ids: list[UUID] | None = None
    aspect_artifact_id: UUID | None = None  # 観点ファイル (PM 提供) の artifact ID


class ReviewJobResponse(BaseModel):
    review_id: UUID
    job_id: str
    status: str


class PDFStatusResponse(BaseModel):
    review_id: UUID
    status: PdfStatus
    pdf_path: str | None = None
    pdf_generated_at: datetime | None = None
    error_message: str | None = None


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID | None
    review_type: str
    target_artifact_ids: list[UUID]
    aspect_ids: list[UUID]
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    created_by: UUID | None
    error_message: str | None
    pdf_status: str | None = None
    pdf_path: str | None = None
    pdf_generated_at: datetime | None = None
