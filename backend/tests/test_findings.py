from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import auth_headers, create_user

PROMPT_TEMPLATE = (
    "Phase: {phase}\n"
    "Aspect: {aspect_name}\n"
    "Artifact:\n{artifact_content}\n"
    "Return JSON array."
)


async def create_project(client: AsyncClient, headers: dict[str, str], name: str = "Findings") -> str:
    response = await client.post("/api/projects", headers=headers, json={"name": name})
    assert response.status_code == 201
    return response.json()["id"]


async def create_aspect(client: AsyncClient, headers: dict[str, str], name: str = "Finding Aspect") -> str:
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


async def create_finding(client: AsyncClient, headers: dict[str, str], project_name: str) -> str:
    project_id = await create_project(client, headers, name=project_name)
    upload_response = await client.post(
        f"/api/projects/{project_id}/artifacts",
        headers=headers,
        data={"phase": "PG"},
        files={"file": ("finding_sample.py", b"print('finding')\n", "text/x-python")},
    )
    assert upload_response.status_code == 201
    aspect_id = await create_aspect(client, headers, name=f"{project_name} Aspect")
    review_response = await client.post(
        f"/api/projects/{project_id}/reviews",
        headers=headers,
        json={"artifact_id": upload_response.json()["id"], "aspect_ids": [aspect_id]},
    )
    assert review_response.status_code == 202
    findings_response = await client.get(
        f"/api/reviews/{review_response.json()['review_id']}/findings",
        headers=headers,
    )
    assert findings_response.status_code == 200
    return findings_response.json()[0]["id"]


@pytest.mark.asyncio
async def test_get_finding_detail_without_response(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await create_user(db_session, email="finding-detail@example.com")
    headers = await auth_headers(client, "finding-detail@example.com")
    finding_id = await create_finding(client, headers, "Finding Detail")

    response = await client.get(f"/api/findings/{finding_id}", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == finding_id
    assert body["response"] is None


@pytest.mark.asyncio
async def test_put_finding_response_creates_response(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await create_user(db_session, email="finding-response@example.com")
    headers = await auth_headers(client, "finding-response@example.com")
    finding_id = await create_finding(client, headers, "Finding Response")

    response = await client.put(
        f"/api/findings/{finding_id}/response",
        headers=headers,
        json={"status": "in_progress", "comment": "Checking"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["finding_id"] == finding_id
    assert body["status"] == "in_progress"
    assert body["comment"] == "Checking"


@pytest.mark.asyncio
async def test_put_finding_response_updates_existing_response(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await create_user(db_session, email="finding-response-update@example.com")
    headers = await auth_headers(client, "finding-response-update@example.com")
    finding_id = await create_finding(client, headers, "Finding Response Update")
    first_response = await client.put(
        f"/api/findings/{finding_id}/response",
        headers=headers,
        json={"status": "in_progress", "comment": "Checking"},
    )
    assert first_response.status_code == 200

    second_response = await client.put(
        f"/api/findings/{finding_id}/response",
        headers=headers,
        json={"status": "done", "comment": "Fixed"},
    )

    assert second_response.status_code == 200
    assert second_response.json()["id"] == first_response.json()["id"]
    assert second_response.json()["status"] == "done"
    assert second_response.json()["comment"] == "Fixed"


@pytest.mark.asyncio
async def test_finding_not_found_for_other_owner(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await create_user(db_session, email="finding-owner@example.com")
    await create_user(db_session, email="finding-other@example.com")
    owner_headers = await auth_headers(client, "finding-owner@example.com")
    other_headers = await auth_headers(client, "finding-other@example.com")
    finding_id = await create_finding(client, owner_headers, "Private Finding")

    response = await client.get(f"/api/findings/{finding_id}", headers=other_headers)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_finding_response_rejects_invalid_status(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await create_user(db_session, email="finding-invalid@example.com")
    headers = await auth_headers(client, "finding-invalid@example.com")
    finding_id = await create_finding(client, headers, "Finding Invalid")

    response = await client.put(
        f"/api/findings/{finding_id}/response",
        headers=headers,
        json={"status": "invalid", "comment": "Nope"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_finding_not_found(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, email="finding-404@example.com")
    headers = await auth_headers(client, "finding-404@example.com")

    response = await client.get(f"/api/findings/{uuid4()}", headers=headers)

    assert response.status_code == 404
