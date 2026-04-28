from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

import fitz

from app.core.config import settings

CELL_ROW_PATTERN = re.compile(r"![A-Z]+(\d+)")
SEVERITY_LABELS = {"high": "高", "mid": "中", "low": "低"}


@dataclass(frozen=True)
class PdfAnnotationFinding:
    number: int
    severity: str
    aspect_name: str
    location: str | None
    content: str
    suggestion: str | None
    page_number: int = 0


@dataclass(frozen=True)
class FindingBoxLayout:
    index: int
    desired_y: float
    y: float
    height: float

    @property
    def bottom(self) -> float:
        return self.y + self.height


class PDFAnnotator:
    def __init__(self, findings_per_page: int | None = None) -> None:
        self._findings_per_page = findings_per_page or settings.pdf_findings_per_page

    def annotate(
        self,
        input_pdf: Path,
        output_pdf: Path,
        findings: list[PdfAnnotationFinding],
        *,
        include_pt_candidates: bool = False,
    ) -> Path:
        output_pdf.parent.mkdir(parents=True, exist_ok=True)
        doc = fitz.open(input_pdf)
        try:
            if doc.page_count == 0:
                doc.new_page()
            self._annotate_findings(doc, findings)
            self._append_summary_page(doc, findings)
            if include_pt_candidates:
                self._append_pt_candidate_page(doc, findings)
            doc.save(output_pdf, garbage=4, deflate=True)
            return output_pdf
        finally:
            doc.close()

    def _annotate_findings(self, doc: fitz.Document, findings: list[PdfAnnotationFinding]) -> None:
        if not findings:
            return

        max_per_page = max(1, self._findings_per_page)
        for chunk_index, start in enumerate(range(0, len(findings), max_per_page)):
            chunk = findings[start : start + max_per_page]
            page = self._page_for_chunk(doc, chunk_index)
            desired_ys = [
                _desired_box_y(page.rect, finding.location, local_index)
                for local_index, finding in enumerate(chunk)
            ]
            layouts = layout_finding_boxes(
                desired_ys,
                top=48,
                bottom=page.rect.height - 48,
                height=68,
                gap=8,
            )
            layouts_by_index = {layout.index: layout for layout in layouts}
            for local_index, finding in enumerate(chunk):
                layout = layouts_by_index[local_index]
                badge_point = _badge_point(page.rect, finding.location, local_index)
                box_rect = _box_rect(page.rect, layout.y, layout.height)
                _draw_badge(page, badge_point, finding.number)
                _draw_dashed_line(page, badge_point, fitz.Point(box_rect.x0, box_rect.y0 + 12))
                _draw_finding_box(page, box_rect, finding)

    def _page_for_chunk(self, doc: fitz.Document, chunk_index: int) -> fitz.Page:
        if chunk_index < doc.page_count:
            return doc[chunk_index]
        first = doc[0]
        page = doc.new_page(width=first.rect.width, height=first.rect.height)
        page.insert_text((48, 48), "追加指摘", fontsize=14, fontname="helv")
        return page

    def _append_summary_page(
        self,
        doc: fitz.Document,
        findings: list[PdfAnnotationFinding],
    ) -> None:
        first = doc[0]
        page = doc.new_page(width=first.rect.width, height=first.rect.height)
        y = 48
        page.insert_text((48, y), "レビュー指摘サマリ", fontsize=16, fontname="helv")
        y += 28
        headers = "# / 重要度 / 観点 / 位置 / 内容 / 修正案"
        page.insert_text((48, y), headers, fontsize=9, fontname="helv")
        y += 16
        for finding in findings:
            if y > page.rect.height - 48:
                break
            text = (
                f"{finding.number}. {SEVERITY_LABELS.get(finding.severity, finding.severity)} / "
                f"{finding.aspect_name} / {finding.location or '-'} / "
                f"{finding.content} / {finding.suggestion or '-'}"
            )
            page.insert_textbox(
                fitz.Rect(48, y, page.rect.width - 48, y + 30),
                text,
                fontsize=8,
                fontname="helv",
            )
            y += 32

    def _append_pt_candidate_page(
        self,
        doc: fitz.Document,
        findings: list[PdfAnnotationFinding],
    ) -> None:
        first = doc[0]
        page = doc.new_page(width=first.rect.width, height=first.rect.height)
        page.insert_text((48, 48), "PT項目候補", fontsize=16, fontname="helv")
        y = 82
        if not findings:
            page.insert_text((48, y), "候補なし", fontsize=10, fontname="helv")
            return
        for finding in findings[:20]:
            if y > page.rect.height - 48:
                break
            text = f"{finding.number}. {finding.content}"
            page.insert_textbox(
                fitz.Rect(48, y, page.rect.width - 48, y + 24),
                text,
                fontsize=9,
                fontname="helv",
            )
            y += 26


def layout_finding_boxes(
    desired_ys: list[float],
    *,
    top: float,
    bottom: float,
    height: float,
    gap: float,
) -> list[FindingBoxLayout]:
    if not desired_ys:
        return []
    ordered = sorted(enumerate(desired_ys), key=lambda item: item[1])
    placed: list[tuple[int, float, float]] = []
    cursor = top
    for index, desired_y in ordered:
        y = max(top, min(desired_y, bottom - height))
        y = max(y, cursor)
        placed.append((index, desired_y, y))
        cursor = y + height + gap

    overflow = placed[-1][2] + height - bottom
    if overflow > 0:
        placed = [(index, desired_y, y - overflow) for index, desired_y, y in placed]

    adjusted: list[FindingBoxLayout] = []
    cursor = top
    for index, desired_y, y in placed:
        y = max(top, y, cursor)
        adjusted.append(FindingBoxLayout(index=index, desired_y=desired_y, y=y, height=height))
        cursor = y + height + gap
    return adjusted


def _desired_box_y(rect: fitz.Rect, location: str | None, index: int) -> float:
    badge_y = _badge_point(rect, location, index).y
    return badge_y - 18


def _badge_point(rect: fitz.Rect, location: str | None, index: int) -> fitz.Point:
    margin_width = _margin_width(rect)
    row = _row_from_location(location)
    if row is None:
        y = 72 + index * 64
    else:
        y = 48 + min(row, 45) * 12
    y = max(48, min(y, rect.height - 48))
    return fitz.Point(rect.width - margin_width - 18, y)


def _box_rect(rect: fitz.Rect, y: float, height: float) -> fitz.Rect:
    margin_width = _margin_width(rect)
    return fitz.Rect(rect.width - margin_width + 6, y, rect.width - 12, y + height)


def _margin_width(rect: fitz.Rect) -> float:
    return min(210, max(160, rect.width * 0.32))


def _row_from_location(location: str | None) -> int | None:
    if not location:
        return None
    match = CELL_ROW_PATTERN.search(location)
    if match is None:
        return None
    return int(match.group(1))


def _draw_badge(page: fitz.Page, point: fitz.Point, number: int) -> None:
    page.draw_circle(point, 9, color=(0.7, 0.2, 0.1), fill=(1, 0.92, 0.35), width=1)
    page.insert_textbox(
        fitz.Rect(point.x - 8, point.y - 6, point.x + 8, point.y + 7),
        _circled_number(number),
        fontsize=8,
        fontname="helv",
        align=fitz.TEXT_ALIGN_CENTER,
    )


def _draw_finding_box(page: fitz.Page, rect: fitz.Rect, finding: PdfAnnotationFinding) -> None:
    page.draw_rect(rect, color=(0.65, 0.3, 0.1), fill=(1, 0.98, 0.88), width=0.8)
    text = (
        f"{_circled_number(finding.number)}"
        f"{SEVERITY_LABELS.get(finding.severity, finding.severity)} "
        f"{finding.aspect_name}\n"
        f"位置: {finding.location or '-'}\n"
        f"内容: {finding.content}\n"
        f"修正案: {finding.suggestion or '-'}"
    )
    page.insert_textbox(
        rect + (5, 4, -5, -4),
        text,
        fontsize=7.5,
        fontname="helv",
        color=(0.15, 0.12, 0.08),
    )


def _draw_dashed_line(page: fitz.Page, start: fitz.Point, end: fitz.Point) -> None:
    dx = end.x - start.x
    dy = end.y - start.y
    length = math.hypot(dx, dy)
    if length <= 0:
        return
    dash = 5.0
    gap = 3.0
    ux = dx / length
    uy = dy / length
    distance = 0.0
    while distance < length:
        segment_end = min(distance + dash, length)
        p1 = fitz.Point(start.x + ux * distance, start.y + uy * distance)
        p2 = fitz.Point(start.x + ux * segment_end, start.y + uy * segment_end)
        page.draw_line(p1, p2, color=(0.7, 0.2, 0.1), width=0.7)
        distance += dash + gap


def _circled_number(number: int) -> str:
    if 1 <= number <= 20:
        return chr(0x245F + number)
    return f"({number})"
