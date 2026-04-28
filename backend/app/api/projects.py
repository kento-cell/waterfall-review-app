from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.project_service import (
    create_project,
    delete_project,
    get_project_for_user,
    list_projects_for_user,
    update_project,
)

router = APIRouter()


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ProjectResponse]:
    return await list_projects_for_user(db, current_user.id)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create(
    payload: ProjectCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectResponse:
    try:
        return await create_project(db, current_user.id, payload)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project name already exists for this user",
        ) from exc


@router.get("/{project_id}", response_model=ProjectResponse)
async def get(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectResponse:
    return await get_project_for_user(db, current_user.id, project_id)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update(
    project_id: UUID,
    payload: ProjectUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectResponse:
    try:
        project = await get_project_for_user(db, current_user.id, project_id)
        return await update_project(db, project, payload)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project name already exists for this user",
        ) from exc


@router.delete("/{project_id}", response_model=MessageResponse)
async def delete(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    project = await get_project_for_user(db, current_user.id, project_id)
    await delete_project(db, project)
    return MessageResponse(message="deleted")
