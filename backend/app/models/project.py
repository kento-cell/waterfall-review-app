from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.database import Base
from app.models.user import utc_now


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("owner_id", "name", name="uq_projects_owner_id_name"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    owner_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())
    phases: Mapped[list[str] | None] = mapped_column(JSON())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    owner = relationship("User", back_populates="projects")
    artifacts = relationship("Artifact", back_populates="project")
