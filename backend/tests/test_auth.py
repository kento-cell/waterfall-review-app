from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import auth_headers, create_user


@pytest.mark.asyncio
async def test_login_me_logout_success(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, email="login@example.com", password="secret123")

    response = await client.post(
        "/api/auth/login",
        json={"email": "login@example.com", "password": "secret123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 28800

    headers = {"Authorization": f"Bearer {body['access_token']}"}
    me_response = await client.get("/api/auth/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "login@example.com"

    logout_response = await client.post("/api/auth/logout", headers=headers)
    assert logout_response.status_code == 200
    assert logout_response.json() == {"message": "logged_out"}


@pytest.mark.asyncio
async def test_login_failure(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, email="fail@example.com", password="secret123")

    response = await client.post(
        "/api/auth/login",
        json={"email": "fail@example.com", "password": "wrong"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_token(client: AsyncClient) -> None:
    response = await client.get("/api/auth/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_headers_fixture(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, email="fixture@example.com")

    headers = await auth_headers(client, "fixture@example.com")

    response = await client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
