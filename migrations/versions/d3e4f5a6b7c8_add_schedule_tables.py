"""Add schedule tables: curators, availability_slots, consultation_requests,
consultation_offers, appointments.

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-05-01 12:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d3e4f5a6b7c8"
down_revision: Union[str, Sequence[str], None] = "c2d3e4f5a6b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Curators
    op.create_table(
        "schedule_curators",
        sa.Column("curator_id", sa.String(255), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 2. Curator skills (simple text array via separate table)
    op.create_table(
        "schedule_curator_skills",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "curator_id",
            sa.String(255),
            sa.ForeignKey("schedule_curators.curator_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("skill", sa.String(255), nullable=False),
    )
    op.create_index(
        "ix_schedule_curator_skills_curator_id",
        "schedule_curator_skills",
        ["curator_id"],
    )

    # 3. Availability slots
    op.create_table(
        "schedule_availability_slots",
        sa.Column("slot_id", sa.String(255), primary_key=True),
        sa.Column(
            "curator_id",
            sa.String(255),
            sa.ForeignKey("schedule_curators.curator_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("weekday", sa.Integer, nullable=False),
        sa.Column("start_time", sa.Time, nullable=False),
        sa.Column("end_time", sa.Time, nullable=False),
    )
    op.create_index(
        "ix_schedule_availability_slots_curator_id",
        "schedule_availability_slots",
        ["curator_id"],
    )

    # 4. Consultation requests
    op.create_table(
        "schedule_consultation_requests",
        sa.Column("request_id", sa.String(255), primary_key=True),
        sa.Column("student_name", sa.String(255), nullable=False),
        sa.Column("request_text", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("recommended_curator_ids", sa.Text, nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 5. Consultation offers
    op.create_table(
        "schedule_consultation_offers",
        sa.Column("offer_id", sa.String(255), primary_key=True),
        sa.Column(
            "request_id",
            sa.String(255),
            sa.ForeignKey("schedule_consultation_requests.request_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("curator_id", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("offered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_schedule_offers_request_id",
        "schedule_consultation_offers",
        ["request_id"],
    )

    # 6. Appointments
    op.create_table(
        "schedule_appointments",
        sa.Column("appointment_id", sa.String(255), primary_key=True),
        sa.Column(
            "request_id",
            sa.String(255),
            sa.ForeignKey("schedule_consultation_requests.request_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("curator_id", sa.String(255), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="scheduled"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_schedule_appointments_request_id",
        "schedule_appointments",
        ["request_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_schedule_appointments_request_id", table_name="schedule_appointments")
    op.drop_table("schedule_appointments")
    op.drop_index("ix_schedule_offers_request_id", table_name="schedule_consultation_offers")
    op.drop_table("schedule_consultation_offers")
    op.drop_table("schedule_consultation_requests")
    op.drop_index("ix_schedule_availability_slots_curator_id", table_name="schedule_availability_slots")
    op.drop_table("schedule_availability_slots")
    op.drop_index("ix_schedule_curator_skills_curator_id", table_name="schedule_curator_skills")
    op.drop_table("schedule_curator_skills")
    op.drop_table("schedule_curators")
