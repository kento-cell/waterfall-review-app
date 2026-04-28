from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import auth_headers, create_user


async def create_project(client: AsyncClient, headers: dict[str, str], name: str = "Artifacts") -> str:
    response = await client.post("/api/projects", headers=headers, json={"name": name})
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.asyncio
async def test_artifact_crud_success(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, email="artifact@example.com")
    headers = await auth_headers(client, "artifact@example.com")
    project_id = await create_project(client, headers)

    upload_response = await client.post(
        f"/api/projects/{project_id}/artifacts",
        headers=headers,
        data={"phase": "PG"},
        files={"file": ("sample.py", b"print('ok')\n", "text/x-python")},
    )
    assert upload_response.status_code == 201
    artifact = upload_response.json()
    assert artifact["file_name"] == "sample.py"
    assert artifact["file_type"] == "source"
    assert artifact["size_bytes"] == len(b"print('ok')\n")
    assert artifact["file_path"].startswith(f"storage/projects/{project_id}/PG/")

    list_response = await client.get(f"/api/projects/{project_id}/artifacts", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = await client.get(f"/api/artifacts/{artifact['id']}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == artifact["id"]

    download_response = await client.get(f"/api/artifacts/{artifact['id']}/download", headers=headers)
    assert download_response.status_code == 200
    assert download_response.content == b"print('ok')\n"

    delete_response = await client.delete(f"/api/artifacts/{artifact['id']}", headers=headers)
    assert delete_response.status_code == 200
    assert delete_response.json() == {"message": "deleted"}

    missing_response = await client.get(f"/api/artifacts/{artifact['id']}", headers=headers)
    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_artifact_upload_rejects_extension(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await create_user(db_session, email="reject@example.com")
    headers = await auth_headers(client, "reject@example.com")
    project_id = await create_project(client, headers, name="Reject")

    response = await client.post(
        f"/api/projects/{project_id}/artifacts",
        headers=headers,
        data={"phase": "PG"},
        files={"file": ("sample.exe", b"binary", "application/octet-stream")},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_artifact_forbidden_for_other_owner(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await create_user(db_session, email="artifact-owner@example.com")
    await create_user(db_session, email="artifact-other@example.com")
    owner_headers = await auth_headers(client, "artifact-owner@example.com")
    other_headers = await auth_headers(client, "artifact-other@example.com")
    project_id = await create_project(client, owner_headers, name="Private Artifacts")

    upload_response = await client.post(
        f"/api/projects/{project_id}/artifacts",
        headers=owner_headers,
        data={"phase": "PG"},
        files={"file": ("private.py", b"print('private')\n", "text/x-python")},
    )
    artifact_id = upload_response.json()["id"]

    response = await client.get(f"/api/artifacts/{artifact_id}", headers=other_headers)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_artifact_not_found(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, email="artifact-404@example.com")
    headers = await auth_headers(client, "artifact-404@example.com")

    response = await client.get(f"/api/artifacts/{uuid4()}", headers=headers)

    assert response.status_code == 404
