from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "AI Team Backend")
    environment: str = os.getenv("ENVIRONMENT", "development")
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "xxx-development-placeholder")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_hours: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "8"))
    llm_provider: str = os.getenv("LLM_PROVIDER", "stub")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "xxx")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    anthropic_max_tokens: int = int(os.getenv("ANTHROPIC_MAX_TOKENS", "4096"))
    review_execution_timeout_seconds: int = int(
        os.getenv("REVIEW_EXECUTION_TIMEOUT_SECONDS", "60")
    )
    review_aspect_concurrency: int = int(os.getenv("REVIEW_ASPECT_CONCURRENCY", "2"))
    pii_masking_enabled: bool = os.getenv("PII_MASKING_ENABLED", "false").lower() == "true"
    pdf_output_dir: str = os.getenv("PDF_OUTPUT_DIR", "storage/pdfs")
    pdf_generation_timeout_seconds: int = int(
        os.getenv("PDF_GENERATION_TIMEOUT_SECONDS", "120")
    )
    pdf_findings_per_page: int = int(os.getenv("PDF_FINDINGS_PER_PAGE", "8"))
    excel_converter: str = os.getenv("EXCEL_CONVERTER", "auto")
    max_upload_bytes: int = 50 * 1024 * 1024

    @property
    def access_token_expire_seconds(self) -> int:
        return self.access_token_expire_hours * 60 * 60

    @property
    def backend_dir(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def pdf_output_path(self) -> Path:
        path = Path(self.pdf_output_dir)
        if path.is_absolute():
            return path
        return self.backend_dir / path


settings = Settings()
