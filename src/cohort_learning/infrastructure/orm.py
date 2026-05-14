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
- ``_events`` on PracticeTask and PeerReview are NOT persisted (transient).
- ReviewScore is mapped as a composite value object via a child table.
- HelperMetrics.average_satisfaction (Decimal) is stored as String(10) and
  converted by the repository layer.
- RewardEntry is a frozen dataclass (value object) and cannot be mapped
  directly. RewardEntryRecord is the mutable ORM proxy; metadata (dict[str,str])
  is serialised as JSON text and converted by the repository layer.
"""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    MetaData,
    PrimaryKeyConstraint,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import composite, registry, relationship

from cohort_learning.domain.cohort_membership import CohortMembership
from cohort_learning.domain.cohort_role import CohortRole
from cohort_learning.domain.cohort_status import CohortStatus
from cohort_learning.domain.helper_metrics import HelperMetrics
from cohort_learning.domain.learning_cohort import LearningCohort
from cohort_learning.domain.lesson import Lesson
from cohort_learning.domain.module_curator import ModuleCurator
from cohort_learning.domain.module_progression import ModuleProgression
from cohort_learning.domain.peer_review import PeerReview
from cohort_learning.domain.pending_competency_validation import (
    PendingCompetencyValidation,
)
from cohort_learning.domain.pending_curator_promotion import PendingCuratorPromotion
from cohort_learning.domain.practice_task import PracticeTask
from cohort_learning.domain.review_score import ReviewScore
from cohort_learning.domain.review_status import ReviewStatus
from cohort_learning.domain.reward_entry import RewardEntry
from cohort_learning.domain.task_status import SubmissionStatus, TaskStatus
from cohort_learning.domain.task_submission import TaskSubmission
from cohort_learning.domain.topic import Topic
from cohort_learning.domain.topic_competency import TopicCompetency
from cohort_learning.domain.topic_expert import TopicExpert

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
    Column("repo_url", Text, nullable=True),
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

lessons_table = Table(
    "lessons",
    metadata,
    Column("lesson_id", String(255), primary_key=True),
    Column(
        "module_id",
        String(255),
        ForeignKey("module_progressions.module_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "topic_id",
        String(255),
        ForeignKey("topics.topic_id", ondelete="SET NULL"),
        nullable=True,
    ),
    Column("title", String(300), nullable=False),
    Column("position", Integer, nullable=False, default=0),
    Column("content_path", Text, nullable=True),
    Column("homework_path", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
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

practice_tasks_table = Table(
    "practice_tasks",
    metadata,
    Column("task_id", String(255), primary_key=True),
    Column("cohort_id", String(255), nullable=False),
    Column("topic_id", String(255), nullable=False),
    Column("creator_id", String(255), nullable=False),
    Column("title", String(500), nullable=False),
    Column("description", Text, nullable=False, default=""),
    Column(
        "status",
        Enum(TaskStatus, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=TaskStatus.DRAFT.value,
    ),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

task_submissions_table = Table(
    "task_submissions",
    metadata,
    Column("submission_id", String(255), primary_key=True),
    Column(
        "task_id",
        String(255),
        ForeignKey("practice_tasks.task_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("learner_id", String(255), nullable=False),
    Column("content", Text, nullable=False),
    Column(
        "status",
        Enum(SubmissionStatus, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=SubmissionStatus.SUBMITTED.value,
    ),
    Column("submitted_at", DateTime(timezone=True), nullable=False),
)

peer_reviews_table = Table(
    "peer_reviews",
    metadata,
    Column("review_id", String(255), primary_key=True),
    Column("submission_id", String(255), nullable=False),
    Column("reviewer_id", String(255), nullable=False),
    Column("task_id", String(255), nullable=False),
    Column("cohort_id", String(255), nullable=False),
    Column(
        "status",
        Enum(ReviewStatus, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=ReviewStatus.DRAFT.value,
    ),
    Column("overall_feedback", Text, nullable=False, default=""),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("reviewed_at", DateTime(timezone=True), nullable=True),
)

review_scores_table = Table(
    "review_scores",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "review_id",
        String(255),
        ForeignKey("peer_reviews.review_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("criterion", String(255), nullable=False),
    Column("score", Integer, nullable=False),
    Column("comment", Text, nullable=False, default=""),
)

# --- Partner Progression tables ---

topic_experts_table = Table(
    "topic_experts",
    metadata,
    Column("expert_id", String(255), primary_key=True),
    Column("learner_id", String(255), nullable=False),
    Column("topic_id", String(255), nullable=False),
    Column("cohort_id", String(255), nullable=False),
    Column("validated_at", DateTime(timezone=True), nullable=False),
    Column("validator_id", String(255), nullable=False),
)

helper_metrics_table = Table(
    "helper_metrics",
    metadata,
    Column("learner_id", String(255), nullable=False),
    Column("cohort_id", String(255), nullable=False),
    Column("learners_helped", Integer, nullable=False, default=0),
    Column("questions_answered", Integer, nullable=False, default=0),
    Column("tasks_reviewed", Integer, nullable=False, default=0),
    Column("average_satisfaction", String(10), nullable=True),  # Decimal as string
    Column("updated_at", DateTime(timezone=True), nullable=False),
    PrimaryKeyConstraint("learner_id", "cohort_id"),
)

module_curators_table = Table(
    "module_curators",
    metadata,
    Column("curator_id", String(255), primary_key=True),
    Column("learner_id", String(255), nullable=False),
    Column("module_id", String(255), nullable=False),
    Column("cohort_id", String(255), nullable=False),
    Column("promoted_at", DateTime(timezone=True), nullable=False),
    Column("promoted_by", String(255), nullable=False),
)

# --- Rewards tables ---

reward_ledger_table = Table(
    "reward_ledger",
    metadata,
    Column("entry_id", String(255), primary_key=True),
    Column("learner_id", String(255), nullable=False, index=True),
    Column("reward_type", String(50), nullable=False, index=True),
    Column("amount", Integer, nullable=True),
    Column("metadata_json", Text, nullable=False, default="{}"),
    Column("granted_at", DateTime(timezone=True), nullable=False),
    Column("triggering_event", String(255), nullable=True),
    Column("cohort_id", String(255), nullable=True),
)

# --- Eligibility notification tables (Stage 17-18) ---

pending_competency_validations_table = Table(
    "pending_competency_validations",
    metadata,
    Column("pending_id", String(255), primary_key=True),
    Column("learner_id", String(255), nullable=False),
    Column("topic_id", String(255), nullable=False),
    Column("cohort_id", String(255), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

pending_curator_promotions_table = Table(
    "pending_curator_promotions",
    metadata,
    Column("pending_id", String(255), primary_key=True),
    Column("learner_id", String(255), nullable=False),
    Column("module_id", String(255), nullable=False),
    Column("cohort_id", String(255), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
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

# --- Peer Review System mappings ---

mapper_registry.map_imperatively(TaskSubmission, task_submissions_table)

mapper_registry.map_imperatively(
    PracticeTask,
    practice_tasks_table,
    properties={
        "submissions": relationship(
            TaskSubmission,
            cascade="all, delete-orphan",
            passive_deletes=True,
        ),
    },
)


class ReviewScoreRecord:
    """ORM-mapped row for review_scores table.

    ReviewScore is a frozen dataclass (value object) and cannot be mapped
    directly by SQLAlchemy's imperative mapping. This thin ORM record acts
    as the persistence representation. Conversion to/from the domain
    ReviewScore is handled in the repository layer.
    """

    def __init__(
        self,
        review_id: str = "",
        criterion: str = "",
        score: int = 0,
        comment: str = "",
    ) -> None:
        self.review_id = review_id
        self.criterion = criterion
        self.score = score
        self.comment = comment

    def to_domain(self) -> ReviewScore:
        """Convert ORM record to domain ReviewScore value object."""
        return ReviewScore(
            criterion=self.criterion,
            score=self.score,
            comment=self.comment,
        )

    @staticmethod
    def from_domain(review_id: str, score: ReviewScore) -> "ReviewScoreRecord":
        """Create ORM record from a domain ReviewScore value object."""
        return ReviewScoreRecord(
            review_id=review_id,
            criterion=score.criterion,
            score=score.score,
            comment=score.comment,
        )


mapper_registry.map_imperatively(ReviewScoreRecord, review_scores_table)

mapper_registry.map_imperatively(
    PeerReview,
    peer_reviews_table,
    properties={
        "_score_records": relationship(
            ReviewScoreRecord,
            cascade="all, delete-orphan",
            passive_deletes=True,
        ),
    },
)

# --- Partner Progression mappings ---

mapper_registry.map_imperatively(TopicExpert, topic_experts_table)

mapper_registry.map_imperatively(HelperMetrics, helper_metrics_table)

mapper_registry.map_imperatively(ModuleCurator, module_curators_table)


# --- Rewards mappings ---


class RewardEntryRecord:
    """ORM-mapped row for reward_ledger table.

    RewardEntry is a frozen dataclass (value object) and cannot be mapped
    directly by SQLAlchemy's imperative mapping. This mutable record acts
    as the persistence representation. Conversion to/from the domain
    RewardEntry is handled in the repository layer.

    The ``metadata`` dict[str, str] field is serialised as JSON text in
    ``metadata_json`` and deserialised on load.
    """

    def __init__(
        self,
        entry_id: str = "",
        learner_id: str = "",
        reward_type: str = "",
        amount: int | None = None,
        metadata_json: str = "{}",
        granted_at: datetime | None = None,
        triggering_event: str | None = None,
        cohort_id: str | None = None,
    ) -> None:
        self.entry_id = entry_id
        self.learner_id = learner_id
        self.reward_type = reward_type
        self.amount = amount
        self.metadata_json = metadata_json
        self.granted_at = granted_at
        self.triggering_event = triggering_event
        self.cohort_id = cohort_id

    def to_domain(self) -> RewardEntry:
        """Convert ORM record to domain RewardEntry frozen dataclass."""
        metadata: dict[str, str] = json.loads(self.metadata_json or "{}")
        return RewardEntry(
            entry_id=self.entry_id,
            learner_id=self.learner_id,
            reward_type=self.reward_type,
            amount=self.amount,
            metadata=metadata,
            granted_at=self.granted_at,  # type: ignore[arg-type]
            triggering_event=self.triggering_event,
            cohort_id=self.cohort_id,
        )

    @staticmethod
    def from_domain(entry: RewardEntry) -> "RewardEntryRecord":
        """Create ORM record from a domain RewardEntry frozen dataclass."""
        return RewardEntryRecord(
            entry_id=entry.entry_id,
            learner_id=entry.learner_id,
            reward_type=entry.reward_type,
            amount=entry.amount,
            metadata_json=json.dumps(entry.metadata),
            granted_at=entry.granted_at,
            triggering_event=entry.triggering_event,
            cohort_id=entry.cohort_id,
        )


mapper_registry.map_imperatively(RewardEntryRecord, reward_ledger_table)

# --- Eligibility notification mappings (Stage 17-18) ---

mapper_registry.map_imperatively(
    PendingCompetencyValidation, pending_competency_validations_table
)

mapper_registry.map_imperatively(
    PendingCuratorPromotion, pending_curator_promotions_table
)

# --- Lessons mapping ---

mapper_registry.map_imperatively(Lesson, lessons_table)
