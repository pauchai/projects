"""Reward auto-grant event handlers.

These handlers subscribe to domain events and automatically grant appropriate
rewards to learners via GrantExpertRewardUseCase.

Handlers:
- PeerReviewSubmittedRewardHandler  → +10 XP to reviewer
- TopicExpertPromotedRewardHandler  → Topic Expert Badge to learner
- HelperMetricsUpdatedRewardHandler → reputation recalc + credits milestone
"""

from __future__ import annotations

import uuid

from cohort_learning.application.grant_expert_reward import GrantExpertRewardUseCase
from cohort_learning.domain.events import (
    HelperMetricsUpdated,
    PeerReviewSubmitted,
    TopicExpertPromoted,
)
from cohort_learning.domain.ports import UnitOfWork
from shared_kernel.events import DomainEvent

_CREDITS_PER_MILESTONE = 5
_MILESTONE_STEP = 10


class PeerReviewSubmittedRewardHandler:
    """Grant +10 XP to the reviewer whenever a peer review is submitted.

    Triggered by: ``PeerReviewSubmitted``
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, event: DomainEvent) -> None:
        assert isinstance(event, PeerReviewSubmitted)
        GrantExpertRewardUseCase(self._uow).execute(
            learner_id=event.reviewer_id,
            reward_type="xp",
            entry_id=str(uuid.uuid4()),
            amount=10,
            cohort_id=event.cohort_id,
            triggering_event="PeerReviewSubmitted",
        )


class TopicExpertPromotedRewardHandler:
    """Grant a Topic Expert Badge when a learner is promoted to Topic Expert.

    Triggered by: ``TopicExpertPromoted``
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, event: DomainEvent) -> None:
        assert isinstance(event, TopicExpertPromoted)
        GrantExpertRewardUseCase(self._uow).execute(
            learner_id=event.learner_id,
            reward_type="badge",
            entry_id=str(uuid.uuid4()),
            topic_id=event.topic_id,
            cohort_id=event.cohort_id,
            triggering_event="TopicExpertPromoted",
        )


class HelperMetricsUpdatedRewardHandler:
    """Update reputation and grant learning credits at milestone thresholds.

    Triggered by: ``HelperMetricsUpdated``

    Behaviour:
    - Always recalculates and stores the learner's reputation score.
    - Grants +5% learning credits for every new multiple of 10 in
      ``learners_helped`` (catch-up logic: compares expected vs actual).
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, event: DomainEvent) -> None:
        assert isinstance(event, HelperMetricsUpdated)

        grant_uc = GrantExpertRewardUseCase(self._uow)

        # --- Reputation recalculation ---
        reputation_score = self._calculate_reputation(event)
        grant_uc.execute(
            learner_id=event.learner_id,
            reward_type="reputation",
            entry_id=str(uuid.uuid4()),
            amount=reputation_score,
            cohort_id=event.cohort_id,
            triggering_event="HelperMetricsUpdated",
        )

        # --- Credits milestone (catch-up) ---
        expected_credits = (
            event.learners_helped // _MILESTONE_STEP
        ) * _CREDITS_PER_MILESTONE
        if expected_credits <= 0:
            return

        # Read current raw credits from the ledger (before any cap)
        ledger = self._uow.reward_ledgers.find_by_learner(event.learner_id)
        raw_credits = 0
        if ledger is not None:
            raw_credits = sum(
                e.amount
                for e in ledger.entries
                if e.reward_type == "credits" and e.amount is not None
            )

        credits_to_grant = expected_credits - raw_credits
        if credits_to_grant > 0:
            grant_uc.execute(
                learner_id=event.learner_id,
                reward_type="credits",
                entry_id=str(uuid.uuid4()),
                amount=credits_to_grant,
                cohort_id=event.cohort_id,
                triggering_event="HelperMetricsUpdated",
            )

    @staticmethod
    def _calculate_reputation(event: HelperMetricsUpdated) -> int:
        """Compute reputation score from helper activity counts.

        Formula: tasks_reviewed × 3 + learners_helped × 2
        Produces higher scores for more helping activity.
        """
        return event.tasks_reviewed * 3 + event.learners_helped * 2
