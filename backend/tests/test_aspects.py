from __future__ import annotations

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


@pytest.mark.asyncio
async def test_aspect_crud_success(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, email="aspect@example.com")
    headers = await auth_headers(client, "aspect@example.com")

    create_response = await client.post(
        "/api/aspects",
        headers=headers,
        json={
            "name": "Naming",
            "description": "Check naming",
            "target_phases": ["PG"],
            "prompt_template": PROMPT_TEMPLATE,
            "default_severity": "mid",
        },
    )
    assert create_response.status_code == 201
    aspect = create_response.json()
    assert aspect["name"] == "Naming"
    assert aspect["is_active"] is True

    list_response = await client.get("/api/aspects", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    update_response = await client.put(
        f"/api/aspects/{aspect['id']}",
        headers=headers,
        json={"name": "Naming Updated", "default_severity": "high"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Naming Updated"
    assert update_response.json()["default_severity"] == "high"

    delete_response = await client.delete(f"/api/aspects/{aspect['id']}", headers=headers)
    assert delete_response.status_code == 200
    assert delete_response.json() == {"message": "deleted"}

    active_response = await client.get("/api/aspects", headers=headers)
    assert active_response.status_code == 200
    assert active_response.json() == []

    all_response = await client.get("/api/aspects?include_inactive=true", headers=headers)
    assert all_response.status_code == 200
    assert all_response.json()[0]["is_active"] is False


@pytest.mark.asyncio
async def test_aspect_create_rejects_template_without_required_variables(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await create_user(db_session, email="aspect-invalid@example.com")
    headers = await auth_headers(client, "aspect-invalid@example.com")

    response = await client.post(
        "/api/aspects",
        headers=headers,
        json={
            "name": "Invalid",
            "prompt_template": "missing placeholders",
            "default_severity": "mid",
        },
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "prompt_template",
    [
        "{phase} {aspect_name} {artifact_content} {ticket_id}",
        "{phase} {aspect_name} {artifact_content} {",
        "{phase} {aspect_name}",
    ],
)
@pytest.mark.asyncio
async def test_aspect_create_rejects_invalid_prompt_template_cases(
    client: AsyncClient,
    db_session: AsyncSession,
    prompt_template: str,
) -> None:
    await create_user(db_session, email=f"aspect-invalid-{abs(hash(prompt_template))}@example.com")
    headers = await auth_headers(client, f"aspect-invalid-{abs(hash(prompt_template))}@example.com")

    response = await client.post(
        "/api/aspects",
        headers=headers,
        json={
            "name": "Invalid",
            "prompt_template": prompt_template,
            "default_severity": "mid",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_aspect_update_rejects_invalid_prompt_template(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await create_user(db_session, email="aspect-update-invalid@example.com")
    headers = await auth_headers(client, "aspect-update-invalid@example.com")
    create_response = await client.post(
        "/api/aspects",
        headers=headers,
        json={
            "name": "Valid",
            "prompt_template": PROMPT_TEMPLATE,
            "default_severity": "mid",
        },
    )
    assert create_response.status_code == 201

    response = await client.put(
        f"/api/aspects/{create_response.json()['id']}",
        headers=headers,
        json={
            "prompt_template": "{phase} {aspect_name} {artifact_content} {unknown}",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_aspect_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/aspects")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_aspect_update_not_found(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, email="aspect-404@example.com")
    headers = await auth_headers(client, "aspect-404@example.com")

    response = await client.put(
        "/api/aspects/00000000-0000-0000-0000-000000000000",
        headers=headers,
        json={"name": "Missing"},
    )

    assert response.status_code == 404
