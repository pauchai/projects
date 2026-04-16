"""GetCohortTasks use case."""

from cohort_learning.application._helpers import (
    get_cohort_or_raise,
    require_cohort_member,
)
from cohort_learning.domain.ports import UnitOfWork
from cohort_learning.domain.practice_task import PracticeTask


class GetCohortTasksUseCase:
    """Retrieves all practice tasks for a given cohort.

    Authorization: Any active cohort member.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, cohort_id: str, caller_id: str) -> list[PracticeTask]:
        """Get all tasks for a cohort.

        Args:
            cohort_id: ID of the cohort
            caller_id: ID of the user requesting the list (must be a member)

        Returns:
            List of PracticeTask aggregates for this cohort

        Raises:
            LookupError: Cohort not found
            PermissionError: Caller is not a cohort member
        """
        with self._uow as uow:
            cohort = get_cohort_or_raise(uow, cohort_id)
            require_cohort_member(cohort, caller_id)
            return uow.practice_tasks.find_by_cohort(cohort_id)
