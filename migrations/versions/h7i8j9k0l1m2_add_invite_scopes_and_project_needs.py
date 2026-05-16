"""Add scope/project_id/role to invite_codes; add project_needs table

Revision ID: h7i8j9k0l1m2
Revises: g6b7c8d9e0f1
Create Date: 2026-05-16 12:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "h7i8j9k0l1m2"
down_revision: Union[str, Sequence[str], None] = "g6b7c8d9e0f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Extend auth_invite_codes with scope, project_id, role
    op.add_column(
        "auth_invite_codes",
        sa.Column(
            "scope",
            sa.String(20),
            nullable=False,
            server_default="system",
        ),
    )
    op.add_column(
        "auth_invite_codes",
        sa.Column(
            "project_id",
            sa.String(255),
            sa.ForeignKey("projects.project_id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.add_column(
        "auth_invite_codes",
        sa.Column("role", sa.String(50), nullable=True),
    )

    # 2. Create project_needs table
    op.create_table(
        "project_needs",
        sa.Column("need_id", sa.String(255), primary_key=True),
        sa.Column(
            "project_id",
            sa.String(255),
            sa.ForeignKey("projects.project_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("skills", sa.Text, nullable=False, server_default="[]"),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("slots", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="open",
        ),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_project_needs_project_id", "project_needs", ["project_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_project_needs_project_id", table_name="project_needs")
    op.drop_table("project_needs")
    op.drop_column("auth_invite_codes", "role")
    op.drop_column("auth_invite_codes", "project_id")
    op.drop_column("auth_invite_codes", "scope")
