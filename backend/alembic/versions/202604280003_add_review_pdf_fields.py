"""add review pdf fields

Revision ID: 202604280003
Revises: 202604280002
Create Date: 2026-04-28 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "202604280003"
down_revision = "202604280002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reviews", sa.Column("pdf_status", sa.String(length=20), nullable=True))
    op.add_column("reviews", sa.Column("pdf_path", sa.String(length=500), nullable=True))
    op.add_column(
        "reviews",
        sa.Column("pdf_generated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("reviews", "pdf_generated_at")
    op.drop_column("reviews", "pdf_path")
    op.drop_column("reviews", "pdf_status")
