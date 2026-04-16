"""Fake in-memory implementation of UnitOfWork for testing."""

import copy

from cohort_learning.domain.helper_metrics import HelperMetrics
from cohort_learning.domain.learning_cohort import LearningCohort
from cohort_learning.domain.module_curator import ModuleCurator
from cohort_learning.domain.peer_review import PeerReview
from cohort_learning.domain.practice_task import PracticeTask
from cohort_learning.domain.topic_competency import TopicCompetency
from cohort_learning.domain.topic_expert import TopicExpert
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


class _FakeTopicExpertRepository:
    """In-memory TopicExpertRepository used within FakeUnitOfWork."""

    def __init__(self, uow: "FakeUnitOfWork") -> None:
        self._storage: dict[str, TopicExpert] = {}
        self._uow = uow

    def find_by_id(self, expert_id: str) -> TopicExpert | None:
        return self._storage.get(expert_id)

    def save(self, expert: TopicExpert) -> None:
        # TopicExpert is a simple value object without domain events
        self._storage[expert.expert_id] = expert

    def find_by_learner_and_topic(
        self, learner_id: str, topic_id: str, cohort_id: str
    ) -> TopicExpert | None:
        for expert in self._storage.values():
            if (
                expert.learner_id == learner_id
                and expert.topic_id == topic_id
                and expert.cohort_id == cohort_id
            ):
                return expert
        return None

    def find_by_topic(self, topic_id: str) -> list[TopicExpert]:
        return [e for e in self._storage.values() if e.topic_id == topic_id]

    def find_by_cohort(self, cohort_id: str) -> list[TopicExpert]:
        return [e for e in self._storage.values() if e.cohort_id == cohort_id]

    def snapshot(self) -> dict[str, TopicExpert]:
        return copy.deepcopy(self._storage)

    def restore(self, snapshot: dict[str, TopicExpert]) -> None:
        self._storage = snapshot


class _FakeHelperMetricsRepository:
    """In-memory HelperMetricsRepository used within FakeUnitOfWork."""

    def __init__(self, uow: "FakeUnitOfWork") -> None:
        self._storage: dict[tuple[str, str], HelperMetrics] = {}
        self._uow = uow

    def find_by_learner_and_cohort(
        self, learner_id: str, cohort_id: str
    ) -> HelperMetrics | None:
        return self._storage.get((learner_id, cohort_id))

    def find_by_cohort(self, cohort_id: str) -> list[HelperMetrics]:
        return [m for m in self._storage.values() if m.cohort_id == cohort_id]

    def save(self, metrics: HelperMetrics) -> None:
        # HelperMetrics has no domain events, so no event collection
        key = (metrics.learner_id, metrics.cohort_id)
        self._storage[key] = metrics

    def snapshot(self) -> dict[tuple[str, str], HelperMetrics]:
        return copy.deepcopy(self._storage)

    def restore(self, snapshot: dict[tuple[str, str], HelperMetrics]) -> None:
        self._storage = snapshot


class _FakeTopicCompetencyRepository:
    """In-memory TopicCompetencyRepository used within FakeUnitOfWork."""

    def __init__(self, uow: "FakeUnitOfWork") -> None:
        self._storage: dict[tuple[str, str, str], TopicCompetency] = {}
        self._uow = uow

    def find_by_learner_and_topic(
        self, learner_id: str, topic_id: str, cohort_id: str
    ) -> TopicCompetency | None:
        return self._storage.get((learner_id, topic_id, cohort_id))

    def save(self, competency: TopicCompetency) -> None:
        key = (competency.learner_id, competency.topic_id, competency.cohort_id)
        self._storage[key] = competency

    def snapshot(self) -> dict[tuple[str, str, str], TopicCompetency]:
        return copy.deepcopy(self._storage)

    def restore(self, snapshot: dict[tuple[str, str, str], TopicCompetency]) -> None:
        self._storage = snapshot


class _FakeModuleCuratorRepository:
    """In-memory ModuleCuratorRepository used within FakeUnitOfWork."""

    def __init__(self, uow: "FakeUnitOfWork") -> None:
        self._storage: dict[str, ModuleCurator] = {}
        self._uow = uow

    def find_by_id(self, curator_id: str) -> ModuleCurator | None:
        return self._storage.get(curator_id)

    def save(self, curator: ModuleCurator) -> None:
        # ModuleCurator is a simple value object without domain events
        self._storage[curator.curator_id] = curator

    def find_by_learner_and_module(
        self, learner_id: str, module_id: str, cohort_id: str
    ) -> ModuleCurator | None:
        for curator in self._storage.values():
            if (
                curator.learner_id == learner_id
                and curator.module_id == module_id
                and curator.cohort_id == cohort_id
            ):
                return curator
        return None

    def find_by_module(self, module_id: str) -> list[ModuleCurator]:
        return [c for c in self._storage.values() if c.module_id == module_id]

    def snapshot(self) -> dict[str, ModuleCurator]:
        return copy.deepcopy(self._storage)

    def restore(self, snapshot: dict[str, ModuleCurator]) -> None:
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
        self.topic_experts = _FakeTopicExpertRepository(self)
        self.helper_metrics = _FakeHelperMetricsRepository(self)
        self.module_curators = _FakeModuleCuratorRepository(self)
        self.topic_competencies = _FakeTopicCompetencyRepository(self)
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
            "topic_experts": self.topic_experts.snapshot(),
            "helper_metrics": self.helper_metrics.snapshot(),
            "module_curators": self.module_curators.snapshot(),
            "topic_competencies": self.topic_competencies.snapshot(),
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
            self.topic_experts.restore(self._snapshots["topic_experts"])  # type: ignore[arg-type]
            self.helper_metrics.restore(self._snapshots["helper_metrics"])  # type: ignore[arg-type]
            self.module_curators.restore(self._snapshots["module_curators"])  # type: ignore[arg-type]
            self.topic_competencies.restore(self._snapshots["topic_competencies"])  # type: ignore[arg-type]
            self._snapshots = None
        self._pending_events.clear()

    def collect_events(self, events: list[DomainEvent]) -> None:
        """Accumulate domain events for publishing after commit."""
        self._pending_events.extend(events)
