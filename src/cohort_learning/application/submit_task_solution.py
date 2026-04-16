"""SubmitTaskSolution use case."""

from cohort_learning.application._helpers import (
    get_cohort_or_raise,
    require_cohort_member,
)
from cohort_learning.domain.ports import UnitOfWork
from cohort_learning.domain.task_submission import TaskSubmission


class SubmitTaskSolutionUseCase:
    """A cohort member submits a solution to a practice task.

    The learner must be an active member of the task's cohort.
    Domain rules (task must be active, no duplicate submissions, creator
    cannot submit own task) are enforced by the PracticeTask aggregate.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        submission_id: str,
        task_id: str,
        learner_id: str,
        content: str,
    ) -> TaskSubmission:
        with self._uow as uow:
            task = uow.practice_tasks.find_by_id(task_id)
            if task is None:
                raise LookupError(f"Task {task_id} not found")

            cohort = get_cohort_or_raise(uow, task.cohort_id)
            require_cohort_member(cohort, learner_id)

            submission = task.add_submission(
                submission_id=submission_id,
                learner_id=learner_id,
                content=content,
            )
            uow.practice_tasks.save(task)
            uow.commit()
            return submission
