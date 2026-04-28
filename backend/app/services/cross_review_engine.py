from __future__ import annotations

import asyncio
from collections.abc import Sequence
from uuid import UUID

from app.core.config import settings
from app.models.review import Finding, Review
from app.models.user import utc_now
from app.services.base_review_engine import BaseReviewEngine, ReviewAspect
from app.services.review_engine import mask_pii


class CrossReviewEngine(BaseReviewEngine):
    async def run_cross_review(
        self,
        ui_artifact_id: UUID,
        ss_artifact_id: UUID,
        aspect_ids: Sequence[UUID],
        review_id: UUID | None = None,
        aspect_artifact_id: UUID | None = None,
    ) -> Review:
        review = await self._get_or_create_review(
            ui_artifact_id,
            ss_artifact_id,
            aspect_ids,
            review_id,
        )
        persisted_review_id = review.id
        try:
            review.status = "running"
            review.started_at = utc_now()
            review.completed_at = None
            review.error_message = None
            await self._db.commit()

            ui_artifact = await self._get_artifact(ui_artifact_id)
            ss_artifact = await self._get_artifact(ss_artifact_id)
            ui_content = self._parser_registry.parse(
                self._artifact_path(ui_artifact),
                ui_artifact.file_type,
            ).content
            ss_content = self._parser_registry.parse(
                self._artifact_path(ss_artifact),
                ss_artifact.file_type,
            ).content
            if settings.pii_masking_enabled:
                ui_content = mask_pii(ui_content)
                ss_content = mask_pii(ss_content)

            aspects = await self._resolve_aspects(aspect_ids, aspect_artifact_id)
            llm_client = self._client()
            semaphore = asyncio.Semaphore(max(1, settings.review_aspect_concurrency))

            async def review_aspect(aspect: ReviewAspect) -> list[Finding]:
                async with semaphore:
                    raw_response = await llm_client.review_artifact(
                        _cross_prompt(aspect, ui_content=ui_content, ss_content=ss_content)
                    )
                    return [
                        self._build_finding(review.id, ui_artifact.id, aspect, item)
                        for item in self._parse_response(raw_response)
                    ]

            async with asyncio.timeout(settings.review_execution_timeout_seconds):
                finding_groups = await asyncio.gather(*(review_aspect(aspect) for aspect in aspects))
            findings = [finding for group in finding_groups for finding in group]

            self._db.add_all(findings)
            review.status = "completed"
            review.completed_at = utc_now()
            await self._db.commit()
            await self._db.refresh(review)
            return review
        except Exception as exc:
            await self._db.rollback()
            review = await self._db.get(Review, persisted_review_id)
            if review is not None:
                review.status = "failed"
                review.completed_at = utc_now()
                review.error_message = (str(exc) or exc.__class__.__name__)[:2000]
                await self._db.commit()
                await self._db.refresh(review)
                return review
            raise

    async def _resolve_aspects(
        self,
        aspect_ids: Sequence[UUID],
        aspect_artifact_id: UUID | None,
    ) -> list[ReviewAspect]:
        if aspect_ids:
            return await self._get_active_review_aspects(aspect_ids)
        if aspect_artifact_id is not None:
            return await self._get_file_review_aspects(aspect_artifact_id, "UI×SS")
        return [
            ReviewAspect(
                id=None,
                name="UI×SS 整合性",
                target="UI×SS",
                default_severity="mid",
                prompt_template="UI と SS の対応関係の漏れ・矛盾・不整合を確認してください。",
            )
        ]

    async def _get_or_create_review(
        self,
        ui_artifact_id: UUID,
        ss_artifact_id: UUID,
        aspect_ids: Sequence[UUID],
        review_id: UUID | None,
    ) -> Review:
        if review_id is not None:
            review = await self._db.get(Review, review_id)
            if review is None:
                raise ValueError("Review not found")
            return review

        ui_artifact = await self._get_artifact(ui_artifact_id)
        review = Review(
            project_id=ui_artifact.project_id,
            review_type="cross",
            target_artifact_ids=[str(ui_artifact_id), str(ss_artifact_id)],
            aspect_ids=[str(aspect_id) for aspect_id in aspect_ids],
            status="pending",
        )
        self._db.add(review)
        await self._db.commit()
        await self._db.refresh(review)
        return review


def _cross_prompt(aspect: ReviewAspect, *, ui_content: str, ss_content: str) -> str:
    return (
        "以下の UI と SS について、対応関係の漏れ・矛盾・不整合を JSON で返してください。\n"
        "location 形式: UI:Sheet1!A23 ↔ SS:Sheet3!行42-58\n"
        f"観点: {aspect.name}\n"
        f"レビュー指示文:\n{aspect.prompt_template}\n\n"
        f"UI:\n{ui_content}\n\nSS:\n{ss_content}"
    )
