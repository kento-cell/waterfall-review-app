from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.review_engine as review_engine_module
from app.models.artifact import Artifact
from app.models.review import Review
from app.models.user import utc_now
from app.services.review_engine import ReviewService
from tests.conftest import auth_headers, create_user

PROMPT_TEMPLATE = (
    "Phase: {phase}\n"
    "Aspect: {aspect_name}\n"
    "Artifact:\n{artifact_content}\n"
    "Return JSON array with location, severity, content, suggestion."
)


class SlowLLMClient:
    async def review_artifact(self, prompt: str) -> str:
        await asyncio.sleep(0.05)
        return "[]"


class TrackingLLMClient:
    def __init__(self) -> None:
        self.calls = 0
        self.current = 0
        self.max_seen = 0

    async def review_artifact(self, prompt: str) -> str:
        self.calls += 1
        self.current += 1
        self.max_seen = max(self.max_seen, self.current)
        try:
            await asyncio.sleep(0.02)
            return json.dumps(
                [
                    {
                        "location": "Line:1",
                        "severity": "mid",
                        "content": "Tracked finding",
                        "suggestion": "Review tracked finding.",
                    }
                ]
            )
        finally:
            self.current -= 1


async def create_project(client: AsyncClient, headers: dict[str, str], name: str = "Reviews") -> str:
    response = await client.post("/api/projects", headers=headers, json={"name": name})
    assert response.status_code == 201
    return response.json()["id"]


async def create_aspect(client: AsyncClient, headers: dict[str, str], name: str = "Naming") -> str:
    response = await client.post(
        "/api/aspects",
        headers=headers,
        json={
            "name": name,
            "target_phases": ["PG"],
            "prompt_template": PROMPT_TEMPLATE,
            "default_severity": "mid",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


async def upload_source_artifact(client: AsyncClient, headers: dict[str, str], project_id: str) -> str:
    response = await client.post(
        f"/api/projects/{project_id}/artifacts",
        headers=headers,
        data={"phase": "PG"},
        files={"file": ("review_sample.py", b"print('review')\n", "text/x-python")},
    )
    assert response.status_code == 201
    return response.json()["id"]


async def create_completed_review(
    client: AsyncClient,
    headers: dict[str, str],
    project_id: str,
    artifact_id: str,
    aspect_id: str,
) -> str:
    response = await client.post(
        f"/api/projects/{project_id}/reviews",
        headers=headers,
        json={"artifact_id": artifact_id, "aspect_ids": [aspect_id]},
    )
    assert response.status_code == 202
    return response.json()["review_id"]


@pytest.mark.asyncio
async def test_single_review_with_stub_llm_creates_findings(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await create_user(db_session, email="review@example.com")
    headers = await auth_headers(client, "review@example.com")
    project_id = await create_project(client, headers)
    artifact_id = await upload_source_artifact(client, headers, project_id)
    aspect_id = await create_aspect(client, headers)

    review_id = await create_completed_review(client, headers, project_id, artifact_id, aspect_id)

    review_response = await client.get(f"/api/reviews/{review_id}", headers=headers)
    assert review_response.status_code == 200
    assert review_response.json()["status"] == "completed"

    findings_response = await client.get(f"/api/reviews/{review_id}/findings", headers=headers)
    assert findings_response.status_code == 200
    findings = findings_response.json()
    assert len(findings) == 2
    assert {finding["severity"] for finding in findings} == {"high", "mid"}
    assert {finding["location"] for finding in findings} == {"Line:1", "Line:2"}


@pytest.mark.asyncio
async def test_review_findings_can_filter_by_severity_aspect_and_response_status(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await create_user(db_session, email="review-filter@example.com")
    headers = await auth_headers(client, "review-filter@example.com")
    project_id = await create_project(client, headers, name="Review Filters")
    artifact_id = await upload_source_artifact(client, headers, project_id)
    aspect_id = await create_aspect(client, headers, name="Filter Aspect")
    review_id = await create_completed_review(client, headers, project_id, artifact_id, aspect_id)

    high_response = await client.get(
        f"/api/reviews/{review_id}/findings?severity=high",
        headers=headers,
    )
    assert high_response.status_code == 200
    assert len(high_response.json()) == 1
    assert high_response.json()[0]["severity"] == "high"

    aspect_response = await client.get(
        f"/api/reviews/{review_id}/findings?aspect={aspect_id}",
        headers=headers,
    )
    assert aspect_response.status_code == 200
    assert len(aspect_response.json()) == 2

    not_started_response = await client.get(
        f"/api/reviews/{review_id}/findings?response_status=not_started",
        headers=headers,
    )
    assert not_started_response.status_code == 200
    assert len(not_started_response.json()) == 2


@pytest.mark.asyncio
async def test_project_review_list_returns_created_review(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await create_user(db_session, email="review-list@example.com")
    headers = await auth_headers(client, "review-list@example.com")
    project_id = await create_project(client, headers, name="Review List")
    artifact_id = await upload_source_artifact(client, headers, project_id)
    aspect_id = await create_aspect(client, headers, name="List Aspect")
    review_id = await create_completed_review(client, headers, project_id, artifact_id, aspect_id)

    response = await client.get(f"/api/projects/{project_id}/reviews", headers=headers)

    assert response.status_code == 200
    assert [review["id"] for review in response.json()] == [review_id]


@pytest.mark.asyncio
async def test_project_review_list_sorts_running_completed_and_pending(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await create_user(db_session, email="review-sort@example.com")
    headers = await auth_headers(client, "review-sort@example.com")
    project_id = UUID(await create_project(client, headers, name="Review Sort"))
    base_time = datetime(2026, 4, 28, 10, 0, tzinfo=UTC)

    pending_older = Review(
        project_id=project_id,
        review_type="single",
        target_artifact_ids=[],
        aspect_ids=[],
        status="pending",
        created_at=base_time + timedelta(minutes=1),
    )
    completed = Review(
        project_id=project_id,
        review_type="single",
        target_artifact_ids=[],
        aspect_ids=[],
        status="completed",
        started_at=base_time + timedelta(minutes=2),
        completed_at=base_time + timedelta(minutes=3),
        created_at=base_time,
    )
    pending_newer = Review(
        project_id=project_id,
        review_type="single",
        target_artifact_ids=[],
        aspect_ids=[],
        status="pending",
        created_at=base_time + timedelta(minutes=4),
    )
    running = Review(
        project_id=project_id,
        review_type="single",
        target_artifact_ids=[],
        aspect_ids=[],
        status="running",
        started_at=base_time + timedelta(minutes=5),
        created_at=base_time + timedelta(minutes=2),
    )
    db_session.add_all([pending_older, completed, pending_newer, running])
    await db_session.commit()

    response = await client.get(f"/api/projects/{project_id}/reviews", headers=headers)

    assert response.status_code == 200
    assert [review["id"] for review in response.json()] == [
        str(running.id),
        str(completed.id),
        str(pending_newer.id),
        str(pending_older.id),
    ]


@pytest.mark.asyncio
async def test_review_marks_failed_when_artifact_file_is_missing(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user(db_session, email="review-fail@example.com")
    headers = await auth_headers(client, "review-fail@example.com")
    project_id = await create_project(client, headers, name="Review Failure")
    aspect_id = await create_aspect(client, headers, name="Failure Aspect")
    artifact = Artifact(
        project_id=UUID(project_id),
        phase="PG",
        file_name="missing.py",
        file_path="storage/projects/missing/missing.py",
        file_type="source",
        version=1,
        size_bytes=0,
        uploaded_by=user.id,
    )
    db_session.add(artifact)
    await db_session.commit()
    await db_session.refresh(artifact)

    response = await client.post(
        f"/api/projects/{project_id}/reviews",
        headers=headers,
        json={"artifact_id": str(artifact.id), "aspect_ids": [aspect_id]},
    )
    assert response.status_code == 202

    review_response = await client.get(f"/api/reviews/{response.json()['review_id']}", headers=headers)
    assert review_response.status_code == 200
    body = review_response.json()
    assert body["status"] == "failed"
    assert "Artifact file not found" in body["error_message"]


@pytest.mark.asyncio
async def test_mark_stale_running_reviews_failed_updates_only_timed_out_reviews(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await create_user(db_session, email="review-stale@example.com")
    headers = await auth_headers(client, "review-stale@example.com")
    project_id = UUID(await create_project(client, headers, name="Review Stale"))

    stale_review = Review(
        project_id=project_id,
        review_type="single",
        target_artifact_ids=[],
        aspect_ids=[],
        status="running",
        started_at=utc_now() - timedelta(seconds=120),
    )
    fresh_review = Review(
        project_id=project_id,
        review_type="single",
        target_artifact_ids=[],
        aspect_ids=[],
        status="running",
        started_at=utc_now(),
    )
    db_session.add_all([stale_review, fresh_review])
    await db_session.commit()

    updated_count = await ReviewService(db_session).mark_stale_running_reviews_failed(project_id)

    assert updated_count == 1
    await db_session.refresh(stale_review)
    await db_session.refresh(fresh_review)
    assert stale_review.status == "failed"
    assert stale_review.completed_at is not None
    assert stale_review.error_message == "Review job timed out or was interrupted."
    assert fresh_review.status == "running"
    assert fresh_review.completed_at is None


@pytest.mark.asyncio
async def test_review_timeout_marks_review_failed(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await create_user(db_session, email="review-timeout@example.com")
    headers = await auth_headers(client, "review-timeout@example.com")
    project_id = await create_project(client, headers, name="Review Timeout")
    artifact_id = await upload_source_artifact(client, headers, project_id)
    aspect_id = await create_aspect(client, headers, name="Timeout Aspect")
    monkeypatch.setattr(
        review_engine_module,
        "settings",
        replace(review_engine_module.settings, review_execution_timeout_seconds=0.01),
    )

    review = await ReviewService(db_session, llm_client=SlowLLMClient()).run_single_review(
        UUID(artifact_id),
        [UUID(aspect_id)],
    )

    assert review.status == "failed"
    assert "Timeout" in (review.error_message or "")


@pytest.mark.asyncio
async def test_review_aspect_processing_is_parallel_but_bounded(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await create_user(db_session, email="review-concurrency@example.com")
    headers = await auth_headers(client, "review-concurrency@example.com")
    project_id = await create_project(client, headers, name="Review Concurrency")
    artifact_id = await upload_source_artifact(client, headers, project_id)
    aspect_ids = [
        UUID(await create_aspect(client, headers, name=f"Concurrency Aspect {index}"))
        for index in range(4)
    ]
    tracking_llm = TrackingLLMClient()
    monkeypatch.setattr(
        review_engine_module,
        "settings",
        replace(
            review_engine_module.settings,
            review_execution_timeout_seconds=2,
            review_aspect_concurrency=2,
        ),
    )

    review = await ReviewService(db_session, llm_client=tracking_llm).run_single_review(
        UUID(artifact_id),
        aspect_ids,
    )

    assert review.status == "completed"
    assert tracking_llm.calls == 4
    assert 1 < tracking_llm.max_seen <= 2


@pytest.mark.asyncio
async def test_review_not_found_for_other_owner(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await create_user(db_session, email="review-owner@example.com")
    await create_user(db_session, email="review-other@example.com")
    owner_headers = await auth_headers(client, "review-owner@example.com")
    other_headers = await auth_headers(client, "review-other@example.com")
    project_id = await create_project(client, owner_headers, name="Private Review")
    artifact_id = await upload_source_artifact(client, owner_headers, project_id)
    aspect_id = await create_aspect(client, owner_headers, name="Private Aspect")
    review_id = await create_completed_review(client, owner_headers, project_id, artifact_id, aspect_id)

    response = await client.get(f"/api/reviews/{review_id}", headers=other_headers)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_review_create_rejects_missing_aspect(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await create_user(db_session, email="review-missing-aspect@example.com")
    headers = await auth_headers(client, "review-missing-aspect@example.com")
    project_id = await create_project(client, headers, name="Missing Aspect")
    artifact_id = await upload_source_artifact(client, headers, project_id)

    response = await client.post(
        f"/api/projects/{project_id}/reviews",
        headers=headers,
        json={"artifact_id": artifact_id, "aspect_ids": [str(uuid4())]},
    )

    assert response.status_code == 404
