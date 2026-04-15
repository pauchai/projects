"""Fake in-memory implementation of UnitOfWork for testing."""

import copy

from cohort_learning.domain.learning_cohort import LearningCohort
from cohort_learning.domain.peer_review import PeerReview
from cohort_learning.domain.practice_task import PracticeTask
from shared_kernel.events import DomainEvent, EventBus


class _FakeCohortRepository:
    """In-memory CohortRepository used within FakeUnitOfWork."""

    def __init__(self, uow: "FakeUnitOfWork") -> None:
        self._storage: dict[str, LearningCohort] = {}
        self._uow = uow

    def find_by_id(self, cohort_id: str) -> LearningCohort | None:
        return self._storage.get(cohort_id)

    def save(self, cohort: LearningCohort) -> None:
        events = cohort.collect_events()
        self._uow.collect_events(events)
        self._storage[cohort.cohort_id] = cohort

    def snapshot(self) -> dict[str, LearningCohort]:
        """Return a deep copy of the storage for rollback support."""
        return copy.deepcopy(self._storage)

    def restore(self, snapshot: dict[str, LearningCohort]) -> None:
        """Restore storage from a snapshot."""
        self._storage = snapshot


class _FakePracticeTaskRepository:
    """In-memory PracticeTaskRepository used within FakeUnitOfWork."""

    def __init__(self, uow: "FakeUnitOfWork") -> None:
        self._storage: dict[str, PracticeTask] = {}
        self._uow = uow

    def find_by_id(self, task_id: str) -> PracticeTask | None:
        return self._storage.get(task_id)

    def save(self, task: PracticeTask) -> None:
        events = task.collect_events()
        self._uow.collect_events(events)
        self._storage[task.task_id] = task

    def find_by_cohort(self, cohort_id: str) -> list[PracticeTask]:
        return [t for t in self._storage.values() if t.cohort_id == cohort_id]

    def snapshot(self) -> dict[str, PracticeTask]:
        return copy.deepcopy(self._storage)

    def restore(self, snapshot: dict[str, PracticeTask]) -> None:
        self._storage = snapshot


class _FakePeerReviewRepository:
    """In-memory PeerReviewRepository used within FakeUnitOfWork."""

    def __init__(self, uow: "FakeUnitOfWork") -> None:
        self._storage: dict[str, PeerReview] = {}
        self._uow = uow

    def find_by_id(self, review_id: str) -> PeerReview | None:
        return self._storage.get(review_id)

    def save(self, review: PeerReview) -> None:
        events = review.collect_events()
        self._uow.collect_events(events)
        self._storage[review.review_id] = review

    def find_by_submission(self, submission_id: str) -> list[PeerReview]:
        return [r for r in self._storage.values() if r.submission_id == submission_id]

    def snapshot(self) -> dict[str, PeerReview]:
        return copy.deepcopy(self._storage)

    def restore(self, snapshot: dict[str, PeerReview]) -> None:
        self._storage = snapshot


class FakeUnitOfWork:
    """Fake UoW for testing: in-memory with commit/rollback semantics.

    On __enter__, snapshots current state. On commit(), keeps changes.
    On rollback() or __exit__ without commit, restores the snapshot.
    Supports optional event bus for verifying event publication.
    """

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self.cohorts = _FakeCohortRepository(self)
        self.practice_tasks = _FakePracticeTaskRepository(self)
        self.peer_reviews = _FakePeerReviewRepository(self)
        self.committed = False
        self._snapshots: dict[str, object] | None = None
        self._event_bus = event_bus
        self._pending_events: list[DomainEvent] = []

    def __enter__(self) -> "FakeUnitOfWork":
        self.committed = False
        self._snapshots = {
            "cohorts": self.cohorts.snapshot(),
            "practice_tasks": self.practice_tasks.snapshot(),
            "peer_reviews": self.peer_reviews.snapshot(),
        }
        return self

    def __exit__(self, *args: object) -> None:
        if not self.committed:
            self.rollback()
        self._snapshots = None

    def commit(self) -> None:
        self.committed = True
        if self._event_bus and self._pending_events:
            self._event_bus.publish(self._pending_events)
        self._pending_events.clear()
        self._snapshots = None

    def rollback(self) -> None:
        if self._snapshots is not None:
            self.cohorts.restore(self._snapshots["cohorts"])  # type: ignore[arg-type]
            self.practice_tasks.restore(self._snapshots["practice_tasks"])  # type: ignore[arg-type]
            self.peer_reviews.restore(self._snapshots["peer_reviews"])  # type: ignore[arg-type]
            self._snapshots = None
        self._pending_events.clear()

    def collect_events(self, events: list[DomainEvent]) -> None:
        """Accumulate domain events for publishing after commit."""
        self._pending_events.extend(events)
