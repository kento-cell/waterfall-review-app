from __future__ import annotations

from pathlib import Path
from uuid import UUID

import fitz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.artifact import Artifact
from app.models.review import Finding, Review
from app.models.user import utc_now
from app.services.pdf_annotator import PDFAnnotator, PdfAnnotationFinding
from app.services.pdf_converter import PDFConverter


class PDFGenerationService:
    def __init__(
        self,
        db: AsyncSession,
        converter: PDFConverter | None = None,
        annotator: PDFAnnotator | None = None,
    ) -> None:
        self._db = db
        self._converter = converter or PDFConverter()
        self._annotator = annotator or PDFAnnotator()

    async def generate_pdf(self, review_id: UUID) -> Review:
        review = await self._get_review(review_id)
        try:
            if review.status != "completed":
                raise ValueError("Review must be completed before PDF generation")
            review.pdf_status = "running"
            review.error_message = None
            await self._db.commit()

            artifacts = await self._get_target_artifacts(review)
            findings = await self._get_findings(review.id)
            source_pdf = self._build_source_pdf(review.id, artifacts)
            output_pdf = settings.pdf_output_path / f"{review.id}.pdf"
            self._annotator.annotate(
                source_pdf,
                output_pdf,
                _annotation_findings(findings),
                include_pt_candidates=_include_pt_candidates(review, artifacts),
            )

            review.pdf_status = "completed"
            review.pdf_path = output_pdf.relative_to(settings.backend_dir).as_posix()
            review.pdf_generated_at = utc_now()
            await self._db.commit()
            await self._db.refresh(review)
            return review
        except Exception as exc:
            await self._db.rollback()
            review = await self._get_review(review_id)
            review.pdf_status = "failed"
            review.error_message = (str(exc) or exc.__class__.__name__)[:2000]
            await self._db.commit()
            await self._db.refresh(review)
            return review

    async def _get_review(self, review_id: UUID) -> Review:
        review = await self._db.get(Review, review_id)
        if review is None:
            raise ValueError("Review not found")
        return review

    async def _get_target_artifacts(self, review: Review) -> list[Artifact]:
        ids = [UUID(value) for value in review.target_artifact_ids]
        if not ids:
            raise ValueError("Review has no target artifacts")
        result = await self._db.execute(select(Artifact).where(Artifact.id.in_(ids)))
        artifacts_by_id = {artifact.id: artifact for artifact in result.scalars().all()}
        missing = [str(artifact_id) for artifact_id in ids if artifact_id not in artifacts_by_id]
        if missing:
            raise ValueError(f"Target artifact not found: {', '.join(missing)}")
        return [artifacts_by_id[artifact_id] for artifact_id in ids]

    async def _get_findings(self, review_id: UUID) -> list[Finding]:
        result = await self._db.execute(
            select(Finding)
            .options(selectinload(Finding.aspect))
            .where(Finding.review_id == review_id)
            .order_by(Finding.created_at, Finding.id)
        )
        return list(result.scalars().all())

    def _build_source_pdf(self, review_id: UUID, artifacts: list[Artifact]) -> Path:
        source_paths = [
            self._source_pdf_for_artifact(review_id, index, artifact)
            for index, artifact in enumerate(artifacts, start=1)
        ]
        if len(source_paths) == 1:
            return source_paths[0]
        combined_path = settings.pdf_output_path / f"{review_id}_combined.pdf"
        combined_path.parent.mkdir(parents=True, exist_ok=True)
        combined = fitz.open()
        try:
            for source_path in source_paths:
                source = fitz.open(source_path)
                try:
                    combined.insert_pdf(source)
                finally:
                    source.close()
            combined.save(combined_path, garbage=4, deflate=True)
        finally:
            combined.close()
        return combined_path

    def _source_pdf_for_artifact(self, review_id: UUID, index: int, artifact: Artifact) -> Path:
        path = settings.backend_dir / artifact.file_path
        if not path.is_file():
            raise ValueError("Artifact file not found")
        if path.suffix.lower() == ".pdf":
            return path
        output_path = settings.pdf_output_path / f"{review_id}_{index}_{artifact.id}.pdf"
        return self._converter.convert_to_pdf(path, output_path)


def _annotation_findings(findings: list[Finding]) -> list[PdfAnnotationFinding]:
    annotations: list[PdfAnnotationFinding] = []
    for index, finding in enumerate(findings, start=1):
        annotations.append(
            PdfAnnotationFinding(
                number=index,
                severity=finding.severity,
                aspect_name=finding.aspect.name if finding.aspect is not None else "-",
                location=finding.location,
                content=finding.content,
                suggestion=finding.suggestion,
            )
        )
    return annotations


def _include_pt_candidates(review: Review, artifacts: list[Artifact]) -> bool:
    return review.review_type == "single" and any(artifact.phase == "SS" for artifact in artifacts)
