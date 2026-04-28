from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.artifact import ArtifactResponse
from app.schemas.auth import MessageResponse
from app.services.artifact_service import (
    create_artifact,
    delete_artifact,
    get_artifact_for_user,
    get_artifact_path,
    list_artifacts_for_project,
)
from app.services.project_service import get_project_for_user

router = APIRouter()


@router.get("/api/projects/{project_id}/artifacts", response_model=list[ArtifactResponse])
async def list_artifacts(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    phase: Annotated[str | None, Query(max_length=50)] = None,
) -> list[ArtifactResponse]:
    await get_project_for_user(db, current_user.id, project_id)
    return await list_artifacts_for_project(db, project_id, phase)


@router.post(
    "/api/projects/{project_id}/artifacts",
    response_model=ArtifactResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_artifact(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    phase: Annotated[str, Form(max_length=50)],
    file: Annotated[UploadFile, File()],
) -> ArtifactResponse:
    await get_project_for_user(db, current_user.id, project_id)
    return await create_artifact(db, project_id, current_user.id, phase, file)


@router.get("/api/artifacts/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ArtifactResponse:
    return await get_artifact_for_user(db, current_user.id, artifact_id)


@router.get("/api/artifacts/{artifact_id}/download")
async def download_artifact(
    artifact_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FileResponse:
    artifact = await get_artifact_for_user(db, current_user.id, artifact_id)
    path = get_artifact_path(artifact)
    return FileResponse(path=path, filename=artifact.file_name)


@router.delete("/api/artifacts/{artifact_id}", response_model=MessageResponse)
async def delete_artifact_route(
    artifact_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    artifact = await get_artifact_for_user(db, current_user.id, artifact_id)
    await delete_artifact(db, artifact)
    return MessageResponse(message="deleted")
