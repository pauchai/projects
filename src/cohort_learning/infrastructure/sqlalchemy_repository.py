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
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from cohort_learning.domain.learning_cohort import LearningCohort
from cohort_learning.domain.peer_review import PeerReview
from cohort_learning.domain.practice_task import PracticeTask
from cohort_learning.domain.review_score import ReviewScore
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
