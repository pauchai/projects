"""ListMyCohorts use case."""

from cohort_learning.domain.learning_cohort import LearningCohort
from cohort_learning.domain.ports import UnitOfWork


class ListMyCohortsUseCase:
    """Returns all cohorts where the caller is either master or active member.

    Results are deduplicated (a master who is also a member of their own cohort
    appears only once) and ordered by ``formed_at`` descending.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, caller_id: str) -> list[LearningCohort]:
        with self._uow as uow:
            as_master = uow.cohorts.find_by_master(caller_id)
            as_learner = uow.cohorts.find_by_learner(caller_id)

            seen: set[str] = set()
            result: list[LearningCohort] = []
            for cohort in as_master + as_learner:
                if cohort.cohort_id not in seen:
                    seen.add(cohort.cohort_id)
                    result.append(cohort)

            result.sort(key=lambda c: c.formed_at, reverse=True)
            return result
