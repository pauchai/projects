"""Add lessons table and repo_url columns.

Revision ID: g6b7c8d9e0f1
Revises: f5a6b7c8d9e0
Create Date: 2026-05-14
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "g6b7c8d9e0f1"
down_revision = "a0b1c2d3e4f5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- module_progressions: репозиторий учебного контента модуля ---
    op.add_column(
        "module_progressions",
        sa.Column("repo_url", sa.Text(), nullable=True),
    )

    # --- projects: репозиторий документации проекта ---
    op.add_column(
        "projects",
        sa.Column("docs_repo_url", sa.Text(), nullable=True),
    )

    # --- lessons: уроки внутри модуля ---
    op.create_table(
        "lessons",
        sa.Column("lesson_id", sa.String(255), primary_key=True),
        sa.Column(
            "module_id",
            sa.String(255),
            sa.ForeignKey("module_progressions.module_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "topic_id",
            sa.String(255),
            sa.ForeignKey("topics.topic_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("content_path", sa.Text(), nullable=True),
        sa.Column("homework_path", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("lessons")
    op.drop_column("projects", "docs_repo_url")
    op.drop_column("module_progressions", "repo_url")
