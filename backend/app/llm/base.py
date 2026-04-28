from __future__ import annotations

from typing import Protocol


class LLMClient(Protocol):
    async def review_artifact(self, prompt: str) -> str:
        """Return review findings as a JSON string."""
