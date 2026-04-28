from __future__ import annotations

from pathlib import Path

from pdfminer.high_level import extract_text

from app.parsers.base import ParsedArtifact


class PdfParser:
    def parse(self, path: Path) -> ParsedArtifact:
        return ParsedArtifact(content=extract_text(path))
