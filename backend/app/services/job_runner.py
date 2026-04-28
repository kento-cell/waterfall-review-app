from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from fastapi import BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.services.cross_review_engine import CrossReviewEngine
from app.services.pdf_generation import PDFGenerationService
from app.services.review_engine import ReviewService

SessionFactory = Callable[[], AsyncSession]


class JobRunner:
    def enqueue_single_review(
        self,
        background_tasks: BackgroundTasks,
        review_id: UUID,
        artifact_id: UUID,
        aspect_ids: list[UUID],
        aspect_artifact_id: UUID | None = None,
    ) -> str:
        raise NotImplementedError

    def enqueue_cross_review(
        self,
        background_tasks: BackgroundTasks,
        review_id: UUID,
        ui_artifact_id: UUID,
        ss_artifact_id: UUID,
        aspect_ids: list[UUID],
        aspect_artifact_id: UUID | None = None,
    ) -> str:
        raise NotImplementedError

    def enqueue_pdf_generation(
        self,
        background_tasks: BackgroundTasks,
        review_id: UUID,
    ) -> str:
        raise NotImplementedError


class BackgroundTaskJobRunner(JobRunner):
    def __init__(self, session_factory: SessionFactory = async_session_factory) -> None:
        self._session_factory = session_factory

    def enqueue_single_review(
        self,
        background_tasks: BackgroundTasks,
        review_id: UUID,
        artifact_id: UUID,
        aspect_ids: list[UUID],
        aspect_artifact_id: UUID | None = None,
    ) -> str:
        background_tasks.add_task(
            run_single_review_job,
            self._session_factory,
            review_id,
            artifact_id,
            aspect_ids,
            aspect_artifact_id,
        )
        return str(review_id)

    def enqueue_cross_review(
        self,
        background_tasks: BackgroundTasks,
        review_id: UUID,
        ui_artifact_id: UUID,
        ss_artifact_id: UUID,
        aspect_ids: list[UUID],
        aspect_artifact_id: UUID | None = None,
    ) -> str:
        background_tasks.add_task(
            run_cross_review_job,
            self._session_factory,
            review_id,
            ui_artifact_id,
            ss_artifact_id,
            aspect_ids,
            aspect_artifact_id,
        )
        return str(review_id)

    def enqueue_pdf_generation(
        self,
        background_tasks: BackgroundTasks,
        review_id: UUID,
    ) -> str:
        background_tasks.add_task(
            run_pdf_generation_job,
            self._session_factory,
            review_id,
        )
        return str(review_id)


async def run_single_review_job(
    session_factory: SessionFactory,
    review_id: UUID,
    artifact_id: UUID,
    aspect_ids: list[UUID],
    aspect_artifact_id: UUID | None = None,
) -> None:
    async with session_factory() as db:
        service = ReviewService(db)
        await service.run_single_review(
            artifact_id,
            aspect_ids,
            review_id=review_id,
            aspect_artifact_id=aspect_artifact_id,
        )


async def run_cross_review_job(
    session_factory: SessionFactory,
    review_id: UUID,
    ui_artifact_id: UUID,
    ss_artifact_id: UUID,
    aspect_ids: list[UUID],
    aspect_artifact_id: UUID | None = None,
) -> None:
    async with session_factory() as db:
        service = CrossReviewEngine(db)
        await service.run_cross_review(
            ui_artifact_id,
            ss_artifact_id,
            aspect_ids,
            review_id=review_id,
            aspect_artifact_id=aspect_artifact_id,
        )


async def run_pdf_generation_job(
    session_factory: SessionFactory,
    review_id: UUID,
) -> None:
    async with session_factory() as db:
        service = PDFGenerationService(db)
        await service.generate_pdf(review_id)


def get_job_runner() -> JobRunner:
    return BackgroundTaskJobRunner()


JobRunnerDependency = Depends(get_job_runner)
