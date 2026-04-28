from __future__ import annotations

import asyncio
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.llm import LLMClient
from app.models.artifact import Artifact
from app.models.review import Finding, Review
from app.models.user import utc_now
from app.parsers import ParserRegistry
from app.services.base_review_engine import (
    VALID_SEVERITIES,
    BaseReviewEngine,
    ReviewAspect,
    render_review_prompt,
)

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_PATTERN = re.compile(r"\b(?:\+?\d[\d -]{8,}\d)\b")


@dataclass(frozen=True)
class PiiMaskRule:
    pattern: re.Pattern[str]
    replacement: str


DEFAULT_PII_MASK_RULES = (
    PiiMaskRule(EMAIL_PATTERN, "[MASKED_EMAIL]"),
    PiiMaskRule(PHONE_PATTERN, "[MASKED_PHONE]"),
)


def mask_pii(text: str, rules: Sequence[PiiMaskRule] = DEFAULT_PII_MASK_RULES) -> str:
    masked = text
    for rule in rules:
        masked = rule.pattern.sub(rule.replacement, masked)
    return masked


class ReviewService(BaseReviewEngine):
    async def run_single_review(
        self,
        artifact_id: UUID,
        aspect_ids: Sequence[UUID],
        review_id: UUID | None = None,
        aspect_artifact_id: UUID | None = None,
    ) -> Review:
        review = await self._get_or_create_review(artifact_id, aspect_ids, review_id)
        persisted_review_id = review.id
        try:
            review.status = "running"
            review.started_at = utc_now()
            review.completed_at = None
            review.error_message = None
            await self._db.commit()

            artifact = await self._get_artifact(artifact_id)
            aspects = await self._resolve_aspects(artifact, aspect_ids, aspect_artifact_id)
            parsed = self._parser_registry.parse(self._artifact_path(artifact), artifact.file_type)
            artifact_content = mask_pii(parsed.content) if settings.pii_masking_enabled else parsed.content
            llm_client = self._client()

            semaphore = asyncio.Semaphore(max(1, settings.review_aspect_concurrency))

            async def review_aspect(aspect: ReviewAspect) -> list[Finding]:
                async with semaphore:
                    prompt = render_review_prompt(
                        aspect,
                        phase=artifact.phase,
                        artifact_content=artifact_content,
                    )
                    raw_response = await llm_client.review_artifact(prompt)
                    return self._build_findings(
                        review=review,
                        artifact=artifact,
                        aspect=aspect,
                        raw_response=raw_response,
                    )

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

    async def mark_stale_running_reviews_failed(self, project_id: UUID | None = None) -> int:
        now = utc_now()
        cutoff = now - timedelta(seconds=settings.review_execution_timeout_seconds)
        statement = (
            update(Review)
            .where(
                Review.status == "running",
                Review.started_at.is_not(None),
                Review.started_at < cutoff,
            )
            .values(
                status="failed",
                completed_at=now,
                error_message="Review job timed out or was interrupted.",
            )
        )
        if project_id is not None:
            statement = statement.where(Review.project_id == project_id)
        result = await self._db.execute(statement)
        await self._db.commit()
        return result.rowcount or 0

    async def _resolve_aspects(
        self,
        artifact: Artifact,
        aspect_ids: Sequence[UUID],
        aspect_artifact_id: UUID | None,
    ) -> list[ReviewAspect]:
        if aspect_ids:
            return await self._get_active_review_aspects(aspect_ids)
        if aspect_artifact_id is not None:
            target = artifact.phase if artifact.phase in {"UI", "SS"} else None
            return await self._get_file_review_aspects(aspect_artifact_id, target)
        return []

    async def _get_or_create_review(
        self,
        artifact_id: UUID,
        aspect_ids: Sequence[UUID],
        review_id: UUID | None,
    ) -> Review:
        if review_id is not None:
            review = await self._db.get(Review, review_id)
            if review is None:
                raise ValueError("Review not found")
            return review

        artifact = await self._get_artifact(artifact_id)
        review = Review(
            project_id=artifact.project_id,
            review_type="single",
            target_artifact_ids=[str(artifact_id)],
            aspect_ids=[str(aspect_id) for aspect_id in aspect_ids],
            status="pending",
        )
        self._db.add(review)
        await self._db.commit()
        await self._db.refresh(review)
        return review
