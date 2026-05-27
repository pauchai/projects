"""SQLAlchemy ORM mapping for the Guarantorship bounded context.

Only table definitions and imperative mappings live here.
No business logic in this layer.
"""

from __future__ import annotations

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import registry, relationship

from guarantorship.domain.complaint import Complaint, CompensationVote
from guarantorship.domain.deal import Deal
from guarantorship.domain.guarantee_request import GuaranteeRequest
from guarantorship.domain.guarantorship import Guarantorship
from guarantorship.domain.platform_settings import PlatformSettings
from guarantorship.domain.user_deposit import UserDeposit
from guarantorship.domain.zero_circle import ZeroCircle, ZeroCircleMember

mapper_registry = registry()
metadata: MetaData = mapper_registry.metadata

# ── guarantee_requests ───────────────────────────────────────────────────────
guarantee_requests_table = Table(
    "guarantee_requests",
    metadata,
    Column("request_id", String(255), primary_key=True),
    Column("ward_id", String(255), nullable=False),
    Column("guarantor_id", String(255), nullable=False),
    Column("status", String(50), nullable=False, default="pending"),
    Column("message", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("responded_at", DateTime(timezone=True), nullable=True),
    Column("converted_to_guarantorship_id", String(255), nullable=True),
)

# ── guarantorships ───────────────────────────────────────────────────────────
guarantorships_table = Table(
    "guarantorships",
    metadata,
    Column("guarantorship_id", String(255), primary_key=True),
    Column("guarantor_id", String(255), nullable=False),
    Column("ward_id", String(255), nullable=False),
    Column("request_id", String(255), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

# ── user_deposits ────────────────────────────────────────────────────────────
user_deposits_table = Table(
    "user_deposits",
    metadata,
    Column("deposit_id", String(255), primary_key=True),
    Column("ward_id", String(255), nullable=False),
    Column("guarantor_id", String(255), nullable=False),
    Column("amount", Numeric(18, 4), nullable=False),
    Column("blockchain_ref", String(512), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

# ── platform_settings ────────────────────────────────────────────────────────
platform_settings_table = Table(
    "platform_settings",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("required_guarantors_count", Integer, nullable=False),
    Column("guarantor_ward_limit", Integer, nullable=False),
    Column("escalation_levels", Integer, nullable=False),
)

# ── deals ────────────────────────────────────────────────────────────────────
deals_table = Table(
    "deals",
    metadata,
    Column("deal_id", String(255), primary_key=True),
    Column("initiator_id", String(255), nullable=False),
    Column("counterparty_id", String(255), nullable=False),
    Column("amount", Numeric(18, 4), nullable=False),
    Column("status", String(32), nullable=False, default="pending"),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

# ── complaints ───────────────────────────────────────────────────────────────
complaints_table = Table(
    "complaints",
    metadata,
    Column("complaint_id", String(255), primary_key=True),
    Column("deal_id", String(255), nullable=False),
    Column("filed_by_id", String(255), nullable=False),
    Column("against_id", String(255), nullable=False),
    Column("description", Text, nullable=False),
    Column("status", String(32), nullable=False, default="open"),
    Column("verdict", String(64), nullable=True),
    Column("voting_deadline", DateTime(timezone=True), nullable=True),
    Column("escalation_level", Integer, nullable=False, default=0),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

# ── compensation_votes ───────────────────────────────────────────────────────
compensation_votes_table = Table(
    "compensation_votes",
    metadata,
    Column("vote_id", String(255), primary_key=True),
    Column("complaint_id", String(255), nullable=False),
    Column("voter_id", String(255), nullable=False),
    Column("vote", String(64), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("complaint_id", "voter_id", name="uq_vote_per_complaint"),
)

# ── zero_circles ─────────────────────────────────────────────────────────────
zero_circles_table = Table(
    "zero_circles",
    metadata,
    Column("circle_id", String(255), primary_key=True),
    Column("name", String(300), nullable=False),
    Column("initiated_by", String(255), nullable=False),
    Column("status", String(50), nullable=False, default="open"),
    Column("deposit_stub", Numeric(14, 2), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

zero_circle_members_table = Table(
    "zero_circle_members",
    metadata,
    Column("circle_id", String(255), primary_key=True),
    Column("user_id", String(255), primary_key=True),
    Column("joined_at", DateTime(timezone=True), nullable=False),
)

# ── imperative mappings (lazy — call register_mappers() to activate) ─────────
_mappers_registered = False


def register_mappers() -> None:
    """Register imperative ORM mappings for all Guarantorship domain classes.

    This MUST be called before any SQLAlchemy session operations in this
    bounded context. It is safe to call multiple times (idempotent).
    """
    global _mappers_registered
    if _mappers_registered:
        return
    _mappers_registered = True

    mapper_registry.map_imperatively(GuaranteeRequest, guarantee_requests_table)
    mapper_registry.map_imperatively(Guarantorship, guarantorships_table)
    mapper_registry.map_imperatively(UserDeposit, user_deposits_table)
    mapper_registry.map_imperatively(PlatformSettings, platform_settings_table)
    mapper_registry.map_imperatively(Deal, deals_table)
    mapper_registry.map_imperatively(CompensationVote, compensation_votes_table)
    mapper_registry.map_imperatively(
        Complaint,
        complaints_table,
        properties={
            "votes": relationship(
                CompensationVote,
                primaryjoin=complaints_table.c.complaint_id
                == compensation_votes_table.c.complaint_id,
                foreign_keys=[compensation_votes_table.c.complaint_id],
                cascade="all, delete-orphan",
            )
        },
    )
    mapper_registry.map_imperatively(ZeroCircleMember, zero_circle_members_table)
    mapper_registry.map_imperatively(
        ZeroCircle,
        zero_circles_table,
        properties={
            "members": relationship(
                ZeroCircleMember,
                primaryjoin=zero_circles_table.c.circle_id
                == zero_circle_members_table.c.circle_id,
                foreign_keys=[zero_circle_members_table.c.circle_id],
                cascade="all, delete-orphan",
            )
        },
    )
