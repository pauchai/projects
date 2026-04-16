"""SQLAlchemy ORM mapping via Imperative Mapping for the Partnership bounded context.

Domain classes remain free of SQLAlchemy imports. The mapper is triggered on
module import.

Key design decisions:
- ``_events`` on Commission is NOT persisted (transient, initialised in the
  repository after load via ``_init_transient()``).
- All IDs are stored as String(255) (UUIDs generated at domain level).
- ``CommissionStatus`` Enum uses ``values_callable`` to store the ``.value``
  string in the database.
- Monetary amounts are stored as NUMERIC(12, 2).
"""

from __future__ import annotations

from sqlalchemy import Column, DateTime, Enum, MetaData, Numeric, String, Table
from sqlalchemy.orm import registry

from partnership.domain.commission import Commission, CommissionStatus

# ---------------------------------------------------------------------------
# Registry (manages MetaData + class ↔ table mappings)
# ---------------------------------------------------------------------------

mapper_registry = registry()
metadata: MetaData = mapper_registry.metadata

# ---------------------------------------------------------------------------
# Table definitions
# ---------------------------------------------------------------------------

commissions_table = Table(
    "commissions",
    metadata,
    Column("commission_id", String(255), primary_key=True),
    Column("curator_id", String(255), nullable=False, index=True),
    Column("cohort_id", String(255), nullable=False, index=True),
    Column("module_id", String(255), nullable=False),
    Column("base_amount", Numeric(12, 2), nullable=False),
    Column("bonus_amount", Numeric(12, 2), nullable=False),
    Column(
        "status",
        Enum(CommissionStatus, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    ),
    Column("earned_at", DateTime(timezone=True), nullable=False),
    Column("release_eligible_at", DateTime(timezone=True), nullable=False),
    Column("released_at", DateTime(timezone=True), nullable=True),
)

# ---------------------------------------------------------------------------
# Imperative mappings
# ---------------------------------------------------------------------------

mapper_registry.map_imperatively(Commission, commissions_table)
