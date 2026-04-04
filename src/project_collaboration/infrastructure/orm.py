"""SQLAlchemy table definitions (Core only, no ORM mapping).

The repository handles all persistence and reconstitution of domain objects
using SQLAlchemy Core queries. This keeps domain classes completely free of
SQLAlchemy concerns: no ``__init__`` conflicts, no transient-field issues,
no value-object mapping headaches.

Key design decisions:
- ``previous_status`` is persisted as a nullable column (needed for resume).
- ``_events`` is NOT persisted (transient domain events).
- ``required_skills`` uses a separate association table ``project_skill_tags``.
- ``applicant_skills`` on ApplicationForm is stored as a JSON array of strings.
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import JSON

from project_collaboration.domain.application_form import ApplicationStatus
from project_collaboration.domain.project_status import ProjectStatus
from project_collaboration.domain.role import ProjectRole

metadata = MetaData()

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
    Column("applicant_skills", JSON, nullable=False, default=[]),
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
