from __future__ import annotations

from pathlib import Path

from app.parsers.base import ParsedArtifact, Parser
from app.parsers.docx_parser import DocxParser
from app.parsers.pdf_parser import PdfParser
from app.parsers.source_parser import SourceParser
from app.parsers.xlsx_parser import XlsxParser


class ParserRegistry:
    def __init__(self) -> None:
        source_parser = SourceParser()
        self._parsers: dict[str, Parser] = {
            "xlsx": XlsxParser(),
            "docx": DocxParser(),
            "pdf": PdfParser(),
            "source": source_parser,
            "vb": source_parser,
            "cs": source_parser,
            "java": source_parser,
            "py": source_parser,
            "js": source_parser,
            "ts": source_parser,
        }

    def parser_for(self, path: Path, file_type: str | None = None) -> Parser:
        key = (file_type or path.suffix.lower().lstrip(".")).lower()
        parser = self._parsers.get(key)
        if parser is None:
            raise ValueError(f"Unsupported parser type: {key}")
        return parser

    def parse(self, path: Path, file_type: str | None = None) -> ParsedArtifact:
        return self.parser_for(path, file_type).parse(path)
