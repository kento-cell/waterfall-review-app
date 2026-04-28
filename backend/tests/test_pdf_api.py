from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import fitz
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.artifact import Artifact
from app.models.project import Project
from app.models.review import Finding, Review
from tests.conftest import auth_headers, create_user

TEST_DIR = settings.backend_dir / "storage" / "phase4_tests"


def _write_pdf(name: str = "source.pdf") -> Path:
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    path = TEST_DIR / f"{uuid4()}_{name}"
    doc = fitz.open()
    try:
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 72), "pdf api source", fontsize=12)
        doc.save(path)
    finally:
        doc.close()
    return path


async def _project(db_session: AsyncSession, owner_id: UUID) -> Project:
    project = Project(owner_id=owner_id, name=f"PDF {uuid4()}")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


async def _pdf_artifact(db_session: AsyncSession, project: Project, missing: bool = False) -> Artifact:
    path = TEST_DIR / f"{uuid4()}_missing.pdf" if missing else _write_pdf()
    artifact = Artifact(
        project_id=project.id,
        phase="UI",
        file_name=path.name,
        file_path=path.relative_to(settings.backend_dir).as_posix(),
        file_type="pdf",
        version=1,
        size_bytes=0 if missing else path.stat().st_size,
    )
    db_session.add(artifact)
    await db_session.commit()
    await db_session.refresh(artifact)
    return artifact


async def _review(
    db_session: AsyncSession,
    project: Project,
    artifact: Artifact,
    review_status: str = "completed",
) -> Review:
    review = Review(
        project_id=project.id,
        review_type="single",
        target_artifact_ids=[str(artifact.id)],
        aspect_ids=[],
        status=review_status,
    )
    db_session.add(review)
    await db_session.commit()
    await db_session.refresh(review)
    if review_status == "completed":
        db_session.add(
            Finding(
                review_id=review.id,
                artifact_id=artifact.id,
                location="UI:Sheet1!A3",
                severity="high",
                content="PDF API finding",
                suggestion="PDF API suggestion",
            )
        )
        await db_session.commit()
    return review


@pytest.mark.asyncio
async def test_pdf_status_defaults_to_pending(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user(db_session, email="pdf-status@example.com")
    headers = await auth_headers(client, "pdf-status@example.com")
    project = await _project(db_session, user.id)
    artifact = await _pdf_artifact(db_session, project)
    review = await _review(db_session, project, artifact)

    response = await client.get(f"/api/reviews/{review.id}/pdf_status", headers=headers)

    assert response.status_code == 200
    assert response.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_pdf_download_returns_conflict_before_generation(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user(db_session, email="pdf-conflict@example.com")
    headers = await auth_headers(client, "pdf-conflict@example.com")
    project = await _project(db_session, user.id)
    artifact = await _pdf_artifact(db_session, project)
    review = await _review(db_session, project, artifact)

    response = await client.get(f"/api/reviews/{review.id}/pdf", headers=headers)

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_generate_pdf_creates_downloadable_pdf(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user(db_session, email="pdf-generate@example.com")
    headers = await auth_headers(client, "pdf-generate@example.com")
    project = await _project(db_session, user.id)
    artifact = await _pdf_artifact(db_session, project)
    review = await _review(db_session, project, artifact)

    generate_response = await client.post(f"/api/reviews/{review.id}/generate_pdf", headers=headers)
    status_response = await client.get(f"/api/reviews/{review.id}/pdf_status", headers=headers)
    download_response = await client.get(f"/api/reviews/{review.id}/pdf", headers=headers)

    assert generate_response.status_code == 202
    assert status_response.json()["status"] == "completed"
    assert download_response.status_code == 200
    assert download_response.headers["content-type"].startswith("application/pdf")


@pytest.mark.asyncio
async def test_generate_pdf_rejects_incomplete_review(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user(db_session, email="pdf-incomplete@example.com")
    headers = await auth_headers(client, "pdf-incomplete@example.com")
    project = await _project(db_session, user.id)
    artifact = await _pdf_artifact(db_session, project)
    review = await _review(db_session, project, artifact, review_status="running")

    response = await client.post(f"/api/reviews/{review.id}/generate_pdf", headers=headers)

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_pdf_download_returns_conflict_when_completed_file_is_missing(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user(db_session, email="pdf-missing-file@example.com")
    headers = await auth_headers(client, "pdf-missing-file@example.com")
    project = await _project(db_session, user.id)
    artifact = await _pdf_artifact(db_session, project)
    review = await _review(db_session, project, artifact)
    review.pdf_status = "completed"
    review.pdf_path = "storage/pdfs/not-created.pdf"
    await db_session.commit()

    response = await client.get(f"/api/reviews/{review.id}/pdf", headers=headers)

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_generate_pdf_marks_failed_when_artifact_file_is_missing(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user(db_session, email="pdf-failed@example.com")
    headers = await auth_headers(client, "pdf-failed@example.com")
    project = await _project(db_session, user.id)
    artifact = await _pdf_artifact(db_session, project, missing=True)
    review = await _review(db_session, project, artifact)

    response = await client.post(f"/api/reviews/{review.id}/generate_pdf", headers=headers)
    status_response = await client.get(f"/api/reviews/{review.id}/pdf_status", headers=headers)

    assert response.status_code == 202
    assert status_response.json()["status"] == "failed"
    assert "Artifact file not found" in status_response.json()["error_message"]
