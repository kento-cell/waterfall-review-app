from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import auth_headers, create_user


@pytest.mark.asyncio
async def test_project_crud_success(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, email="owner@example.com")
    headers = await auth_headers(client, "owner@example.com")

    create_response = await client.post(
        "/api/projects",
        headers=headers,
        json={"name": "Project A", "description": "Initial"},
    )
    assert create_response.status_code == 201
    project = create_response.json()
    assert project["name"] == "Project A"
    assert project["phases"] == ["要件定義", "基本設計", "詳細設計", "PG", "UT", "IT", "ST"]

    list_response = await client.get("/api/projects", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = await client.get(f"/api/projects/{project['id']}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == project["id"]

    update_response = await client.put(
        f"/api/projects/{project['id']}",
        headers=headers,
        json={"name": "Project A Updated", "phases": ["PG", "UT"]},
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Project A Updated"
    assert update_response.json()["phases"] == ["PG", "UT"]

    delete_response = await client.delete(f"/api/projects/{project['id']}", headers=headers)
    assert delete_response.status_code == 200
    assert delete_response.json() == {"message": "deleted"}

    missing_response = await client.get(f"/api/projects/{project['id']}", headers=headers)
    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_project_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/projects")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_project_not_found(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, email="notfound@example.com")
    headers = await auth_headers(client, "notfound@example.com")

    response = await client.get(f"/api/projects/{uuid4()}", headers=headers)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_project_forbidden_for_other_owner(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await create_user(db_session, email="owner1@example.com")
    await create_user(db_session, email="owner2@example.com")
    owner_headers = await auth_headers(client, "owner1@example.com")
    other_headers = await auth_headers(client, "owner2@example.com")

    create_response = await client.post(
        "/api/projects",
        headers=owner_headers,
        json={"name": "Private Project"},
    )
    project_id = create_response.json()["id"]

    response = await client.get(f"/api/projects/{project_id}", headers=other_headers)

    assert response.status_code == 403
