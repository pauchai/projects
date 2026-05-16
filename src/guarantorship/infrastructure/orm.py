"""SQLAlchemy ORM mapping for the Guarantorship module.

Only the table definition and imperative mapping are provided here.
No business logic lives in this layer.
"""

from __future__ import annotations

from sqlalchemy import Column, DateTime, Enum, MetaData, Numeric, String, Table, Text
from sqlalchemy.orm import registry

from guarantorship.domain.guarantee import Guarantee
from guarantorship.domain.guarantee_request import GuaranteeRequest
from guarantorship.domain.guarantee_status import GuaranteeStatus
from guarantorship.domain.zero_circle import ZeroCircle, ZeroCircleMember

mapper_registry = registry()
metadata: MetaData = mapper_registry.metadata

guarantorships_table = Table(
    "guarantorships",
    metadata,
    Column("guarantee_id", String(255), primary_key=True),
    Column("guarantor_id", String(255), nullable=False),
    Column("guaranteed_id", String(255), nullable=False),
    Column(
        "status",
        Enum(GuaranteeStatus, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=GuaranteeStatus.ACTIVE.value,
    ),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("revoked_at", DateTime(timezone=True), nullable=True),
    Column("blockchain_tx", String(255), nullable=True),
)

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
)

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

mapper_registry.map_imperatively(Guarantee, guarantorships_table)
mapper_registry.map_imperatively(GuaranteeRequest, guarantee_requests_table)
mapper_registry.map_imperatively(ZeroCircleMember, zero_circle_members_table)
mapper_registry.map_imperatively(
    ZeroCircle,
    zero_circles_table,
    properties={
        "members": __import__("sqlalchemy.orm", fromlist=["relationship"]).relationship(
            ZeroCircleMember,
            primaryjoin=zero_circles_table.c.circle_id
            == zero_circle_members_table.c.circle_id,
            foreign_keys=[zero_circle_members_table.c.circle_id],
            cascade="all, delete-orphan",
        )
    },
)
