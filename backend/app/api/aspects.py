from __future__ import annotations

import string
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.review import Aspect
from app.models.user import User
from app.schemas.aspect import AspectCreate, AspectResponse, AspectUpdate
from app.schemas.auth import MessageResponse

router = APIRouter()

REQUIRED_PROMPT_FIELDS = {"phase", "aspect_name", "artifact_content"}


@router.get("", response_model=list[AspectResponse])
async def list_aspects(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    include_inactive: Annotated[bool, Query()] = False,
) -> list[AspectResponse]:
    statement = select(Aspect).order_by(Aspect.name)
    if not include_inactive:
        statement = statement.where(Aspect.is_active.is_(True))
    result = await db.execute(statement)
    return list(result.scalars().all())


@router.post("", response_model=AspectResponse, status_code=status.HTTP_201_CREATED)
async def create_aspect(
    payload: AspectCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AspectResponse:
    _validate_prompt_template(payload.prompt_template)
    aspect = Aspect(**payload.model_dump(), created_by=current_user.id)
    db.add(aspect)
    await db.commit()
    await db.refresh(aspect)
    return aspect


@router.put("/{aspect_id}", response_model=AspectResponse)
async def update_aspect(
    aspect_id: UUID,
    payload: AspectUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AspectResponse:
    aspect = await db.get(Aspect, aspect_id)
    if aspect is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aspect not found")
    values = payload.model_dump(exclude_unset=True)
    if "prompt_template" in values and values["prompt_template"] is not None:
        _validate_prompt_template(values["prompt_template"])
    for key, value in values.items():
        setattr(aspect, key, value)
    await db.commit()
    await db.refresh(aspect)
    return aspect


@router.delete("/{aspect_id}", response_model=MessageResponse)
async def delete_aspect(
    aspect_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    aspect = await db.get(Aspect, aspect_id)
    if aspect is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aspect not found")
    aspect.is_active = False
    await db.commit()
    return MessageResponse(message="deleted")


def _validate_prompt_template(template: str) -> None:
    try:
        field_names = {
            field_name
            for _, field_name, _, _ in string.Formatter().parse(template)
            if field_name is not None
        }
        template.format(
            phase="",
            aspect_name="",
            artifact_content="",
        )
    except (IndexError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid prompt_template format: {exc}",
        ) from exc

    unknown_fields = field_names - REQUIRED_PROMPT_FIELDS
    missing_fields = REQUIRED_PROMPT_FIELDS - field_names
    if unknown_fields or missing_fields:
        details: list[str] = []
        if missing_fields:
            details.append(f"missing fields: {', '.join(sorted(missing_fields))}")
        if unknown_fields:
            details.append(f"unknown fields: {', '.join(sorted(unknown_fields))}")
        raise HTTPException(
            status_code=422,
            detail=f"Invalid prompt_template placeholders: {'; '.join(details)}",
        )
