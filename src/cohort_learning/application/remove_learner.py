"""RemoveLearner use case."""

from cohort_learning.application._helpers import get_cohort_or_raise, require_master
from cohort_learning.domain.ports import UnitOfWork


class RemoveLearnerUseCase:
    """Removes a learner from a cohort by deactivating their membership."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        cohort_id: str,
        membership_id: str,
        caller_id: str,
    ) -> None:
        with self._uow as uow:
            cohort = get_cohort_or_raise(uow, cohort_id)
            require_master(cohort, caller_id)
            cohort.remove_learner(membership_id=membership_id)
            uow.cohorts.save(cohort)
            uow.commit()
