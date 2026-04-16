"""GrantExpertRewardUseCase — grants XP, badges, credits, or reputation to a learner."""

from __future__ import annotations

from datetime import datetime, timezone

from cohort_learning.domain.ports import UnitOfWork
from cohort_learning.domain.reward_ledger import RewardLedger


class GrantExpertRewardUseCase:
    """Grant a reward (XP, badge, credits, or reputation) to a learner.

    The use case finds-or-creates the learner's RewardLedger, applies the
    appropriate reward method, saves the ledger, and commits the transaction.

    Parameters
    ----------
    learner_id:
        Identifier of the learner receiving the reward.
    reward_type:
        One of ``"xp"``, ``"badge"``, ``"credits"``, ``"reputation"``.
    entry_id:
        Unique ID for the ledger entry (caller-supplied for idempotency).
    amount:
        Required for ``"xp"``, ``"credits"``, and ``"reputation"``.
    topic_id:
        Required for ``"badge"`` — identifies which topic the badge is for.
    cohort_id:
        Optional cohort context for the reward.
    triggering_event:
        Optional name of the domain event that triggered this reward.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        learner_id: str,
        reward_type: str,
        entry_id: str,
        amount: int | None = None,
        topic_id: str | None = None,
        cohort_id: str | None = None,
        triggering_event: str | None = None,
    ) -> RewardLedger:
        self._validate(reward_type, amount, topic_id)

        with self._uow as uow:
            ledger = uow.reward_ledgers.find_by_learner(learner_id)
            if ledger is None:
                ledger = RewardLedger(learner_id=learner_id)

            granted_at = datetime.now(timezone.utc)

            if reward_type == "xp":
                ledger.add_xp(
                    entry_id=entry_id,
                    amount=amount,  # type: ignore[arg-type]  # validated above
                    triggering_event=triggering_event,
                    granted_at=granted_at,
                    cohort_id=cohort_id,
                )
            elif reward_type == "badge":
                ledger.add_badge(
                    entry_id=entry_id,
                    topic_id=topic_id,  # type: ignore[arg-type]  # validated above
                    triggering_event=triggering_event,
                    granted_at=granted_at,
                    cohort_id=cohort_id,
                )
            elif reward_type == "credits":
                ledger.add_credits(
                    entry_id=entry_id,
                    amount=amount,  # type: ignore[arg-type]  # validated above
                    triggering_event=triggering_event,
                    granted_at=granted_at,
                    cohort_id=cohort_id,
                )
            elif reward_type == "reputation":
                ledger.update_reputation(
                    entry_id=entry_id,
                    score=amount,  # type: ignore[arg-type]  # validated above
                    granted_at=granted_at,
                    cohort_id=cohort_id,
                )

            uow.reward_ledgers.save(ledger)
            uow.commit()
            return ledger

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate(
        reward_type: str,
        amount: int | None,
        topic_id: str | None,
    ) -> None:
        valid_types = {"xp", "badge", "credits", "reputation"}
        if reward_type not in valid_types:
            raise ValueError(
                f"Invalid reward_type '{reward_type}'. Must be one of: {valid_types}"
            )
        if reward_type in {"xp", "credits", "reputation"} and amount is None:
            raise ValueError(f"amount is required for reward_type '{reward_type}'")
        if reward_type == "badge" and not topic_id:
            raise ValueError("topic_id is required for reward_type 'badge'")
