"""FormCohort use case."""

from cohort_learning.domain.learning_cohort import LearningCohort
from cohort_learning.domain.ports import UnitOfWork


class FormCohortUseCase:
    """Creates a new learning cohort in Forming status."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        cohort_id: str,
        master_id: str,
        module_id: str,
    ) -> LearningCohort:
        with self._uow as uow:
            cohort = LearningCohort(
                cohort_id=cohort_id,
                master_id=master_id,
                module_id=module_id,
            )
            uow.cohorts.save(cohort)
            uow.commit()
            return cohort
