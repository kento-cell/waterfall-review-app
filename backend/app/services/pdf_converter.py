from __future__ import annotations

import importlib
import platform
import shutil
import subprocess
from pathlib import Path

from app.core.config import settings


class PDFConversionError(RuntimeError):
    pass


class PDFConverter:
    def __init__(self, converter: str | None = None) -> None:
        self._converter = converter or settings.excel_converter

    def convert_to_pdf(self, input_path: Path, output_path: Path) -> Path:
        mode = self._converter.lower()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if mode == "disabled":
            raise PDFConversionError("PDF conversion is disabled by EXCEL_CONVERTER=disabled")
        if mode == "excel_com":
            return self._convert_with_excel_com(input_path, output_path)
        if mode == "libreoffice":
            return self._convert_with_libreoffice(input_path, output_path)
        if mode != "auto":
            raise PDFConversionError(f"Unsupported EXCEL_CONVERTER: {self._converter}")

        excel_error: Exception | None = None
        if platform.system().lower() == "windows" and input_path.suffix.lower() in {
            ".xlsx",
            ".xlsm",
            ".xls",
        }:
            try:
                return self._convert_with_excel_com(input_path, output_path)
            except Exception as exc:  # pragma: no cover - real COM depends on host Excel
                excel_error = exc

        try:
            return self._convert_with_libreoffice(input_path, output_path)
        except Exception as libreoffice_error:
            if excel_error is not None:
                raise PDFConversionError(
                    "Excel COM conversion failed and LibreOffice fallback is unavailable or failed: "
                    f"{excel_error}; {libreoffice_error}"
                ) from libreoffice_error
            raise PDFConversionError(
                "No PDF converter available. Install Microsoft Excel on Windows or LibreOffice "
                f"headless. Details: {libreoffice_error}"
            ) from libreoffice_error

    def _convert_with_excel_com(self, input_path: Path, output_path: Path) -> Path:
        if platform.system().lower() != "windows":
            raise PDFConversionError("Excel COM conversion requires Windows and Microsoft Excel")
        try:
            win32com_client = importlib.import_module("win32com.client")
        except ImportError as exc:
            raise PDFConversionError("pywin32 is not installed; Excel COM conversion is unavailable") from exc

        excel = None
        workbook = None
        try:
            excel = win32com_client.DispatchEx("Excel.Application")
            excel.Visible = False
            excel.DisplayAlerts = False
            workbook = excel.Workbooks.Open(str(input_path.resolve()))
            workbook.ExportAsFixedFormat(0, str(output_path.resolve()))
            return output_path
        except Exception as exc:  # pragma: no cover - depends on Excel COM
            raise PDFConversionError(f"Excel COM PDF conversion failed: {exc}") from exc
        finally:  # pragma: no cover - depends on Excel COM
            if workbook is not None:
                workbook.Close(False)
            if excel is not None:
                excel.Quit()

    def _convert_with_libreoffice(self, input_path: Path, output_path: Path) -> Path:
        executable = shutil.which("soffice") or shutil.which("libreoffice")
        if executable is None:
            raise PDFConversionError("LibreOffice executable was not found")
        result = subprocess.run(
            [
                executable,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(output_path.parent),
                str(input_path),
            ],
            capture_output=True,
            text=True,
            timeout=settings.pdf_generation_timeout_seconds,
            check=False,
        )
        if result.returncode != 0:
            message = (result.stderr or result.stdout or "unknown error").strip()
            raise PDFConversionError(f"LibreOffice PDF conversion failed: {message}")

        generated_path = output_path.parent / f"{input_path.stem}.pdf"
        if not generated_path.is_file():
            raise PDFConversionError("LibreOffice did not create the expected PDF output")
        if generated_path != output_path:
            shutil.copyfile(generated_path, output_path)
        return output_path
