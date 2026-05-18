"""guarantorship_v2: guarantorships, user_deposits, deals, complaints, votes, platform_settings

Revision ID: k0l1m2n3o4p5
Revises: j9k0l1m2n3o4
Create Date: 2026-05-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "k0l1m2n3o4p5"
down_revision = "j9k0l1m2n3o4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── guarantorships ──────────────────────────────────────────────────────
    op.create_table(
        "guarantorships",
        sa.Column("guarantorship_id", UUID(as_uuid=False), primary_key=True),
        sa.Column("guarantor_id", UUID(as_uuid=False), nullable=False),
        sa.Column("ward_id", UUID(as_uuid=False), nullable=False),
        sa.Column("request_id", UUID(as_uuid=False), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_guarantorships_guarantor_id", "guarantorships", ["guarantor_id"])
    op.create_index("ix_guarantorships_ward_id", "guarantorships", ["ward_id"])

    # back-ref on guarantee_requests
    op.add_column(
        "guarantee_requests",
        sa.Column(
            "converted_to_guarantorship_id",
            UUID(as_uuid=False),
            nullable=True,
        ),
    )

    # ── user_deposits ───────────────────────────────────────────────────────
    op.create_table(
        "user_deposits",
        sa.Column("deposit_id", UUID(as_uuid=False), primary_key=True),
        sa.Column("ward_id", UUID(as_uuid=False), nullable=False),
        sa.Column("guarantor_id", UUID(as_uuid=False), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("blockchain_ref", sa.String(length=512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_user_deposits_ward_id", "user_deposits", ["ward_id"])
    op.create_index("ix_user_deposits_guarantor_id", "user_deposits", ["guarantor_id"])

    # ── platform_settings (singleton, id=1) ─────────────────────────────────
    op.create_table(
        "platform_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("required_guarantors_count", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("guarantor_ward_limit", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("escalation_levels", sa.Integer(), nullable=False, server_default="1"),
    )
    # seed default row
    op.execute(
        "INSERT INTO platform_settings (id, required_guarantors_count, guarantor_ward_limit, escalation_levels) "
        "VALUES (1, 2, 5, 1)"
    )

    # ── deals (stub) ────────────────────────────────────────────────────────
    op.create_table(
        "deals",
        sa.Column("deal_id", UUID(as_uuid=False), primary_key=True),
        sa.Column("initiator_id", UUID(as_uuid=False), nullable=False),
        sa.Column("counterparty_id", UUID(as_uuid=False), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # ── complaints ──────────────────────────────────────────────────────────
    op.create_table(
        "complaints",
        sa.Column("complaint_id", UUID(as_uuid=False), primary_key=True),
        sa.Column("deal_id", UUID(as_uuid=False), nullable=False),
        sa.Column("filed_by_id", UUID(as_uuid=False), nullable=False),
        sa.Column("against_id", UUID(as_uuid=False), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="open",
        ),
        sa.Column("verdict", sa.String(length=64), nullable=True),
        sa.Column("voting_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("escalation_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_complaints_deal_id", "complaints", ["deal_id"])
    op.create_index("ix_complaints_against_id", "complaints", ["against_id"])

    # ── compensation_votes ──────────────────────────────────────────────────
    op.create_table(
        "compensation_votes",
        sa.Column("vote_id", UUID(as_uuid=False), primary_key=True),
        sa.Column("complaint_id", UUID(as_uuid=False), nullable=False),
        sa.Column("voter_id", UUID(as_uuid=False), nullable=False),
        sa.Column("vote", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("complaint_id", "voter_id", name="uq_vote_per_complaint"),
    )
    op.create_index("ix_compensation_votes_complaint_id", "compensation_votes", ["complaint_id"])


def downgrade() -> None:
    op.drop_table("compensation_votes")
    op.drop_table("complaints")
    op.drop_table("deals")
    op.drop_table("platform_settings")
    op.drop_index("ix_user_deposits_guarantor_id", "user_deposits")
    op.drop_index("ix_user_deposits_ward_id", "user_deposits")
    op.drop_table("user_deposits")
    op.drop_column("guarantee_requests", "converted_to_guarantorship_id")
    op.drop_index("ix_guarantorships_ward_id", "guarantorships")
    op.drop_index("ix_guarantorships_guarantor_id", "guarantorships")
    op.drop_table("guarantorships")
