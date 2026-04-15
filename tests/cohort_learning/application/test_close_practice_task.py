"""Tests for ClosePracticeTaskUseCase — Draft/Active → Closed workflow."""

from __future__ import annotations

import pytest

from cohort_learning.application.close_practice_task import ClosePracticeTaskUseCase
from cohort_learning.domain.task_status import TaskStatus
from tests.cohort_learning.factories import make_active_cohort, make_cohort, make_task
from tests.cohort_learning.fakes.fake_unit_of_work import FakeUnitOfWork


class TestClosePracticeTask:
    """Test suite for closing a practice task (Draft/Active → Closed)."""

    def test_closes_draft_task(self) -> None:
        """Master can close a draft task."""
        # Arrange
        cohort = make_cohort(cohort_id="c1", master_id="master1")
        task = make_task(task_id="t1", cohort_id="c1", creator_id="master1")

        uow = FakeUnitOfWork()
        uow.cohorts.save(cohort)
        uow.practice_tasks.save(task)

        use_case = ClosePracticeTaskUseCase(uow)

        # Act
        result = use_case.execute(task_id="t1", caller_id="master1")

        # Assert
        assert result.status == TaskStatus.CLOSED
        assert uow.committed is True

    def test_closes_active_task(self) -> None:
        """Master can close an active task."""
        # Arrange
        cohort = make_cohort(cohort_id="c1", master_id="master1")
        task = make_task(task_id="t1", cohort_id="c1", creator_id="master1")
        task.activate()

        uow = FakeUnitOfWork()
        uow.cohorts.save(cohort)
        uow.practice_tasks.save(task)

        use_case = ClosePracticeTaskUseCase(uow)

        # Act
        result = use_case.execute(task_id="t1", caller_id="master1")

        # Assert
        assert result.status == TaskStatus.CLOSED

    def test_curator_can_close_task(self) -> None:
        """Module curator can close a task."""
        from cohort_learning.domain.cohort_role import CohortRole

        # Arrange
        cohort = make_active_cohort(cohort_id="c1", master_id="master1")
        membership = cohort.find_membership_by_learner_id("learner1")
        assert membership is not None
        membership.promote_to(CohortRole.TOPIC_EXPERT)
        membership.promote_to(CohortRole.MODULE_CURATOR)
        cohort.collect_events()

        task = make_task(
            task_id="t1", cohort_id="c1", topic_id="t1", creator_id="learner1"
        )

        uow = FakeUnitOfWork()
        uow.cohorts.save(cohort)
        uow.practice_tasks.save(task)

        use_case = ClosePracticeTaskUseCase(uow)

        # Act
        result = use_case.execute(task_id="t1", caller_id="learner1")

        # Assert
        assert result.status == TaskStatus.CLOSED

    def test_raises_when_task_not_found(self) -> None:
        """Raises LookupError when task does not exist."""
        # Arrange
        uow = FakeUnitOfWork()
        use_case = ClosePracticeTaskUseCase(uow)

        # Act & Assert
        with pytest.raises(LookupError, match="Practice task nonexistent not found"):
            use_case.execute(task_id="nonexistent", caller_id="user1")

    def test_raises_when_caller_not_master_or_curator(self) -> None:
        """Raises PermissionError when caller is not master/curator."""
        # Arrange
        cohort = make_cohort(cohort_id="c1", master_id="master1")
        task = make_task(task_id="t1", cohort_id="c1", creator_id="master1")

        uow = FakeUnitOfWork()
        uow.cohorts.save(cohort)
        uow.practice_tasks.save(task)

        use_case = ClosePracticeTaskUseCase(uow)

        # Act & Assert
        with pytest.raises(PermissionError, match="master or module curator"):
            use_case.execute(task_id="t1", caller_id="regular_learner")

    def test_raises_when_task_already_closed(self) -> None:
        """Raises ValueError when task is already closed (idempotency check)."""
        # Arrange
        cohort = make_cohort(cohort_id="c1", master_id="master1")
        task = make_task(task_id="t1", cohort_id="c1", creator_id="master1")
        task.close()  # Already closed

        uow = FakeUnitOfWork()
        uow.cohorts.save(cohort)
        uow.practice_tasks.save(task)

        use_case = ClosePracticeTaskUseCase(uow)

        # Act & Assert
        with pytest.raises(ValueError, match="Cannot transition from closed to closed"):
            use_case.execute(task_id="t1", caller_id="master1")
