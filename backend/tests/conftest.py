from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from uuid import UUID

import pytest_asyncio
from fastapi import BackgroundTasks
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

os.environ["LLM_PROVIDER"] = "stub"

from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.main import app
from app.models.user import User
from app.services.cross_review_engine import CrossReviewEngine
from app.services.job_runner import get_job_runner
from app.services.pdf_generation import PDFGenerationService
from app.services.review_engine import ReviewService


class InlineJobRunner:
    def __init__(self, db_session: AsyncSession) -> None:
        self._db_session = db_session

    def enqueue_single_review(
        self,
        background_tasks: BackgroundTasks,
        review_id: UUID,
        artifact_id: UUID,
        aspect_ids: list[UUID],
        aspect_artifact_id: UUID | None = None,
    ) -> str:
        background_tasks.add_task(self._run, review_id, artifact_id, aspect_ids, aspect_artifact_id)
        return str(review_id)

    def enqueue_cross_review(
        self,
        background_tasks: BackgroundTasks,
        review_id: UUID,
        ui_artifact_id: UUID,
        ss_artifact_id: UUID,
        aspect_ids: list[UUID],
        aspect_artifact_id: UUID | None = None,
    ) -> str:
        background_tasks.add_task(
            self._run_cross,
            review_id,
            ui_artifact_id,
            ss_artifact_id,
            aspect_ids,
            aspect_artifact_id,
        )
        return str(review_id)

    def enqueue_pdf_generation(
        self,
        background_tasks: BackgroundTasks,
        review_id: UUID,
    ) -> str:
        background_tasks.add_task(self._run_pdf_generation, review_id)
        return str(review_id)

    async def _run(
        self,
        review_id: UUID,
        artifact_id: UUID,
        aspect_ids: list[UUID],
        aspect_artifact_id: UUID | None,
    ) -> None:
        await ReviewService(self._db_session).run_single_review(
            artifact_id,
            aspect_ids,
            review_id=review_id,
            aspect_artifact_id=aspect_artifact_id,
        )

    async def _run_cross(
        self,
        review_id: UUID,
        ui_artifact_id: UUID,
        ss_artifact_id: UUID,
        aspect_ids: list[UUID],
        aspect_artifact_id: UUID | None,
    ) -> None:
        await CrossReviewEngine(self._db_session).run_cross_review(
            ui_artifact_id,
            ss_artifact_id,
            aspect_ids,
            review_id=review_id,
            aspect_artifact_id=aspect_artifact_id,
        )

    async def _run_pdf_generation(self, review_id: UUID) -> None:
        await PDFGenerationService(self._db_session).generate_pdf(review_id)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_job_runner] = lambda: InlineJobRunner(db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
    app.dependency_overrides.clear()


async def create_user(
    db_session: AsyncSession,
    email: str = "user@example.com",
    password: str = "password123",
    display_name: str = "Test User",
    role: str = "general",
) -> User:
    user = User(
        email=email,
        password_hash=get_password_hash(password),
        display_name=display_name,
        role=role,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def auth_headers(client: AsyncClient, email: str, password: str = "password123") -> dict[str, str]:
    response = await client.post("/api/auth/login", json={"email": email, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
