"""Tests for GetCohortTasks use case."""

import pytest

from cohort_learning.application.get_cohort_tasks import GetCohortTasksUseCase
from cohort_learning.domain.practice_task import PracticeTask
from tests.cohort_learning.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.cohort_learning.factories import (
    make_active_cohort,
    make_active_task,
    make_task,
    save_cohort,
    save_task,
)


class TestGetCohortTasksUseCase:
    """Retrieve all practice tasks for a cohort."""

    def test_returns_empty_list_when_no_tasks(self) -> None:
        uow = FakeUnitOfWork()
        save_cohort(uow, make_active_cohort())
        use_case = GetCohortTasksUseCase(uow=uow)

        result = use_case.execute(cohort_id="c1", caller_id="learner1")

        assert result == []

    def test_returns_all_tasks_for_cohort(self) -> None:
        uow = FakeUnitOfWork()
        save_cohort(uow, make_active_cohort())
        save_task(uow, make_task(task_id="t1", cohort_id="c1"))
        save_task(uow, make_active_task(task_id="t2", cohort_id="c1"))
        use_case = GetCohortTasksUseCase(uow=uow)

        result = use_case.execute(cohort_id="c1", caller_id="learner1")

        assert len(result) == 2
        task_ids = {t.task_id for t in result}
        assert task_ids == {"t1", "t2"}

    def test_does_not_return_tasks_from_other_cohorts(self) -> None:
        uow = FakeUnitOfWork()
        save_cohort(uow, make_active_cohort(cohort_id="c1"))
        save_cohort(uow, make_active_cohort(cohort_id="c2"))
        save_task(uow, make_task(task_id="t1", cohort_id="c1"))
        save_task(uow, make_task(task_id="t2", cohort_id="c2"))
        use_case = GetCohortTasksUseCase(uow=uow)

        result = use_case.execute(cohort_id="c1", caller_id="learner1")

        assert len(result) == 1
        assert result[0].task_id == "t1"

    def test_raises_when_cohort_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = GetCohortTasksUseCase(uow=uow)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute(cohort_id="nonexistent", caller_id="user1")

    def test_raises_when_caller_not_member(self) -> None:
        """Non-members cannot list cohort tasks."""
        uow = FakeUnitOfWork()
        save_cohort(uow, make_active_cohort(cohort_id="c1"))
        use_case = GetCohortTasksUseCase(uow=uow)

        with pytest.raises(PermissionError, match="not an active member"):
            use_case.execute(cohort_id="c1", caller_id="non_member")
