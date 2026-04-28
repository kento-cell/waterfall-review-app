from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.artifact import Artifact
from app.models.project import Project
from app.models.review import Aspect, Finding, FindingResponse, Review
from app.models.user import User
from app.schemas.finding import FindingListItem, ResponseStatus, Severity
from app.schemas.review import PDFStatusResponse, ReviewCreate, ReviewJobResponse, ReviewResponse
from app.services.job_runner import JobRunner, get_job_runner
from app.services.project_service import get_project_for_user

router = APIRouter()


@router.get("/api/projects/{project_id}/reviews", response_model=list[ReviewResponse])
async def list_reviews(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ReviewResponse]:
    await get_project_for_user(db, current_user.id, project_id)
    result = await db.execute(
        select(Review)
        .where(Review.project_id == project_id)
        .order_by(
            Review.started_at.desc().nullslast(),
            Review.created_at.desc(),
            Review.id.desc(),
        )
    )
    return list(result.scalars().all())


@router.post(
    "/api/projects/{project_id}/reviews",
    response_model=ReviewJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_review(
    project_id: UUID,
    payload: ReviewCreate,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    job_runner: Annotated[JobRunner, Depends(get_job_runner)],
) -> ReviewJobResponse:
    await get_project_for_user(db, current_user.id, project_id)

    # 新API (Phase 3.5): target_artifact_ids が指定されていればそれを使用、
    # なければ旧API互換で artifact_id を使う
    if payload.target_artifact_ids:
        target_ids = payload.target_artifact_ids
    elif payload.artifact_id:
        target_ids = [payload.artifact_id]
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="artifact_id または target_artifact_ids のいずれかが必要です",
        )

    # 各 target_artifact が project 配下に存在するか検証
    primary_artifact = await _get_project_artifact(db, project_id, target_ids[0])
    for aid in target_ids[1:]:
        await _get_project_artifact(db, project_id, aid)

    # aspect_ids が指定されていれば検証 (Phase 4 で aspect_artifact_id 経由の動的生成対応予定)
    if payload.aspect_ids:
        await _ensure_active_aspects(db, payload.aspect_ids)
    elif payload.aspect_artifact_id:
        # PM 提供の観点ファイルが指定されている場合、Artifact 存在のみ確認
        await _get_project_artifact(db, project_id, payload.aspect_artifact_id)

    if payload.review_type == "cross" and len(target_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="cross レビューには UI と SS の target_artifact_ids が必要です",
        )

    review = Review(
        project_id=project_id,
        review_type=payload.review_type or "single",
        target_artifact_ids=[str(aid) for aid in target_ids],
        aspect_ids=[str(aid) for aid in payload.aspect_ids],
        status="pending",
        created_by=current_user.id,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)

    if review.review_type == "cross":
        job_id = job_runner.enqueue_cross_review(
            background_tasks,
            review.id,
            target_ids[0],
            target_ids[1],
            payload.aspect_ids,
            payload.aspect_artifact_id,
        )
    else:
        job_id = job_runner.enqueue_single_review(
            background_tasks,
            review.id,
            primary_artifact.id,
            payload.aspect_ids,
            payload.aspect_artifact_id,
        )
    return ReviewJobResponse(review_id=review.id, job_id=job_id, status=review.status)


@router.get("/api/reviews/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReviewResponse:
    return await _get_review_for_user(db, current_user.id, review_id)


@router.get("/api/reviews/{review_id}/findings", response_model=list[FindingListItem])
async def list_review_findings(
    review_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    severity: Annotated[Severity | None, Query()] = None,
    aspect: Annotated[UUID | None, Query()] = None,
    response_status: Annotated[ResponseStatus | None, Query()] = None,
) -> list[FindingListItem]:
    await _get_review_for_user(db, current_user.id, review_id)
    statement = (
        select(Finding, FindingResponse.status, Aspect.name)
        .outerjoin(FindingResponse, FindingResponse.finding_id == Finding.id)
        .outerjoin(Aspect, Finding.aspect_id == Aspect.id)
        .where(Finding.review_id == review_id)
        .order_by(Finding.created_at)
    )
    if severity is not None:
        statement = statement.where(Finding.severity == severity)
    if aspect is not None:
        statement = statement.where(Finding.aspect_id == aspect)
    if response_status is not None:
        if response_status == "not_started":
            statement = statement.where(
                (FindingResponse.status == "not_started") | (FindingResponse.id.is_(None))
            )
        else:
            statement = statement.where(FindingResponse.status == response_status)

    result = await db.execute(statement)
    return [
        _finding_list_item(finding, status_value, aspect_name)
        for finding, status_value, aspect_name in result.all()
    ]


@router.post(
    "/api/reviews/{review_id}/generate_pdf",
    response_model=PDFStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_review_pdf(
    review_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    job_runner: Annotated[JobRunner, Depends(get_job_runner)],
) -> PDFStatusResponse:
    review = await _get_review_for_user(db, current_user.id, review_id)
    if review.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Review is not completed",
        )
    if review.pdf_status == "completed" and _review_pdf_path(review).is_file():
        return _pdf_status_response(review)
    review.pdf_status = "pending"
    await db.commit()
    await db.refresh(review)
    job_runner.enqueue_pdf_generation(background_tasks, review.id)
    return _pdf_status_response(review)


@router.get("/api/reviews/{review_id}/pdf_status", response_model=PDFStatusResponse)
async def get_review_pdf_status(
    review_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PDFStatusResponse:
    review = await _get_review_for_user(db, current_user.id, review_id)
    return _pdf_status_response(review)


@router.get("/api/reviews/{review_id}/pdf")
async def download_review_pdf(
    review_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FileResponse:
    review = await _get_review_for_user(db, current_user.id, review_id)
    path = _review_pdf_path(review)
    if review.pdf_status != "completed" or not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="PDF is not generated",
        )
    return FileResponse(path=path, media_type="application/pdf", filename=f"{review.id}.pdf")


async def _get_project_artifact(db: AsyncSession, project_id: UUID, artifact_id: UUID) -> Artifact:
    result = await db.execute(
        select(Artifact).where(Artifact.id == artifact_id, Artifact.project_id == project_id)
    )
    artifact = result.scalar_one_or_none()
    if artifact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")
    return artifact


async def _ensure_active_aspects(db: AsyncSession, aspect_ids: list[UUID]) -> None:
    unique_ids = list(dict.fromkeys(aspect_ids))
    result = await db.execute(
        select(Aspect.id).where(Aspect.id.in_(unique_ids), Aspect.is_active.is_(True))
    )
    found_ids = set(result.scalars().all())
    if len(found_ids) != len(unique_ids):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aspect not found")


async def _get_review_for_user(db: AsyncSession, owner_id: UUID, review_id: UUID) -> Review:
    result = await db.execute(
        select(Review)
        .join(Project, Review.project_id == Project.id)
        .where(Review.id == review_id, Project.owner_id == owner_id)
    )
    review = result.scalar_one_or_none()
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    return review


def _pdf_status_response(review: Review) -> PDFStatusResponse:
    return PDFStatusResponse(
        review_id=review.id,
        status=review.pdf_status or "pending",
        pdf_path=review.pdf_path,
        pdf_generated_at=review.pdf_generated_at,
        error_message=review.error_message,
    )


def _review_pdf_path(review: Review):
    if review.pdf_path:
        return settings.backend_dir / review.pdf_path
    return settings.pdf_output_path / f"{review.id}.pdf"


def _finding_list_item(
    finding: Finding,
    status_value: str | None,
    aspect_name: str | None,
) -> FindingListItem:
    return FindingListItem(
        id=finding.id,
        review_id=finding.review_id,
        artifact_id=finding.artifact_id,
        location=finding.location,
        severity=finding.severity,
        aspect_id=finding.aspect_id,
        aspect_name=aspect_name,
        content=finding.content,
        suggestion=finding.suggestion,
        created_at=finding.created_at,
        response_status=status_value or "not_started",
    )
