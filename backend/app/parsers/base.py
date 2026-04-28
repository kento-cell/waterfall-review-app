from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class ParsedArtifact:
    content: str


class Parser(Protocol):
    def parse(self, path: Path) -> ParsedArtifact:
        """Extract text from an artifact without modifying it."""
