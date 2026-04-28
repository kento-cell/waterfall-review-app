from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.project import Project
from app.models.review import Finding, FindingResponse, Review
from app.models.user import User
from app.schemas.finding import FindingDetail, FindingResponsePayload, FindingResponseUpdate

router = APIRouter()


@router.get("/api/findings/{finding_id}", response_model=FindingDetail)
async def get_finding(
    finding_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FindingDetail:
    finding = await _get_finding_for_user(db, current_user.id, finding_id)
    return FindingDetail.model_validate(finding)


@router.put("/api/findings/{finding_id}/response", response_model=FindingResponsePayload)
async def update_finding_response(
    finding_id: UUID,
    payload: FindingResponseUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FindingResponsePayload:
    finding = await _get_finding_for_user(db, current_user.id, finding_id)
    response = finding.response
    if response is None:
        response = FindingResponse(finding_id=finding.id)
        db.add(response)
    response.status = payload.status
    response.comment = payload.comment
    response.updated_by = current_user.id
    await db.commit()
    await db.refresh(response)
    return response


async def _get_finding_for_user(db: AsyncSession, owner_id: UUID, finding_id: UUID) -> Finding:
    result = await db.execute(
        select(Finding)
        .options(selectinload(Finding.response))
        .join(Review, Finding.review_id == Review.id)
        .join(Project, Review.project_id == Project.id)
        .where(Finding.id == finding_id, Project.owner_id == owner_id)
    )
    finding = result.scalar_one_or_none()
    if finding is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")
    return finding
