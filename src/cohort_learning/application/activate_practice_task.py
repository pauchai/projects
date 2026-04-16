"""Use case: Activate a practice task (Draft → Active)."""

from __future__ import annotations

from cohort_learning.application._helpers import require_master_or_curator
from cohort_learning.domain.practice_task import PracticeTask
from cohort_learning.domain.ports import UnitOfWork


class ActivatePracticeTaskUseCase:
    """Activate a draft practice task, making it available for submissions.

    Authorization: Master or Module Curator of the cohort.
    Preconditions: Task must exist and be in Draft status.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, task_id: str, caller_id: str) -> PracticeTask:
        """Activate a practice task.

        Args:
            task_id: ID of the task to activate
            caller_id: ID of the user requesting activation (master or curator)

        Returns:
            The activated PracticeTask

        Raises:
            LookupError: Task not found
            PermissionError: Caller is not master or curator
            ValueError: Task is not in Draft status
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

            # Business logic: transition to Active
            task.activate()

            uow.practice_tasks.save(task)
            uow.commit()

            return task
