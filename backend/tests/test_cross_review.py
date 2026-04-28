from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.artifact import Artifact
from app.models.project import Project
from app.models.review import Finding, Review
from app.services.cross_review_engine import CrossReviewEngine
from tests.conftest import auth_headers, create_user

TEST_DIR = settings.backend_dir / "storage" / "phase4_tests"


class CapturingCrossLLM:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    async def review_artifact(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return json.dumps(
            [
                {
                    "location": "UI:Sheet1!A23 ↔ SS:Sheet3!行42-58",
                    "severity": "high",
                    "content": "UI の項目が SS に反映されていない",
                    "suggestion": "SS に該当処理を追加する",
                }
            ],
            ensure_ascii=False,
        )


def _write_storage_file(name: str, content: str) -> Path:
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    path = TEST_DIR / f"{uuid4()}_{name}"
    path.write_text(content, encoding="utf-8")
    return path


async def _project(db_session: AsyncSession, owner_id: UUID) -> Project:
    project = Project(owner_id=owner_id, name=f"Cross {uuid4()}")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


async def _artifact(
    db_session: AsyncSession,
    project: Project,
    phase: str,
    filename: str,
    content: str,
    file_type: str = "source",
) -> Artifact:
    path = _write_storage_file(filename, content)
    artifact = Artifact(
        project_id=project.id,
        phase=phase,
        file_name=path.name,
        file_path=path.relative_to(settings.backend_dir).as_posix(),
        file_type=file_type,
        version=1,
        size_bytes=path.stat().st_size,
    )
    db_session.add(artifact)
    await db_session.commit()
    await db_session.refresh(artifact)
    return artifact


@pytest.mark.asyncio
async def test_cross_review_engine_uses_ui_ss_content_and_dynamic_aspect(
    db_session: AsyncSession,
) -> None:
    user = await create_user(db_session, email="cross-engine@example.com")
    project = await _project(db_session, user.id)
    ui = await _artifact(db_session, project, "UI", "ui.py", "print('ui field')\n")
    ss = await _artifact(db_session, project, "SS", "ss.py", "print('ss process')\n")
    aspect = await _artifact(
        db_session,
        project,
        "観点",
        "aspect.txt",
        "観点名|対象|重要度|工程|レビュー指示文\n整合性|UI×SS|高|詳細設計|対応漏れを確認\n",
        "txt",
    )
    llm = CapturingCrossLLM()

    review = await CrossReviewEngine(db_session, llm_client=llm).run_cross_review(
        ui.id,
        ss.id,
        [],
        aspect_artifact_id=aspect.id,
    )

    assert review.status == "completed"
    assert "以下の UI と SS" in llm.prompts[0]
    assert "print('ui field')" in llm.prompts[0]
    assert "print('ss process')" in llm.prompts[0]
    findings = (await db_session.execute(select(Finding).where(Finding.review_id == review.id))).scalars().all()
    assert len(findings) == 1
    assert findings[0].location == "UI:Sheet1!A23 ↔ SS:Sheet3!行42-58"


@pytest.mark.asyncio
async def test_cross_review_engine_uses_default_aspect_when_none_is_supplied(
    db_session: AsyncSession,
) -> None:
    user = await create_user(db_session, email="cross-default@example.com")
    project = await _project(db_session, user.id)
    ui = await _artifact(db_session, project, "UI", "ui.py", "ui\n")
    ss = await _artifact(db_session, project, "SS", "ss.py", "ss\n")

    review = await CrossReviewEngine(db_session, llm_client=CapturingCrossLLM()).run_cross_review(
        ui.id,
        ss.id,
        [],
    )

    assert review.status == "completed"
    findings = (await db_session.execute(select(Finding).where(Finding.review_id == review.id))).scalars().all()
    assert len(findings) == 1


@pytest.mark.asyncio
async def test_cross_review_engine_marks_failed_when_target_file_is_missing(
    db_session: AsyncSession,
) -> None:
    user = await create_user(db_session, email="cross-fail@example.com")
    project = await _project(db_session, user.id)
    ui = await _artifact(db_session, project, "UI", "ui.py", "ui\n")
    ss = Artifact(
        project_id=project.id,
        phase="SS",
        file_name="missing.py",
        file_path="storage/phase4_tests/missing.py",
        file_type="source",
        version=1,
        size_bytes=0,
    )
    db_session.add(ss)
    await db_session.commit()
    await db_session.refresh(ss)

    review = await CrossReviewEngine(db_session, llm_client=CapturingCrossLLM()).run_cross_review(
        ui.id,
        ss.id,
        [],
    )

    assert review.status == "failed"
    assert "Artifact file not found" in (review.error_message or "")


@pytest.mark.asyncio
async def test_cross_review_api_runs_with_aspect_artifact(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await create_user(db_session, email="cross-api@example.com")
    headers = await auth_headers(client, "cross-api@example.com")
    project_response = await client.post("/api/projects", headers=headers, json={"name": "Cross API"})
    project_id = project_response.json()["id"]
    aspect_response = await client.post(
        f"/api/projects/{project_id}/artifacts",
        headers=headers,
        data={"phase": "観点"},
        files={
            "file": (
                "aspect.txt",
                b"\xe8\xa6\xb3\xe7\x82\xb9\xe5\x90\x8d|\xe5\xaf\xbe\xe8\xb1\xa1|\xe9\x87\x8d\xe8\xa6\x81\xe5\xba\xa6|\xe5\xb7\xa5\xe7\xa8\x8b|\xe3\x83\xac\xe3\x83\x93\xe3\x83\xa5\xe3\x83\xbc\xe6\x8c\x87\xe7\xa4\xba\xe6\x96\x87\n"
                b"\xe6\x95\xb4\xe5\x90\x88\xe6\x80\xa7|UI\xc3\x97SS|\xe9\xab\x98|\xe8\xa9\xb3\xe7\xb4\xb0\xe8\xa8\xad\xe8\xa8\x88|\xe5\xaf\xbe\xe5\xbf\x9c\xe6\xbc\x8f\xe3\x82\x8c\xe3\x82\x92\xe7\xa2\xba\xe8\xaa\x8d\n",
                "text/plain",
            )
        },
    )
    ui_response = await client.post(
        f"/api/projects/{project_id}/artifacts",
        headers=headers,
        data={"phase": "UI"},
        files={"file": ("ui.py", b"print('ui')\n", "text/x-python")},
    )
    ss_response = await client.post(
        f"/api/projects/{project_id}/artifacts",
        headers=headers,
        data={"phase": "SS"},
        files={"file": ("ss.py", b"print('ss')\n", "text/x-python")},
    )

    response = await client.post(
        f"/api/projects/{project_id}/reviews",
        headers=headers,
        json={
            "review_type": "cross",
            "target_artifact_ids": [ui_response.json()["id"], ss_response.json()["id"]],
            "aspect_artifact_id": aspect_response.json()["id"],
        },
    )

    assert response.status_code == 202
    review = await db_session.get(Review, UUID(response.json()["review_id"]))
    assert review is not None
    assert review.status == "completed"
    assert review.review_type == "cross"


@pytest.mark.asyncio
async def test_cross_review_api_rejects_missing_second_target(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await create_user(db_session, email="cross-reject@example.com")
    headers = await auth_headers(client, "cross-reject@example.com")
    project_response = await client.post("/api/projects", headers=headers, json={"name": "Cross Reject"})
    project_id = project_response.json()["id"]
    ui_response = await client.post(
        f"/api/projects/{project_id}/artifacts",
        headers=headers,
        data={"phase": "UI"},
        files={"file": ("ui.py", b"print('ui')\n", "text/x-python")},
    )

    response = await client.post(
        f"/api/projects/{project_id}/reviews",
        headers=headers,
        json={"review_type": "cross", "target_artifact_ids": [ui_response.json()["id"]]},
    )

    assert response.status_code == 400
