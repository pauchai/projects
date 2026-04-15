"""GetCohortTasks use case."""

from cohort_learning.application._helpers import get_cohort_or_raise
from cohort_learning.domain.ports import UnitOfWork
from cohort_learning.domain.practice_task import PracticeTask


class GetCohortTasksUseCase:
    """Retrieves all practice tasks for a given cohort."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, cohort_id: str) -> list[PracticeTask]:
        with self._uow as uow:
            get_cohort_or_raise(uow, cohort_id)
            return uow.practice_tasks.find_by_cohort(cohort_id)
