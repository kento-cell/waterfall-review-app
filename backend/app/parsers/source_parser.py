from __future__ import annotations

from pathlib import Path

from app.parsers.base import ParsedArtifact


class SourceParser:
    def parse(self, path: Path) -> ParsedArtifact:
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = [f"{line_no}: {line}" for line_no, line in enumerate(text.splitlines(), start=1)]
        return ParsedArtifact(content="\n".join(lines))
