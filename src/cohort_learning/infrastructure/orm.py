"""SQLAlchemy ORM mapping via Imperative Mapping (registry.map_imperatively).

Domain classes remain free of SQLAlchemy imports. Table definitions are kept
here alongside the mapping configuration. The mapper is triggered on module
import — any module that imports from ``orm`` will activate the mappings.

Key design decisions:
- ``_events`` on LearningCohort is NOT persisted (transient, initialised in
  the repository after load).
- ``_topics`` on ModuleProgression is mapped as a relationship to Topic.
- All IDs are stored as String(255) (UUIDs generated at the domain level).
- Enums use ``values_callable=lambda e: [m.value for m in e]`` to store
  the ``.value`` string in the database.
"""

from __future__ import annotations

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
from sqlalchemy.orm import registry, relationship

from cohort_learning.domain.cohort_membership import CohortMembership
from cohort_learning.domain.cohort_role import CohortRole
from cohort_learning.domain.cohort_status import CohortStatus
from cohort_learning.domain.learning_cohort import LearningCohort
from cohort_learning.domain.module_progression import ModuleProgression
from cohort_learning.domain.topic import Topic
from cohort_learning.domain.topic_competency import TopicCompetency

# ---------------------------------------------------------------------------
# Registry (manages MetaData + class ↔ table mappings)
# ---------------------------------------------------------------------------

mapper_registry = registry()
metadata: MetaData = mapper_registry.metadata

# ---------------------------------------------------------------------------
# Table definitions
# ---------------------------------------------------------------------------

learning_cohorts_table = Table(
    "learning_cohorts",
    metadata,
    Column("cohort_id", String(255), primary_key=True),
    Column("master_id", String(255), nullable=False),
    Column("module_id", String(255), nullable=False),
    Column(
        "status",
        Enum(CohortStatus, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=CohortStatus.FORMING.value,
    ),
    Column("formed_at", DateTime(timezone=True), nullable=False),
)

cohort_memberships_table = Table(
    "cohort_memberships",
    metadata,
    Column("membership_id", String(255), primary_key=True),
    Column("learner_id", String(255), nullable=False),
    Column(
        "cohort_id",
        String(255),
        ForeignKey("learning_cohorts.cohort_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "role",
        Enum(CohortRole, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=CohortRole.LEARNER.value,
    ),
    Column("is_active", Boolean, nullable=False, default=True),
    Column("joined_at", DateTime(timezone=True), nullable=False),
)

module_progressions_table = Table(
    "module_progressions",
    metadata,
    Column("module_id", String(255), primary_key=True),
    Column("title", String(200), nullable=False),
    Column("master_id", String(255), nullable=False),
)

topics_table = Table(
    "topics",
    metadata,
    Column("topic_id", String(255), primary_key=True),
    Column("title", String(200), nullable=False),
    Column("position", Integer, nullable=False),
    Column("description", Text, nullable=False, default=""),
    Column(
        "module_id",
        String(255),
        ForeignKey("module_progressions.module_id", ondelete="CASCADE"),
        nullable=False,
    ),
)

topic_competencies_table = Table(
    "topic_competencies",
    metadata,
    Column("competency_id", String(255), primary_key=True),
    Column("learner_id", String(255), nullable=False),
    Column("topic_id", String(255), nullable=False),
    Column("cohort_id", String(255), nullable=False),
    Column("achieved_at", DateTime(timezone=True), nullable=False),
)

# ---------------------------------------------------------------------------
# Imperative mappings
# ---------------------------------------------------------------------------

# Child entities first (before parent that references them via relationship)
mapper_registry.map_imperatively(CohortMembership, cohort_memberships_table)

mapper_registry.map_imperatively(
    LearningCohort,
    learning_cohorts_table,
    properties={
        "memberships": relationship(
            CohortMembership,
            cascade="all, delete-orphan",
            passive_deletes=True,
        ),
    },
)

mapper_registry.map_imperatively(Topic, topics_table)

mapper_registry.map_imperatively(
    ModuleProgression,
    module_progressions_table,
    properties={
        "_topics": relationship(
            Topic,
            cascade="all, delete-orphan",
            passive_deletes=True,
        ),
    },
)

mapper_registry.map_imperatively(TopicCompetency, topic_competencies_table)
