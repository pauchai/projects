"""Tests for CreatePracticeTask use case."""

import pytest

from cohort_learning.application.create_practice_task import CreatePracticeTaskUseCase
from cohort_learning.domain.events import PracticeTaskCreated
from cohort_learning.domain.task_status import TaskStatus
from shared_kernel.events import DomainEvent
from tests.cohort_learning.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.cohort_learning.factories import (
    make_active_cohort,
    make_cohort,
    save_cohort,
)


class _SpyEventBus:
    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    def publish(self, events: list[DomainEvent]) -> None:
        self.published.extend(events)


def _setup_active_cohort(uow: FakeUnitOfWork, **overrides: object) -> None:
    """Create and persist an active cohort with defaults."""
    cohort = make_active_cohort(**overrides)
    save_cohort(uow, cohort)


class TestCreatePracticeTaskUseCase:
    """Master or module curator creates a practice task in a cohort."""

    def test_creates_task_in_draft_status(self) -> None:
        uow = FakeUnitOfWork()
        _setup_active_cohort(uow)
        use_case = CreatePracticeTaskUseCase(uow=uow)

        result = use_case.execute(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
            description="Implement CRUD endpoints",
        )

        assert result.task_id == "task1"
        assert result.status == TaskStatus.DRAFT
        assert result.title == "Build a REST API"
        assert result.description == "Implement CRUD endpoints"

    def test_persists_task_in_repository(self) -> None:
        uow = FakeUnitOfWork()
        _setup_active_cohort(uow)
        use_case = CreatePracticeTaskUseCase(uow=uow)

        use_case.execute(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )

        saved = uow.practice_tasks.find_by_id("task1")
        assert saved is not None
        assert saved.cohort_id == "c1"

    def test_commits_transaction(self) -> None:
        uow = FakeUnitOfWork()
        _setup_active_cohort(uow)
        use_case = CreatePracticeTaskUseCase(uow=uow)

        use_case.execute(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )

        assert uow.committed is True

    def test_emits_practice_task_created_event(self) -> None:
        spy_bus = _SpyEventBus()
        uow = FakeUnitOfWork(event_bus=spy_bus)
        _setup_active_cohort(uow)
        use_case = CreatePracticeTaskUseCase(uow=uow)

        use_case.execute(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )

        created_events = [
            e for e in spy_bus.published if isinstance(e, PracticeTaskCreated)
        ]
        assert len(created_events) == 1
        assert created_events[0].task_id == "task1"
        assert created_events[0].cohort_id == "c1"

    def test_raises_when_cohort_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreatePracticeTaskUseCase(uow=uow)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute(
                task_id="task1",
                cohort_id="nonexistent",
                topic_id="t1",
                creator_id="master1",
                title="Build a REST API",
            )

    def test_raises_when_caller_is_not_master_or_curator(self) -> None:
        uow = FakeUnitOfWork()
        _setup_active_cohort(uow)
        use_case = CreatePracticeTaskUseCase(uow=uow)

        with pytest.raises(PermissionError, match="master or module curator"):
            use_case.execute(
                task_id="task1",
                cohort_id="c1",
                topic_id="t1",
                creator_id="learner1",
                title="Build a REST API",
            )

    def test_curator_can_create_task(self) -> None:
        from cohort_learning.domain.cohort_role import CohortRole

        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        membership = cohort.find_membership_by_learner_id("learner1")
        assert membership is not None
        membership.promote_to(CohortRole.TOPIC_EXPERT)
        membership.promote_to(CohortRole.MODULE_CURATOR)
        cohort.collect_events()
        save_cohort(uow, cohort)

        use_case = CreatePracticeTaskUseCase(uow=uow)

        result = use_case.execute(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="learner1",
            title="Build a REST API",
        )

        assert result.task_id == "task1"
        assert result.creator_id == "learner1"

    def test_description_defaults_to_empty(self) -> None:
        uow = FakeUnitOfWork()
        _setup_active_cohort(uow)
        use_case = CreatePracticeTaskUseCase(uow=uow)

        result = use_case.execute(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )

        assert result.description == ""
