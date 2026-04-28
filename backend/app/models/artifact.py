from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.database import Base
from app.models.user import utc_now


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("projects.id"))
    phase: Mapped[str] = mapped_column(String(50), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    uploaded_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    project = relationship("Project", back_populates="artifacts")
