from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.llm import LLMClient, get_llm_client
from app.models.artifact import Artifact
from app.models.review import Aspect, Finding, Review
from app.parsers import ParserRegistry
from app.services.aspect_parser import parse_aspect_file

VALID_SEVERITIES = {"high", "mid", "low"}


@dataclass(frozen=True)
class ReviewAspect:
    id: UUID | None
    name: str
    target: str | None
    default_severity: str
    prompt_template: str
    phase: str | None = None


class BaseReviewEngine:
    def __init__(
        self,
        db: AsyncSession,
        llm_client: LLMClient | None = None,
        parser_registry: ParserRegistry | None = None,
    ) -> None:
        self._db = db
        self._llm_client = llm_client
        self._parser_registry = parser_registry or ParserRegistry()

    def _client(self) -> LLMClient:
        return self._llm_client or get_llm_client()

    async def _get_artifact(self, artifact_id: UUID) -> Artifact:
        artifact = await self._db.get(Artifact, artifact_id)
        if artifact is None:
            raise ValueError("Artifact not found")
        return artifact

    def _artifact_path(self, artifact: Artifact) -> Path:
        path = settings.backend_dir / artifact.file_path
        if not path.is_file():
            raise ValueError("Artifact file not found")
        return path

    async def _get_active_review_aspects(self, aspect_ids: Sequence[UUID]) -> list[ReviewAspect]:
        unique_ids = list(dict.fromkeys(aspect_ids))
        if not unique_ids:
            return []
        result = await self._db.execute(
            select(Aspect).where(Aspect.id.in_(unique_ids), Aspect.is_active.is_(True))
        )
        aspects = list(result.scalars().all())
        found_ids = {aspect.id for aspect in aspects}
        missing = [str(aspect_id) for aspect_id in unique_ids if aspect_id not in found_ids]
        if missing:
            raise ValueError(f"Active aspect not found: {', '.join(missing)}")
        return [
            ReviewAspect(
                id=aspect.id,
                name=aspect.name,
                target=None,
                default_severity=aspect.default_severity,
                prompt_template=aspect.prompt_template,
                phase=None,
            )
            for aspect in aspects
        ]

    async def _get_file_review_aspects(
        self,
        aspect_artifact_id: UUID,
        target: str | None = None,
    ) -> list[ReviewAspect]:
        artifact = await self._get_artifact(aspect_artifact_id)
        parsed_aspects = parse_aspect_file(self._artifact_path(artifact))
        aspects = [
            ReviewAspect(
                id=None,
                name=parsed.name,
                target=parsed.target,
                default_severity=parsed.severity,
                prompt_template=parsed.prompt_template,
                phase=parsed.phase,
            )
            for parsed in parsed_aspects
        ]
        if target is None:
            return aspects
        filtered = [aspect for aspect in aspects if _target_matches(aspect.target, target)]
        if not filtered:
            raise ValueError(f"No aspect rows matched target {target}")
        return filtered

    def _parse_response(self, raw_response: str) -> list[dict[str, object]]:
        payload = _strip_json_fence(raw_response)
        data = json.loads(payload)
        if isinstance(data, dict) and isinstance(data.get("findings"), list):
            data = data["findings"]
        if not isinstance(data, list):
            raise ValueError("LLM response must be a JSON array")
        if not all(isinstance(item, dict) for item in data):
            raise ValueError("LLM response items must be objects")
        return data

    def _build_findings(
        self,
        review: Review,
        artifact: Artifact,
        aspect: ReviewAspect,
        raw_response: str,
    ) -> list[Finding]:
        return [
            self._build_finding(review.id, artifact.id, aspect, item)
            for item in self._parse_response(raw_response)
        ]

    def _build_finding(
        self,
        review_id: UUID,
        artifact_id: UUID | None,
        aspect: ReviewAspect,
        item: dict[str, object],
    ) -> Finding:
        severity = str(item.get("severity") or aspect.default_severity).lower()
        if severity not in VALID_SEVERITIES:
            severity = aspect.default_severity
        content = item.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Finding content is required")
        return Finding(
            review_id=review_id,
            artifact_id=artifact_id,
            location=_optional_str(item.get("location")),
            severity=severity,
            aspect_id=aspect.id,
            content=content,
            suggestion=_optional_str(item.get("suggestion")),
        )


def render_review_prompt(
    aspect: ReviewAspect,
    *,
    phase: str,
    artifact_content: str,
) -> str:
    values = {
        "phase": phase,
        "aspect_name": aspect.name,
        "artifact_content": artifact_content,
    }
    try:
        prompt = aspect.prompt_template.format(**values)
    except (KeyError, IndexError, ValueError):
        prompt = aspect.prompt_template
    if "{artifact_content}" not in aspect.prompt_template:
        prompt = f"{prompt}\n\nPhase: {phase}\nAspect: {aspect.name}\nArtifact:\n{artifact_content}"
    return prompt


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _strip_json_fence(raw_response: str) -> str:
    text = raw_response.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _target_matches(value: str | None, target: str) -> bool:
    if value is None:
        return True
    return _normalize_target(value) == _normalize_target(target)


def _normalize_target(value: str) -> str:
    return value.replace(" ", "").replace("x", "×").replace("X", "×")
