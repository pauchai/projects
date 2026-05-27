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

from community.domain.community import Community
from community.domain.community_membership import CommunityMembership
from community.domain.community_role import CommunityRole
from community.domain.community_status import CommunityStatus
from community.domain.feature_request import FeatureRequest
from community.domain.feature_status import FeatureStatus
from community.domain.fund import CommunityFund, FundDistribution, FundTransaction

mapper_registry = registry()
metadata: MetaData = mapper_registry.metadata

# ---------------------------------------------------------------------------
# Communities
# ---------------------------------------------------------------------------

communities_table = Table(
    "communities",
    metadata,
    Column("community_id", String(255), primary_key=True),
    Column("name", String(200), nullable=False),
    Column("description", Text, nullable=False, default=""),
    Column("owner_id", String(255), nullable=False),
    Column("avatar_url", Text, nullable=True),
    Column(
        "status",
        Enum(CommunityStatus, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=CommunityStatus.ACTIVE.value,
    ),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

community_memberships_table = Table(
    "community_memberships",
    metadata,
    Column("membership_id", String(255), primary_key=True),
    Column("user_id", String(255), nullable=False),
    Column(
        "community_id",
        String(255),
        ForeignKey("communities.community_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "role",
        Enum(CommunityRole, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    ),
    Column("is_active", Boolean, nullable=False, default=True),
    Column("joined_at", DateTime(timezone=True), nullable=False),
    Column("weight", Float, nullable=False, default=0.0),
)

mapper_registry.map_imperatively(CommunityMembership, community_memberships_table)

mapper_registry.map_imperatively(
    Community,
    communities_table,
    properties={
        "memberships": relationship(
            CommunityMembership,
            cascade="all, delete-orphan",
            passive_deletes=True,
        ),
    },
)

# ---------------------------------------------------------------------------
# Feature Requests
# ---------------------------------------------------------------------------

community_feature_requests_table = Table(
    "community_feature_requests",
    metadata,
    Column("request_id", String(255), primary_key=True),
    Column(
        "community_id",
        String(255),
        ForeignKey("communities.community_id", ondelete="CASCADE"),
        nullable=False,
    ),
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

mapper_registry.map_imperatively(FeatureRequest, community_feature_requests_table)

# ---------------------------------------------------------------------------
# Fund
# ---------------------------------------------------------------------------

community_funds_table = Table(
    "community_funds",
    metadata,
    Column("fund_id", String(255), primary_key=True),
    Column(
        "community_id",
        String(255),
        ForeignKey("communities.community_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    ),
    Column("balance", Numeric(14, 2), nullable=False, server_default="0"),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

community_fund_transactions_table = Table(
    "community_fund_transactions",
    metadata,
    Column("transaction_id", String(255), primary_key=True),
    Column(
        "fund_id",
        String(255),
        ForeignKey("community_funds.fund_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("amount", Numeric(14, 2), nullable=False),
    Column("source", String(50), nullable=False),
    Column("ref_id", String(255), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

community_fund_distributions_table = Table(
    "community_fund_distributions",
    metadata,
    Column("distribution_id", String(255), primary_key=True),
    Column(
        "fund_id",
        String(255),
        ForeignKey("community_funds.fund_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("amount", Numeric(14, 2), nullable=False),
    Column("initiated_by", String(255), nullable=False),
    Column("note", Text, nullable=False, server_default=""),
    Column("status", String(50), nullable=False, server_default="pending"),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

mapper_registry.map_imperatively(CommunityFund, community_funds_table)
mapper_registry.map_imperatively(FundTransaction, community_fund_transactions_table)
mapper_registry.map_imperatively(FundDistribution, community_fund_distributions_table)
