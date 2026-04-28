from __future__ import annotations

import re
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.artifact import Artifact
from app.models.project import Project

ALLOWED_EXTENSIONS = {"xlsx", "txt", "docx", "pdf", "vb", "cs", "java", "py", "js", "ts"}
SOURCE_EXTENSIONS = {"vb", "cs", "java", "py", "js", "ts"}
MIME_TYPES_BY_EXTENSION = {
    "xlsx": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/octet-stream",
    },
    "txt": {"text/plain", "application/octet-stream"},
    "docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream",
    },
    "pdf": {"application/pdf"},
    "vb": {"text/plain", "text/x-vb", "application/octet-stream"},
    "cs": {"text/plain", "text/x-csharp", "text/x-csrc", "application/octet-stream"},
    "java": {"text/plain", "text/x-java-source", "application/octet-stream"},
    "py": {"text/plain", "text/x-python", "application/octet-stream"},
    "js": {"text/plain", "text/javascript", "application/javascript", "application/octet-stream"},
    "ts": {"text/plain", "text/typescript", "application/x-typescript", "application/octet-stream"},
}
WINDOWS_RESERVED_CHARS = re.compile(r'[<>:"/\\|?*]')
SAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._ -]")


def _extension(filename: str) -> str:
    return Path(filename).suffix.lower().lstrip(".")


def _file_type(extension: str) -> str:
    if extension in SOURCE_EXTENSIONS:
        return "source"
    return extension


def _validate_phase(phase: str) -> str:
    clean_phase = phase.strip()
    if (
        not clean_phase
        or clean_phase in {".", ".."}
        or WINDOWS_RESERVED_CHARS.search(clean_phase) is not None
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid phase")
    return clean_phase


def _safe_filename(filename: str) -> str:
    original = Path(filename).name.strip()
    if not original or original in {".", ".."}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename")
    safe = SAFE_FILENAME_CHARS.sub("_", original).strip(" .")
    if not safe or safe in {".", ".."}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename")
    return safe[:255]


def _validate_upload_metadata(file: UploadFile) -> tuple[str, str]:
    filename = file.filename or ""
    extension = _extension(filename)
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file extension")

    content_type = (file.content_type or "").split(";")[0].lower()
    if content_type not in MIME_TYPES_BY_EXTENSION[extension]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported MIME type")

    return _safe_filename(filename), extension


async def _next_version(
    db: AsyncSession,
    project_id: UUID,
    phase: str,
    file_name: str,
) -> int:
    result = await db.execute(
        select(func.max(Artifact.version)).where(
            Artifact.project_id == project_id,
            Artifact.phase == phase,
            Artifact.file_name == file_name,
        )
    )
    current = result.scalar_one_or_none()
    return (current or 0) + 1


async def list_artifacts_for_project(
    db: AsyncSession,
    project_id: UUID,
    phase: str | None = None,
) -> list[Artifact]:
    statement = select(Artifact).where(Artifact.project_id == project_id)
    if phase is not None:
        statement = statement.where(Artifact.phase == phase)
    result = await db.execute(statement.order_by(Artifact.uploaded_at))
    return list(result.scalars().all())


async def create_artifact(
    db: AsyncSession,
    project_id: UUID,
    uploaded_by: UUID,
    phase: str,
    file: UploadFile,
) -> Artifact:
    clean_phase = _validate_phase(phase)
    filename, extension = _validate_upload_metadata(file)
    contents = await file.read(settings.max_upload_bytes + 1)
    if len(contents) > settings.max_upload_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")

    relative_path = Path("storage") / "projects" / str(project_id) / clean_phase / filename
    absolute_path = settings.backend_dir / relative_path
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    absolute_path.write_bytes(contents)

    artifact = Artifact(
        project_id=project_id,
        phase=clean_phase,
        file_name=filename,
        file_path=relative_path.as_posix(),
        file_type=_file_type(extension),
        version=await _next_version(db, project_id, clean_phase, filename),
        size_bytes=len(contents),
        uploaded_by=uploaded_by,
    )
    db.add(artifact)
    await db.commit()
    await db.refresh(artifact)
    return artifact


async def get_artifact_for_user(db: AsyncSession, owner_id: UUID, artifact_id: UUID) -> Artifact:
    result = await db.execute(
        select(Artifact, Project.owner_id)
        .join(Project, Artifact.project_id == Project.id)
        .where(Artifact.id == artifact_id)
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")

    artifact, project_owner_id = row
    if project_owner_id != owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Artifact access denied")
    return artifact


def get_artifact_path(artifact: Artifact) -> Path:
    path = settings.backend_dir / artifact.file_path
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact file not found")
    return path


async def delete_artifact(db: AsyncSession, artifact: Artifact) -> None:
    await db.delete(artifact)
    await db.commit()
