"""Tests for SubmitTaskSolution use case."""

import pytest

from cohort_learning.application.submit_task_solution import SubmitTaskSolutionUseCase
from cohort_learning.domain.events import TaskSubmissionCreated
from cohort_learning.domain.task_status import SubmissionStatus
from shared_kernel.events import DomainEvent
from tests.cohort_learning.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.cohort_learning.factories import (
    make_active_cohort,
    make_active_task,
    save_cohort,
    save_task,
)


class _SpyEventBus:
    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    def publish(self, events: list[DomainEvent]) -> None:
        self.published.extend(events)


def _setup(
    uow: FakeUnitOfWork,
    cohort_overrides: dict | None = None,
    task_overrides: dict | None = None,
) -> None:
    """Create an active cohort and an active task in the FakeUnitOfWork."""
    cohort = make_active_cohort(**(cohort_overrides or {}))
    save_cohort(uow, cohort)
    task = make_active_task(**(task_overrides or {}))
    save_task(uow, task)


class TestSubmitTaskSolutionUseCase:
    """A cohort member submits a solution to a practice task."""

    def test_creates_submission_with_submitted_status(self) -> None:
        uow = FakeUnitOfWork()
        _setup(uow)
        use_case = SubmitTaskSolutionUseCase(uow=uow)

        result = use_case.execute(
            submission_id="sub1",
            task_id="task1",
            learner_id="learner1",
            content="My solution code",
        )

        assert result.submission_id == "sub1"
        assert result.status == SubmissionStatus.SUBMITTED
        assert result.content == "My solution code"
        assert result.learner_id == "learner1"

    def test_persists_submission_on_task(self) -> None:
        uow = FakeUnitOfWork()
        _setup(uow)
        use_case = SubmitTaskSolutionUseCase(uow=uow)

        use_case.execute(
            submission_id="sub1",
            task_id="task1",
            learner_id="learner1",
            content="My solution code",
        )

        task = uow.practice_tasks.find_by_id("task1")
        assert task is not None
        assert task.submission_count == 1

    def test_commits_transaction(self) -> None:
        uow = FakeUnitOfWork()
        _setup(uow)
        use_case = SubmitTaskSolutionUseCase(uow=uow)

        use_case.execute(
            submission_id="sub1",
            task_id="task1",
            learner_id="learner1",
            content="My solution code",
        )

        assert uow.committed is True

    def test_emits_task_submission_created_event(self) -> None:
        spy_bus = _SpyEventBus()
        uow = FakeUnitOfWork(event_bus=spy_bus)
        _setup(uow)
        use_case = SubmitTaskSolutionUseCase(uow=uow)

        use_case.execute(
            submission_id="sub1",
            task_id="task1",
            learner_id="learner1",
            content="My solution code",
        )

        created_events = [
            e for e in spy_bus.published if isinstance(e, TaskSubmissionCreated)
        ]
        assert len(created_events) == 1
        assert created_events[0].submission_id == "sub1"
        assert created_events[0].learner_id == "learner1"

    def test_raises_when_task_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = SubmitTaskSolutionUseCase(uow=uow)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute(
                submission_id="sub1",
                task_id="nonexistent",
                learner_id="learner1",
                content="My solution code",
            )

    def test_raises_when_learner_is_not_cohort_member(self) -> None:
        uow = FakeUnitOfWork()
        _setup(uow)
        use_case = SubmitTaskSolutionUseCase(uow=uow)

        with pytest.raises(PermissionError, match="member"):
            use_case.execute(
                submission_id="sub1",
                task_id="task1",
                learner_id="outsider",
                content="My solution code",
            )

    def test_raises_when_creator_submits_own_task(self) -> None:
        uow = FakeUnitOfWork()
        _setup(uow)
        use_case = SubmitTaskSolutionUseCase(uow=uow)

        # master1 is the task creator (default from make_active_task)
        # master is not a "member" in the membership sense, but we need to
        # test the domain rule. Let's test with a task created by a learner.
        # Actually: creator_id="master1" and master1 is not a member,
        # so PermissionError fires first. Let's create task by learner2 instead.
        uow2 = FakeUnitOfWork()
        _setup(uow2, task_overrides={"creator_id": "learner2"})
        use_case2 = SubmitTaskSolutionUseCase(uow=uow2)

        with pytest.raises(ValueError, match="creator cannot submit"):
            use_case2.execute(
                submission_id="sub1",
                task_id="task1",
                learner_id="learner2",
                content="My solution code",
            )

    def test_raises_when_task_not_active(self) -> None:
        from tests.cohort_learning.factories import make_task

        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)
        # Save a DRAFT task (not active)
        task = make_task()
        save_task(uow, task)

        use_case = SubmitTaskSolutionUseCase(uow=uow)

        with pytest.raises(ValueError, match="[Aa]ctive"):
            use_case.execute(
                submission_id="sub1",
                task_id="task1",
                learner_id="learner1",
                content="My solution code",
            )

    def test_raises_when_learner_already_submitted(self) -> None:
        uow = FakeUnitOfWork()
        _setup(uow)
        use_case = SubmitTaskSolutionUseCase(uow=uow)

        use_case.execute(
            submission_id="sub1",
            task_id="task1",
            learner_id="learner1",
            content="First attempt",
        )

        with pytest.raises(ValueError, match="already submitted"):
            use_case.execute(
                submission_id="sub2",
                task_id="task1",
                learner_id="learner1",
                content="Second attempt",
            )
