"""SQLAlchemy ORM mapping for the Guarantorship module.

Only the table definition and imperative mapping are provided here.
No business logic lives in this layer.
"""

from __future__ import annotations

from sqlalchemy import Column, DateTime, Enum, MetaData, String, Table
from sqlalchemy.orm import registry

from guarantorship.domain.guarantee import Guarantee
from guarantorship.domain.guarantee_status import GuaranteeStatus

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

mapper_registry.map_imperatively(Guarantee, guarantorships_table)
