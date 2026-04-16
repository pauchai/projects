"""SQLAlchemy ORM-based repository adapters (driven adapters) for Cohort Learning.

Uses SQLAlchemy ORM with Imperative Mapping (configured in ``orm.py``).
Domain classes are loaded/saved as mapped objects; the ORM handles
``__new__`` + attribute population on load, bypassing ``__init__``.

``_events`` is NOT persisted — it is a transient list of domain events,
initialised after load via ``_init_transient()``.

Repositories:
- ``SqlAlchemyCohortRepository`` — LearningCohort aggregate
- ``SqlAlchemyPracticeTaskRepository`` — PracticeTask aggregate (with submissions)
- ``SqlAlchemyPeerReviewRepository`` — PeerReview aggregate (with ReviewScore conversion)
- ``SqlAlchemyTopicExpertRepository`` — TopicExpert entity (no events)
- ``SqlAlchemyHelperMetricsRepository`` — HelperMetrics entity (with Decimal conversion)
- ``SqlAlchemyModuleCuratorRepository`` — ModuleCurator entity (no events)
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from cohort_learning.domain.helper_metrics import HelperMetrics
from cohort_learning.domain.learning_cohort import LearningCohort
from cohort_learning.domain.module_curator import ModuleCurator
from cohort_learning.domain.peer_review import PeerReview
from cohort_learning.domain.practice_task import PracticeTask
from cohort_learning.domain.review_score import ReviewScore
from cohort_learning.domain.topic_competency import TopicCompetency
from cohort_learning.domain.topic_expert import TopicExpert
from cohort_learning.infrastructure.orm import ReviewScoreRecord


class SqlAlchemyCohortRepository:
    """Implements CohortRepository Protocol using SQLAlchemy ORM."""

    def __init__(self, session: Session, uow: object | None = None) -> None:
        self._session = session
        self._uow = uow

    # ------------------------------------------------------------------
    # Public interface (matches CohortRepository Protocol)
    # ------------------------------------------------------------------

    def find_by_id(self, cohort_id: str) -> LearningCohort | None:
        """Load a full LearningCohort aggregate by ID, or return None."""
        cohort = self._session.get(
            LearningCohort,
            cohort_id,
            options=[
                selectinload(LearningCohort.memberships),  # type: ignore[attr-defined]
            ],
        )
        if cohort is None:
            return None

        self._init_transient(cohort)
        return cohort

    def save(self, cohort: LearningCohort) -> None:
        """Persist a LearningCohort aggregate (cohort + memberships).

        Collects domain events from the aggregate and passes them to the UoW
        for publishing after commit.
        """
        # 1. Collect domain events before merge (merge may return a different object)
        events = cohort.collect_events()
        if events and self._uow is not None and hasattr(self._uow, "collect_events"):
            self._uow.collect_events(events)

        # 2. Merge the aggregate (cohort + relationships handled by ORM)
        self._session.merge(cohort)
        # Flush to ensure the cohort row exists
        self._session.flush()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _init_transient(cohort: LearningCohort) -> None:
        """Initialise transient attributes that the ORM does not populate."""
        if not hasattr(cohort, "_events"):
            cohort._events = []


class SqlAlchemyPracticeTaskRepository:
    """Implements PracticeTaskRepository Protocol using SQLAlchemy ORM.

    PracticeTask is an aggregate root that owns TaskSubmission entities.
    Submissions are eagerly loaded via ``selectinload`` and persisted
    through the ORM cascade.
    """

    def __init__(self, session: Session, uow: object | None = None) -> None:
        self._session = session
        self._uow = uow

    # ------------------------------------------------------------------
    # Public interface (matches PracticeTaskRepository Protocol)
    # ------------------------------------------------------------------

    def find_by_id(self, task_id: str) -> PracticeTask | None:
        """Load a PracticeTask aggregate with submissions, or return None."""
        task = self._session.get(
            PracticeTask,
            task_id,
            options=[
                selectinload(PracticeTask.submissions),  # type: ignore[attr-defined]
            ],
        )
        if task is None:
            return None

        self._init_transient(task)
        return task

    def save(self, task: PracticeTask) -> None:
        """Persist a PracticeTask aggregate (task + submissions).

        Collects domain events and delegates to UoW for post-commit publishing.
        """
        events = task.collect_events()
        if events and self._uow is not None and hasattr(self._uow, "collect_events"):
            self._uow.collect_events(events)

        self._session.merge(task)
        self._session.flush()

    def find_by_cohort(self, cohort_id: str) -> list[PracticeTask]:
        """Return all PracticeTasks belonging to a cohort."""
        stmt = (
            select(PracticeTask)
            .where(PracticeTask.cohort_id == cohort_id)  # type: ignore[attr-defined]
            .options(
                selectinload(PracticeTask.submissions),  # type: ignore[attr-defined]
            )
        )
        tasks = list(self._session.scalars(stmt).all())
        for task in tasks:
            self._init_transient(task)
        return tasks

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _init_transient(task: PracticeTask) -> None:
        """Initialise transient attributes that the ORM does not populate."""
        if not hasattr(task, "_events"):
            task._events = []


class SqlAlchemyPeerReviewRepository:
    """Implements PeerReviewRepository Protocol using SQLAlchemy ORM.

    PeerReview stores scores as ``ReviewScore`` frozen dataclasses (value objects).
    Since frozen dataclasses cannot be mapped directly by SQLAlchemy imperative
    mapping, the ORM maps ``_score_records`` (list of ``ReviewScoreRecord``) as
    a relationship. This repository converts between the two representations:

    - On ``save()``: ``review.scores`` → ``review._score_records``
    - On ``find_by_id()`` / ``find_by_submission()``: ``review._score_records`` → ``review.scores``
    """

    def __init__(self, session: Session, uow: object | None = None) -> None:
        self._session = session
        self._uow = uow

    # ------------------------------------------------------------------
    # Public interface (matches PeerReviewRepository Protocol)
    # ------------------------------------------------------------------

    def find_by_id(self, review_id: str) -> PeerReview | None:
        """Load a PeerReview aggregate with score records, or return None."""
        review = self._session.get(
            PeerReview,
            review_id,
            options=[
                selectinload(PeerReview._score_records),  # type: ignore[attr-defined]
            ],
        )
        if review is None:
            return None

        self._reconstitute(review)
        return review

    def save(self, review: PeerReview) -> None:
        """Persist a PeerReview aggregate with ReviewScore conversion.

        Converts domain ``review.scores`` (list[ReviewScore]) to ORM
        ``_score_records`` (list[ReviewScoreRecord]) before merge.
        """
        events = review.collect_events()
        if events and self._uow is not None and hasattr(self._uow, "collect_events"):
            self._uow.collect_events(events)

        # Convert domain scores → ORM records for persistence
        review._score_records = [  # type: ignore[attr-defined]
            ReviewScoreRecord.from_domain(review.review_id, score)
            for score in review.scores
        ]

        self._session.merge(review)
        self._session.flush()

    def find_by_submission(self, submission_id: str) -> list[PeerReview]:
        """Return all PeerReviews for a given submission."""
        stmt = (
            select(PeerReview)
            .where(PeerReview.submission_id == submission_id)  # type: ignore[attr-defined]
            .options(
                selectinload(PeerReview._score_records),  # type: ignore[attr-defined]
            )
        )
        reviews = list(self._session.scalars(stmt).all())
        for review in reviews:
            self._reconstitute(review)
        return reviews

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _reconstitute(review: PeerReview) -> None:
        """Convert ORM _score_records to domain scores and init transient state."""
        # Convert ORM records → domain ReviewScore value objects
        score_records: list[ReviewScoreRecord] = getattr(review, "_score_records", [])
        review.scores = [record.to_domain() for record in score_records]

        # Initialise transient event list
        if not hasattr(review, "_events"):
            review._events = []


class SqlAlchemyTopicExpertRepository:
    """Implements TopicExpertRepository Protocol using SQLAlchemy ORM.

    TopicExpert is a simple entity without domain events or value object
    conversions. This repository provides basic CRUD operations.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Public interface (matches TopicExpertRepository Protocol)
    # ------------------------------------------------------------------

    def find_by_id(self, expert_id: str) -> TopicExpert | None:
        """Load a TopicExpert by ID, or return None."""
        return self._session.get(TopicExpert, expert_id)

    def save(self, expert: TopicExpert) -> None:
        """Persist a TopicExpert entity."""
        self._session.merge(expert)
        self._session.flush()

    def find_by_learner_and_topic(
        self, learner_id: str, topic_id: str, cohort_id: str
    ) -> TopicExpert | None:
        """Find TopicExpert record for a specific learner, topic, and cohort."""
        stmt = select(TopicExpert).where(
            TopicExpert.learner_id == learner_id,  # type: ignore[attr-defined]
            TopicExpert.topic_id == topic_id,  # type: ignore[attr-defined]
            TopicExpert.cohort_id == cohort_id,  # type: ignore[attr-defined]
        )
        return self._session.scalars(stmt).first()

    def find_by_cohort(self, cohort_id: str) -> list[TopicExpert]:
        """Return all TopicExperts in a cohort."""
        stmt = select(TopicExpert).where(
            TopicExpert.cohort_id == cohort_id  # type: ignore[attr-defined]
        )
        return list(self._session.scalars(stmt).all())


class SqlAlchemyHelperMetricsRepository:
    """Implements HelperMetricsRepository Protocol using SQLAlchemy ORM.

    HelperMetrics stores average_satisfaction as a Decimal in the domain,
    but as String(10) in the database. This repository handles the conversion.
    The table uses a composite primary key (learner_id, cohort_id).
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Public interface (matches HelperMetricsRepository Protocol)
    # ------------------------------------------------------------------

    def find_by_learner_and_cohort(
        self, learner_id: str, cohort_id: str
    ) -> HelperMetrics | None:
        """Load HelperMetrics by composite key (learner_id, cohort_id)."""
        # SQLAlchemy .get() with composite key uses tuple
        metrics = self._session.get(HelperMetrics, (learner_id, cohort_id))
        if metrics is None:
            return None

        self._reconstitute(metrics)
        return metrics

    def save(self, metrics: HelperMetrics) -> None:
        """Persist HelperMetrics with Decimal → String conversion."""
        # Convert Decimal → String for database storage
        avg_satisfaction_str: str | None = None
        if metrics.average_satisfaction is not None:
            avg_satisfaction_str = str(metrics.average_satisfaction)

        # Create a copy with the string value for ORM persistence
        # (The ORM will handle the attribute assignment)
        metrics_dict = {
            "learner_id": metrics.learner_id,
            "cohort_id": metrics.cohort_id,
            "learners_helped": metrics.learners_helped,
            "questions_answered": metrics.questions_answered,
            "tasks_reviewed": metrics.tasks_reviewed,
            "average_satisfaction": avg_satisfaction_str,  # type: ignore[dict-item]
            "updated_at": metrics.updated_at,
        }

        # Merge will INSERT or UPDATE based on primary key
        self._session.merge(HelperMetrics(**metrics_dict))  # type: ignore[arg-type]
        self._session.flush()

    def find_by_cohort(self, cohort_id: str) -> list[HelperMetrics]:
        """Return all HelperMetrics for a cohort."""
        stmt = select(HelperMetrics).where(
            HelperMetrics.cohort_id == cohort_id  # type: ignore[attr-defined]
        )
        metrics_list = list(self._session.scalars(stmt).all())
        for metrics in metrics_list:
            self._reconstitute(metrics)
        return metrics_list

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _reconstitute(metrics: HelperMetrics) -> None:
        """Convert String → Decimal for average_satisfaction after load."""
        avg_str = getattr(metrics, "average_satisfaction", None)
        if avg_str is not None and isinstance(avg_str, str):
            metrics.average_satisfaction = Decimal(avg_str)  # type: ignore[misc]
        else:
            metrics.average_satisfaction = None  # type: ignore[misc]


class SqlAlchemyModuleCuratorRepository:
    """Implements ModuleCuratorRepository Protocol using SQLAlchemy ORM.

    ModuleCurator is a simple entity without domain events or value object
    conversions. This repository provides basic CRUD operations.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Public interface (matches ModuleCuratorRepository Protocol)
    # ------------------------------------------------------------------

    def find_by_id(self, curator_id: str) -> ModuleCurator | None:
        """Load a ModuleCurator by ID, or return None."""
        return self._session.get(ModuleCurator, curator_id)

    def save(self, curator: ModuleCurator) -> None:
        """Persist a ModuleCurator entity."""
        self._session.merge(curator)
        self._session.flush()

    def find_by_learner_and_module(
        self, learner_id: str, module_id: str, cohort_id: str
    ) -> ModuleCurator | None:
        """Find ModuleCurator record for a specific learner, module, and cohort."""
        stmt = select(ModuleCurator).where(
            ModuleCurator.learner_id == learner_id,  # type: ignore[attr-defined]
            ModuleCurator.module_id == module_id,  # type: ignore[attr-defined]
            ModuleCurator.cohort_id == cohort_id,  # type: ignore[attr-defined]
        )
        return self._session.scalars(stmt).first()

    def find_by_cohort(self, cohort_id: str) -> list[ModuleCurator]:
        """Return all ModuleCurators in a cohort."""
        stmt = select(ModuleCurator).where(
            ModuleCurator.cohort_id == cohort_id  # type: ignore[attr-defined]
        )
        return list(self._session.scalars(stmt).all())


class SqlAlchemyTopicCompetencyRepository:
    """Implements TopicCompetencyRepository Protocol using SQLAlchemy ORM."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_learner_and_topic(
        self, learner_id: str, topic_id: str, cohort_id: str
    ) -> TopicCompetency | None:
        """Find TopicCompetency for a specific learner, topic, and cohort."""
        stmt = select(TopicCompetency).where(
            TopicCompetency.learner_id == learner_id,  # type: ignore[attr-defined]
            TopicCompetency.topic_id == topic_id,  # type: ignore[attr-defined]
            TopicCompetency.cohort_id == cohort_id,  # type: ignore[attr-defined]
        )
        return self._session.scalars(stmt).first()

    def save(self, competency: TopicCompetency) -> None:
        """Persist a TopicCompetency record."""
        self._session.merge(competency)
        self._session.flush()
