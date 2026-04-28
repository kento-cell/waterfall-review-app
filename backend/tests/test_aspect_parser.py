from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from openpyxl import Workbook

from app.services.aspect_parser import parse_aspect_file, parse_excel_aspects, parse_txt_aspects

TEST_DIR = Path(__file__).resolve().parents[1] / "storage" / "phase4_tests"


def _path(name: str) -> Path:
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    return TEST_DIR / f"{uuid4()}_{name}"


def _write_excel(rows: list[list[object]], sheet_name: str = "観点") -> Path:
    path = _path("aspects.xlsx")
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_name
    for row in rows:
        sheet.append(row)
    workbook.save(path)
    return path


def test_excel_aspect_parser_parses_valid_rows() -> None:
    path = _write_excel(
        [
            ["観点名", "対象", "重要度", "工程", "レビュー指示文"],
            ["必須項目欠落", "UI", "高", "基本設計", "必須項目を確認"],
            ["型不整合", "SS", "中", "詳細設計", "データ型を確認"],
        ]
    )

    aspects = parse_excel_aspects(path)

    assert [aspect.name for aspect in aspects] == ["必須項目欠落", "型不整合"]
    assert [aspect.target for aspect in aspects] == ["UI", "SS"]
    assert [aspect.severity for aspect in aspects] == ["high", "mid"]


def test_excel_aspect_parser_skips_blank_rows() -> None:
    path = _write_excel(
        [
            ["観点名", "対象", "重要度", "工程", "レビュー指示文"],
            [None, None, None, None, None],
            ["用語統一", "UI×SS", "低", "基本設計", "用語差異を確認"],
        ]
    )

    aspects = parse_excel_aspects(path)

    assert len(aspects) == 1
    assert aspects[0].target == "UI×SS"
    assert aspects[0].severity == "low"


def test_excel_aspect_parser_requires_sheet_named_aspect() -> None:
    path = _write_excel([["観点名", "対象", "重要度", "工程", "レビュー指示文"]], "Other")

    with pytest.raises(ValueError, match='sheet "観点"'):
        parse_excel_aspects(path)


def test_excel_aspect_parser_reports_bad_header_cell() -> None:
    path = _write_excel([["名前", "対象", "重要度", "工程", "レビュー指示文"]])

    with pytest.raises(ValueError, match="row 1 column A"):
        parse_excel_aspects(path)


def test_excel_aspect_parser_reports_missing_required_cell() -> None:
    path = _write_excel(
        [
            ["観点名", "対象", "重要度", "工程", "レビュー指示文"],
            ["", "UI", "高", "基本設計", "必須項目を確認"],
        ]
    )

    with pytest.raises(ValueError, match="row 2 column A"):
        parse_excel_aspects(path)


def test_excel_aspect_parser_reports_invalid_target() -> None:
    path = _write_excel(
        [
            ["観点名", "対象", "重要度", "工程", "レビュー指示文"],
            ["対象外", "PG", "高", "基本設計", "確認"],
        ]
    )

    with pytest.raises(ValueError, match="target must be one of"):
        parse_excel_aspects(path)


def test_excel_aspect_parser_reports_invalid_severity() -> None:
    path = _write_excel(
        [
            ["観点名", "対象", "重要度", "工程", "レビュー指示文"],
            ["重要度不正", "UI", "緊急", "基本設計", "確認"],
        ]
    )

    with pytest.raises(ValueError, match="severity must be one of"):
        parse_excel_aspects(path)


def test_excel_aspect_parser_rejects_empty_data_rows() -> None:
    path = _write_excel([["観点名", "対象", "重要度", "工程", "レビュー指示文"]])

    with pytest.raises(ValueError, match="no aspect rows"):
        parse_excel_aspects(path)


def test_txt_aspect_parser_parses_header_and_rows() -> None:
    path = _path("aspects.txt")
    path.write_text(
        "観点名|対象|重要度|工程|レビュー指示文\n"
        "必須項目欠落|UI|高|基本設計|必須項目を確認\n",
        encoding="utf-8",
    )

    aspects = parse_txt_aspects(path)

    assert len(aspects) == 1
    assert aspects[0].name == "必須項目欠落"
    assert aspects[0].severity == "high"


def test_txt_aspect_parser_parses_without_header_and_trims_fields() -> None:
    path = _path("aspects.txt")
    path.write_text(" 型不整合 | SS | 中 | 詳細設計 | データ型を確認 \n", encoding="utf-8")

    aspects = parse_txt_aspects(path)

    assert aspects[0].name == "型不整合"
    assert aspects[0].target == "SS"
    assert aspects[0].prompt_template == "データ型を確認"


def test_txt_aspect_parser_reports_wrong_field_count() -> None:
    path = _path("aspects.txt")
    path.write_text("観点名|UI|高\n", encoding="utf-8")

    with pytest.raises(ValueError, match="line 1"):
        parse_txt_aspects(path)


def test_txt_aspect_parser_rejects_empty_file() -> None:
    path = _path("aspects.txt")
    path.write_text("\n\n", encoding="utf-8")

    with pytest.raises(ValueError, match="no aspect rows"):
        parse_txt_aspects(path)


def test_parse_aspect_file_rejects_unsupported_extension() -> None:
    path = _path("aspects.md")
    path.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported aspect file extension"):
        parse_aspect_file(path)
