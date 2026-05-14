"""SQLAlchemy ORM mapping via Imperative Mapping (registry.map_imperatively).

Domain classes remain free of SQLAlchemy imports. Table definitions are kept
here alongside the mapping configuration. The mapper is triggered on module
import — any module that imports from ``orm`` will activate the mappings.

Key design decisions:
- ``previous_status`` is persisted as a nullable column (needed for resume).
- ``_events`` is NOT persisted (transient, initialised in the repository).
- ``required_skills`` uses a separate association table ``project_skill_tags``
  and is loaded/saved manually in the repository (SkillTag is a frozen
  dataclass value object, not an ORM-mapped entity).
- ``applicant_skills`` on ApplicationForm is stored as a JSON column and
  converted automatically via ``SkillTagListType`` (TypeDecorator).
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import registry, relationship
from sqlalchemy.types import TypeDecorator

from project_collaboration.domain.application_form import (
    ApplicationForm,
    ApplicationStatus,
)
from project_collaboration.domain.feature_request import FeatureRequest
from project_collaboration.domain.feature_status import FeatureStatus
from project_collaboration.domain.fund import FundDistribution, FundTransaction, ProjectFund
from project_collaboration.domain.membership import Membership
from project_collaboration.domain.product import Product
from project_collaboration.domain.product_type import ProductType
from project_collaboration.domain.product_visibility import ProductVisibility
from project_collaboration.domain.project import Project
from project_collaboration.domain.project_status import ProjectStatus
from project_collaboration.domain.role import ProjectRole
from project_collaboration.domain.skill_tag import SkillTag

# ---------------------------------------------------------------------------
# Registry (manages MetaData + class ↔ table mappings)
# ---------------------------------------------------------------------------

mapper_registry = registry()
metadata: MetaData = mapper_registry.metadata

# ---------------------------------------------------------------------------
# Custom type: JSON list[str] ↔ list[SkillTag]
# ---------------------------------------------------------------------------


class SkillTagListType(TypeDecorator):
    """Transparently convert between ``list[SkillTag]`` and a JSON string list.

    The underlying column type is ``JSON`` (PostgreSQL jsonb).
    """

    impl = JSON
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Any:  # noqa: ANN401
        """Python → DB: list[SkillTag] → list[str]."""
        if value is None:
            return []
        return [tag.value for tag in value]

    def process_result_value(self, value: Any, dialect: Any) -> Any:  # noqa: ANN401
        """DB → Python: list[str] → list[SkillTag]."""
        if value is None:
            return []
        return [SkillTag(v) for v in value]


# ---------------------------------------------------------------------------
# Table definitions
# ---------------------------------------------------------------------------

projects_table = Table(
    "projects",
    metadata,
    Column("project_id", String(255), primary_key=True),
    Column("title", String(200), nullable=False),
    Column("description", Text, nullable=False, default=""),
    Column("owner_id", String(255), nullable=False),
    Column("max_members", Integer, nullable=True),
    Column(
        "status",
        Enum(ProjectStatus, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=ProjectStatus.DRAFT.value,
    ),
    Column(
        "previous_status",
        Enum(ProjectStatus, values_callable=lambda e: [m.value for m in e]),
        nullable=True,
    ),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("docs_repo_url", Text, nullable=True),
)

project_skill_tags_table = Table(
    "project_skill_tags",
    metadata,
    Column(
        "project_id",
        String(255),
        ForeignKey("projects.project_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("skill_value", String(50), primary_key=True),
)

memberships_table = Table(
    "memberships",
    metadata,
    Column("membership_id", String(255), primary_key=True),
    Column("user_id", String(255), nullable=False),
    Column(
        "project_id",
        String(255),
        ForeignKey("projects.project_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "role",
        Enum(ProjectRole, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    ),
    Column("is_active", Boolean, nullable=False, default=True),
    Column("joined_at", DateTime(timezone=True), nullable=False),
    Column("weight", Float, nullable=False, default=0.0),
)

applications_table = Table(
    "applications",
    metadata,
    Column("application_id", String(255), primary_key=True),
    Column("applicant_id", String(255), nullable=False),
    Column(
        "project_id",
        String(255),
        ForeignKey("projects.project_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "desired_role",
        Enum(ProjectRole, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    ),
    Column("motivation", Text, nullable=False, default=""),
    Column("applicant_skills", SkillTagListType(), nullable=False, default=[]),
    Column(
        "status",
        Enum(
            ApplicationStatus,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=ApplicationStatus.PENDING.value,
    ),
    Column("reviewed_by", String(255), nullable=True),
    Column("submitted_at", DateTime(timezone=True), nullable=False),
)

feature_requests_table = Table(
    "feature_requests",
    metadata,
    Column("request_id", String(255), primary_key=True),
    Column("author_id", String(255), nullable=False),
    Column("title", String(500), nullable=False),
    Column("description", Text, nullable=False, default=""),
    Column(
        "status",
        Enum(FeatureStatus, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=FeatureStatus.SUBMITTED.value,
    ),
    Column("category", String(100), nullable=True),
    Column("priority", String(50), nullable=True),
    Column("admin_notes", Text, nullable=True, default=""),
    Column("metadata", JSON, nullable=False, default={}),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

# ---------------------------------------------------------------------------
# Imperative mappings
# ---------------------------------------------------------------------------

mapper_registry.map_imperatively(Membership, memberships_table)

mapper_registry.map_imperatively(ApplicationForm, applications_table)

mapper_registry.map_imperatively(
    Project,
    projects_table,
    properties={
        "memberships": relationship(
            Membership,
            cascade="all, delete-orphan",
            passive_deletes=True,
        ),
        "applications": relationship(
            ApplicationForm,
            cascade="all, delete-orphan",
            passive_deletes=True,
        ),
    },
)

mapper_registry.map_imperatively(FeatureRequest, feature_requests_table)

# ---------------------------------------------------------------------------
# Products table
# ---------------------------------------------------------------------------

project_products_table = Table(
    "project_products",
    metadata,
    Column("product_id", String(255), primary_key=True),
    Column(
        "project_id",
        String(255),
        ForeignKey("projects.project_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("title", String(300), nullable=False),
    Column("description", Text, nullable=False, default=""),
    Column(
        "product_type",
        Enum(ProductType, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    ),
    Column("price", Numeric(12, 2), nullable=True),
    Column(
        "visibility",
        Enum(ProductVisibility, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=ProductVisibility.PUBLIC.value,
    ),
    Column("is_active", Boolean, nullable=False, default=True),
    Column("ref_id", String(255), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

mapper_registry.map_imperatively(Product, project_products_table)

# ---------------------------------------------------------------------------
# Fund tables
# ---------------------------------------------------------------------------

project_funds_table = Table(
    "project_funds",
    metadata,
    Column("fund_id", String(255), primary_key=True),
    Column(
        "project_id",
        String(255),
        ForeignKey("projects.project_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    ),
    Column("balance", Numeric(14, 2), nullable=False, server_default="0"),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

fund_transactions_table = Table(
    "fund_transactions",
    metadata,
    Column("transaction_id", String(255), primary_key=True),
    Column(
        "fund_id",
        String(255),
        ForeignKey("project_funds.fund_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("amount", Numeric(14, 2), nullable=False),
    Column("source", String(50), nullable=False),
    Column("ref_id", String(255), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

fund_distributions_table = Table(
    "fund_distributions",
    metadata,
    Column("distribution_id", String(255), primary_key=True),
    Column(
        "fund_id",
        String(255),
        ForeignKey("project_funds.fund_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("amount", Numeric(14, 2), nullable=False),
    Column("initiated_by", String(255), nullable=False),
    Column("note", Text, nullable=False, server_default=""),
    Column("status", String(50), nullable=False, server_default="pending"),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

mapper_registry.map_imperatively(ProjectFund, project_funds_table)
mapper_registry.map_imperatively(FundTransaction, fund_transactions_table)
mapper_registry.map_imperatively(FundDistribution, fund_distributions_table)
