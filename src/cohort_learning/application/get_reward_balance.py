"""GetRewardBalanceUseCase — retrieve a learner's current reward balance."""

from __future__ import annotations

from cohort_learning.domain.ports import UnitOfWork
from cohort_learning.domain.reward_ledger import RewardBalance, RewardLedger


class GetRewardBalanceUseCase:
    """Return the current reward balance for a given learner.

    If no RewardLedger exists for the learner, returns an empty balance
    (zero XP, zero credits, no badges, no reputation).
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, learner_id: str) -> RewardBalance:
        ledger = self._uow.reward_ledgers.find_by_learner(learner_id)
        if ledger is None:
            return RewardBalance(
                learner_id=learner_id,
                total_xp=0,
                total_credits=0,
                badges=[],
                reputation_score=None,
            )
        return ledger.get_balance()
