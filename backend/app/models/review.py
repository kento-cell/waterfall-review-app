from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.database import Base
from app.models.user import utc_now


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("projects.id"))
    review_type: Mapped[str] = mapped_column(String(20), nullable=False)
    target_artifact_ids: Mapped[list[str]] = mapped_column(JSON(), nullable=False)
    aspect_ids: Mapped[list[str]] = mapped_column(JSON(), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    created_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"))
    error_message: Mapped[str | None] = mapped_column(Text())
    pdf_status: Mapped[str | None] = mapped_column(String(20))
    pdf_path: Mapped[str | None] = mapped_column(String(500))
    pdf_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    findings = relationship("Finding", back_populates="review")


class Aspect(Base):
    __tablename__ = "aspects"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())
    target_phases: Mapped[list[str] | None] = mapped_column(JSON())
    prompt_template: Mapped[str] = mapped_column(Text(), nullable=False)
    default_severity: Mapped[str] = mapped_column(String(10), nullable=False, default="mid")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"))

    findings = relationship("Finding", back_populates="aspect")


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    review_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("reviews.id"))
    artifact_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("artifacts.id"))
    location: Mapped[str | None] = mapped_column(String(500))
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    aspect_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("aspects.id"))
    content: Mapped[str] = mapped_column(Text(), nullable=False)
    suggestion: Mapped[str | None] = mapped_column(Text())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    review = relationship("Review", back_populates="findings")
    aspect = relationship("Aspect", back_populates="findings")
    response = relationship("FindingResponse", back_populates="finding", uselist=False)


class FindingResponse(Base):
    __tablename__ = "responses"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    finding_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("findings.id"), unique=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="not_started")
    comment: Mapped[str | None] = mapped_column(Text())
    updated_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    finding = relationship("Finding", back_populates="response")
