from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import fitz

from app.services.pdf_annotator import (
    PDFAnnotator,
    PdfAnnotationFinding,
    layout_finding_boxes,
)

TEST_DIR = Path(__file__).resolve().parents[1] / "storage" / "phase4_tests"


def _path(name: str) -> Path:
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    return TEST_DIR / f"{uuid4()}_{name}"


def _blank_pdf() -> Path:
    path = _path("blank.pdf")
    doc = fitz.open()
    try:
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 72), "source", fontsize=12)
        doc.save(path)
    finally:
        doc.close()
    return path


def _findings(count: int) -> list[PdfAnnotationFinding]:
    return [
        PdfAnnotationFinding(
            number=index,
            severity="high" if index == 1 else "mid",
            aspect_name="観点",
            location=f"UI:Sheet1!A{index}",
            content=f"指摘 {index}",
            suggestion=f"修正 {index}",
        )
        for index in range(1, count + 1)
    ]


def _page_count(path: Path) -> int:
    doc = fitz.open(path)
    try:
        return doc.page_count
    finally:
        doc.close()


def test_layout_finding_boxes_avoids_overlap_for_clustered_y_values() -> None:
    layouts = layout_finding_boxes([100, 102, 104], top=50, bottom=400, height=60, gap=8)

    assert layouts[1].y >= layouts[0].bottom + 8
    assert layouts[2].y >= layouts[1].bottom + 8


def test_layout_finding_boxes_keeps_y_order_by_desired_position() -> None:
    layouts = layout_finding_boxes([250, 50, 150], top=40, bottom=500, height=50, gap=10)

    assert [layout.index for layout in layouts] == [1, 2, 0]


def test_layout_finding_boxes_shifts_up_when_bottom_would_overflow() -> None:
    layouts = layout_finding_boxes([350, 360, 370], top=40, bottom=430, height=80, gap=10)

    assert layouts[-1].bottom <= 430
    assert layouts[0].y >= 40


def test_layout_finding_boxes_returns_empty_for_no_findings() -> None:
    assert layout_finding_boxes([], top=0, bottom=100, height=20, gap=2) == []


def test_pdf_annotator_adds_summary_page() -> None:
    input_pdf = _blank_pdf()
    output_pdf = _path("annotated.pdf")

    PDFAnnotator().annotate(input_pdf, output_pdf, _findings(2))

    assert output_pdf.is_file()
    assert _page_count(output_pdf) == 2


def test_pdf_annotator_adds_pt_candidate_page_when_requested() -> None:
    input_pdf = _blank_pdf()
    output_pdf = _path("annotated_pt.pdf")

    PDFAnnotator().annotate(input_pdf, output_pdf, _findings(1), include_pt_candidates=True)

    assert _page_count(output_pdf) == 3


def test_pdf_annotator_handles_no_findings_with_summary_only() -> None:
    input_pdf = _blank_pdf()
    output_pdf = _path("annotated_empty.pdf")

    PDFAnnotator().annotate(input_pdf, output_pdf, [])

    assert _page_count(output_pdf) == 2


def test_pdf_annotator_creates_extra_annotation_page_for_more_than_page_limit() -> None:
    input_pdf = _blank_pdf()
    output_pdf = _path("annotated_many.pdf")

    PDFAnnotator(findings_per_page=8).annotate(input_pdf, output_pdf, _findings(9))

    assert _page_count(output_pdf) == 3
