"""GetPendingCuratorPromotions use case — Stage 18.

Returns PendingCuratorPromotion records for a cohort, filtered to exclude
learners who already have a ModuleCurator record for the same
(learner, module, cohort).

Authorization: Master only (curator promotion is a Master-level action).
"""

from __future__ import annotations

from cohort_learning.application._helpers import (
    get_cohort_or_raise,
    require_master,
)
from cohort_learning.domain.pending_curator_promotion import PendingCuratorPromotion
from cohort_learning.domain.ports import UnitOfWork


class GetPendingCuratorPromotionsUseCase:
    """Query pending curator promotions for a cohort.

    Returns all ``PendingCuratorPromotion`` records where the learner has
    not yet been formally promoted to ``ModuleCurator`` for the same module.
    Stale records (learner already promoted) are filtered out at query
    time without being deleted from the store.

    Authorization:
    - Master only. Curator promotion is a Master-level decision.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        cohort_id: str,
        caller_id: str,
    ) -> list[PendingCuratorPromotion]:
        with self._uow as uow:
            cohort = get_cohort_or_raise(uow, cohort_id)
            require_master(cohort, caller_id)

            pending = uow.pending_curator_promotions.find_by_cohort(cohort_id)

            result = [
                record
                for record in pending
                if uow.module_curators.find_by_learner_and_module(
                    learner_id=record.learner_id,
                    module_id=record.module_id,
                    cohort_id=cohort_id,
                )
                is None
            ]

            uow.commit()
            return result
