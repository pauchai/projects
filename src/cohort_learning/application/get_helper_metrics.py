"""GetHelperMetrics use case."""

from cohort_learning.application._helpers import (
    get_cohort_or_raise,
    require_cohort_member,
)
from cohort_learning.domain.helper_metrics import HelperMetrics
from cohort_learning.domain.ports import UnitOfWork


class GetHelperMetricsUseCase:
    """Get helper metrics for a learner in a cohort.

    Authorization:
    - Master can view all helper metrics
    - Any cohort member can view helper metrics of any other member
    - Learner can view their own metrics
    - Non-members cannot view metrics
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        learner_id: str,
        cohort_id: str,
        caller_id: str,
    ) -> HelperMetrics | None:
        with self._uow as uow:
            cohort = get_cohort_or_raise(uow, cohort_id)

            # Allow master or cohort members to view metrics
            if cohort.master_id != caller_id:
                require_cohort_member(cohort, caller_id)

            # Retrieve helper metrics
            metrics = uow.helper_metrics.find_by_learner_and_cohort(learner_id, cohort_id)

            uow.commit()
            return metrics
