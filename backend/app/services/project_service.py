from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact import Artifact
from app.models.project import Project
from app.schemas.project import DEFAULT_PHASES, ProjectCreate, ProjectUpdate


async def list_projects_for_user(db: AsyncSession, owner_id: UUID) -> list[Project]:
    result = await db.execute(select(Project).where(Project.owner_id == owner_id).order_by(Project.created_at))
    return list(result.scalars().all())


async def create_project(db: AsyncSession, owner_id: UUID, payload: ProjectCreate) -> Project:
    project = Project(
        owner_id=owner_id,
        name=payload.name,
        description=payload.description,
        phases=payload.phases if payload.phases is not None else DEFAULT_PHASES,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def get_project_for_user(db: AsyncSession, owner_id: UUID, project_id: UUID) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.owner_id != owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Project access denied")
    return project


async def update_project(db: AsyncSession, project: Project, payload: ProjectUpdate) -> Project:
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)
    await db.commit()
    await db.refresh(project)
    return project


async def delete_project(db: AsyncSession, project: Project) -> None:
    artifact_result = await db.execute(select(Artifact).where(Artifact.project_id == project.id))
    for artifact in artifact_result.scalars().all():
        await db.delete(artifact)
    await db.delete(project)
    await db.commit()
