"""create phase2 review tables

Revision ID: 202604280001
Revises: 202604270001
Create Date: 2026-04-28 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "202604280001"
down_revision = "202604270001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("review_type", sa.String(length=20), nullable=False),
        sa.Column("target_artifact_ids", sa.JSON(), nullable=False),
        sa.Column("aspect_ids", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "aspects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target_phases", sa.JSON(), nullable=True),
        sa.Column("prompt_template", sa.Text(), nullable=False),
        sa.Column("default_severity", sa.String(length=10), server_default="mid", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "findings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("review_id", sa.Uuid(), nullable=True),
        sa.Column("artifact_id", sa.Uuid(), nullable=True),
        sa.Column("location", sa.String(length=500), nullable=True),
        sa.Column("severity", sa.String(length=10), nullable=False),
        sa.Column("aspect_id", sa.Uuid(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("suggestion", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["artifact_id"], ["artifacts.id"]),
        sa.ForeignKeyConstraint(["aspect_id"], ["aspects.id"]),
        sa.ForeignKeyConstraint(["review_id"], ["reviews.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "responses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("finding_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["finding_id"], ["findings.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("finding_id", name="uq_responses_finding_id"),
    )


def downgrade() -> None:
    op.drop_table("responses")
    op.drop_table("findings")
    op.drop_table("aspects")
    op.drop_table("reviews")
