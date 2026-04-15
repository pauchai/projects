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
from sqlalchemy.orm import composite, registry, relationship

from cohort_learning.domain.cohort_membership import CohortMembership
from cohort_learning.domain.cohort_role import CohortRole
from cohort_learning.domain.cohort_status import CohortStatus
from cohort_learning.domain.learning_cohort import LearningCohort
from cohort_learning.domain.module_progression import ModuleProgression
from cohort_learning.domain.peer_review import PeerReview
from cohort_learning.domain.practice_task import PracticeTask
from cohort_learning.domain.review_score import ReviewScore
from cohort_learning.domain.review_status import ReviewStatus
from cohort_learning.domain.task_status import SubmissionStatus, TaskStatus
from cohort_learning.domain.task_submission import TaskSubmission
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
