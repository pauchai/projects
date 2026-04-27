"""GetCohortTasks use case."""

from cohort_learning.application._helpers import (
    get_cohort_or_raise,
    require_master_or_member,
)
from cohort_learning.domain.ports import UnitOfWork
from cohort_learning.domain.practice_task import PracticeTask


class GetCohortTasksUseCase:
    """Retrieves all practice tasks for a given cohort.

    Authorization: Cohort master or any active cohort member.
    The master is allowed even without a membership record.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, cohort_id: str, caller_id: str) -> list[PracticeTask]:
        """Get all tasks for a cohort.

        Args:
            cohort_id: ID of the cohort
            caller_id: ID of the user requesting the list (master or member)

        Returns:
            List of PracticeTask aggregates for this cohort

        Raises:
            LookupError: Cohort not found
            PermissionError: Caller is not the master or a cohort member
        """
        with self._uow as uow:
            cohort = get_cohort_or_raise(uow, cohort_id)
            require_master_or_member(cohort, caller_id)
            return uow.practice_tasks.find_by_cohort(cohort_id)
