"""Use case: Close a practice task (Draft/Active → Closed)."""

from __future__ import annotations

from cohort_learning.application._helpers import require_master_or_curator
from cohort_learning.domain.practice_task import PracticeTask
from cohort_learning.domain.ports import UnitOfWork


class ClosePracticeTaskUseCase:
    """Close a practice task, preventing any further submissions.

    Authorization: Master or Module Curator of the cohort.
    Preconditions: Task must exist and not be already closed.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, task_id: str, caller_id: str) -> PracticeTask:
        """Close a practice task.

        Args:
            task_id: ID of the task to close
            caller_id: ID of the user requesting closure (master or curator)

        Returns:
            The closed PracticeTask

        Raises:
            LookupError: Task not found
            PermissionError: Caller is not master or curator
            ValueError: Task is already closed
        """
        with self._uow as uow:
            task = uow.practice_tasks.find_by_id(task_id)
            if task is None:
                raise LookupError(f"Practice task {task_id} not found")

            cohort = uow.cohorts.find_by_id(task.cohort_id)
            if cohort is None:
                raise LookupError(f"Cohort {task.cohort_id} not found")

            # Authorization: master or curator
            require_master_or_curator(cohort, caller_id)

            # Business logic: transition to Closed
            task.close()

            uow.practice_tasks.save(task)
            uow.commit()

            return task
