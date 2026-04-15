"""CreatePracticeTask use case."""

from cohort_learning.application._helpers import (
    get_cohort_or_raise,
    require_master_or_curator,
)
from cohort_learning.domain.ports import UnitOfWork
from cohort_learning.domain.practice_task import PracticeTask


class CreatePracticeTaskUseCase:
    """Creates a new practice task within a cohort.

    Only the cohort master or a module curator may create tasks.
    The task starts in Draft status.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        task_id: str,
        cohort_id: str,
        topic_id: str,
        creator_id: str,
        title: str,
        description: str = "",
    ) -> PracticeTask:
        with self._uow as uow:
            cohort = get_cohort_or_raise(uow, cohort_id)
            require_master_or_curator(cohort, creator_id)

            task = PracticeTask(
                task_id=task_id,
                cohort_id=cohort_id,
                topic_id=topic_id,
                creator_id=creator_id,
                title=title,
                description=description,
            )
            uow.practice_tasks.save(task)
            uow.commit()
            return task
