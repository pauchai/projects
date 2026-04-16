"""Tests for GrantExpertRewardUseCase."""

from __future__ import annotations

import pytest

from cohort_learning.application.grant_expert_reward import GrantExpertRewardUseCase
from cohort_learning.domain.events import ExpertRewardGranted
from cohort_learning.domain.reward_ledger import RewardLedger
from tests.cohort_learning.fakes.fake_unit_of_work import FakeUnitOfWork


class TestGrantExpertRewardUseCase:
    """Tests for granting rewards to learners via GrantExpertRewardUseCase."""

    # ------------------------------------------------------------------
    # XP rewards
    # ------------------------------------------------------------------

    def test_grants_xp_creates_new_ledger(self) -> None:
        """Granting XP to a new learner creates a RewardLedger for them."""
        uow = FakeUnitOfWork()
        use_case = GrantExpertRewardUseCase(uow)

        use_case.execute(
            learner_id="learner1",
            reward_type="xp",
            entry_id="entry1",
            amount=10,
        )

        ledger = uow.reward_ledgers.find_by_learner("learner1")
        assert ledger is not None
        assert ledger.get_balance().total_xp == 10

    def test_grants_xp_accumulates_on_existing_ledger(self) -> None:
        """Granting XP multiple times accumulates in the ledger."""
        uow = FakeUnitOfWork()
        use_case = GrantExpertRewardUseCase(uow)

        use_case.execute(
            learner_id="learner1", reward_type="xp", entry_id="e1", amount=10
        )
        use_case.execute(
            learner_id="learner1", reward_type="xp", entry_id="e2", amount=25
        )

        balance = uow.reward_ledgers.find_by_learner("learner1").get_balance()
        assert balance.total_xp == 35

    def test_grants_xp_with_cohort_id(self) -> None:
        """cohort_id is stored in the ledger entry."""
        uow = FakeUnitOfWork()
        use_case = GrantExpertRewardUseCase(uow)

        use_case.execute(
            learner_id="learner1",
            reward_type="xp",
            entry_id="e1",
            amount=10,
            cohort_id="cohort1",
        )

        ledger = uow.reward_ledgers.find_by_learner("learner1")
        assert ledger is not None
        entry = ledger.entries[0]
        assert entry.cohort_id == "cohort1"

    def test_grants_xp_with_triggering_event(self) -> None:
        """triggering_event is stored in the ledger entry."""
        uow = FakeUnitOfWork()
        use_case = GrantExpertRewardUseCase(uow)

        use_case.execute(
            learner_id="learner1",
            reward_type="xp",
            entry_id="e1",
            amount=10,
            triggering_event="PeerReviewSubmitted",
        )

        entry = uow.reward_ledgers.find_by_learner("learner1").entries[0]
        assert entry.triggering_event == "PeerReviewSubmitted"

    # ------------------------------------------------------------------
    # Badge rewards
    # ------------------------------------------------------------------

    def test_grants_badge(self) -> None:
        """Granting a badge adds it to the ledger."""
        uow = FakeUnitOfWork()
        use_case = GrantExpertRewardUseCase(uow)

        use_case.execute(
            learner_id="learner1",
            reward_type="badge",
            entry_id="e1",
            topic_id="topic-python",
        )

        balance = uow.reward_ledgers.find_by_learner("learner1").get_balance()
        assert "topic-python" in balance.badges

    def test_grants_badge_idempotent(self) -> None:
        """Granting same badge twice results in only one badge in balance."""
        uow = FakeUnitOfWork()
        use_case = GrantExpertRewardUseCase(uow)

        use_case.execute(
            learner_id="learner1",
            reward_type="badge",
            entry_id="e1",
            topic_id="topic-python",
        )
        use_case.execute(
            learner_id="learner1",
            reward_type="badge",
            entry_id="e2",
            topic_id="topic-python",
        )

        balance = uow.reward_ledgers.find_by_learner("learner1").get_balance()
        assert balance.badges.count("topic-python") == 1

    def test_grants_badge_different_topics(self) -> None:
        """Two different topic badges are both added."""
        uow = FakeUnitOfWork()
        use_case = GrantExpertRewardUseCase(uow)

        use_case.execute(
            learner_id="learner1",
            reward_type="badge",
            entry_id="e1",
            topic_id="topic-a",
        )
        use_case.execute(
            learner_id="learner1",
            reward_type="badge",
            entry_id="e2",
            topic_id="topic-b",
        )

        balance = uow.reward_ledgers.find_by_learner("learner1").get_balance()
        assert "topic-a" in balance.badges
        assert "topic-b" in balance.badges

    def test_grants_badge_requires_topic_id(self) -> None:
        """Granting a badge without topic_id raises ValueError."""
        uow = FakeUnitOfWork()
        use_case = GrantExpertRewardUseCase(uow)

        with pytest.raises(ValueError, match="topic_id"):
            use_case.execute(learner_id="learner1", reward_type="badge", entry_id="e1")

    # ------------------------------------------------------------------
    # Credits rewards
    # ------------------------------------------------------------------

    def test_grants_credits(self) -> None:
        """Granting credits adds to the ledger."""
        uow = FakeUnitOfWork()
        use_case = GrantExpertRewardUseCase(uow)

        use_case.execute(
            learner_id="learner1", reward_type="credits", entry_id="e1", amount=5
        )

        balance = uow.reward_ledgers.find_by_learner("learner1").get_balance()
        assert balance.total_credits == 5

    def test_grants_credits_capped_at_50(self) -> None:
        """Credits are capped at 50% in the balance."""
        uow = FakeUnitOfWork()
        use_case = GrantExpertRewardUseCase(uow)

        for i in range(12):
            use_case.execute(
                learner_id="learner1",
                reward_type="credits",
                entry_id=f"e{i}",
                amount=5,
            )

        balance = uow.reward_ledgers.find_by_learner("learner1").get_balance()
        assert balance.total_credits == 50

    # ------------------------------------------------------------------
    # Reputation updates
    # ------------------------------------------------------------------

    def test_updates_reputation(self) -> None:
        """Updating reputation stores the score in the ledger."""
        uow = FakeUnitOfWork()
        use_case = GrantExpertRewardUseCase(uow)

        use_case.execute(
            learner_id="learner1", reward_type="reputation", entry_id="e1", amount=42
        )

        balance = uow.reward_ledgers.find_by_learner("learner1").get_balance()
        assert balance.reputation_score == 42

    def test_reputation_update_uses_latest_score(self) -> None:
        """The most recent reputation entry wins."""
        uow = FakeUnitOfWork()
        use_case = GrantExpertRewardUseCase(uow)

        use_case.execute(
            learner_id="learner1", reward_type="reputation", entry_id="e1", amount=30
        )
        use_case.execute(
            learner_id="learner1", reward_type="reputation", entry_id="e2", amount=75
        )

        balance = uow.reward_ledgers.find_by_learner("learner1").get_balance()
        assert balance.reputation_score == 75

    # ------------------------------------------------------------------
    # Error cases
    # ------------------------------------------------------------------

    def test_raises_for_unknown_reward_type(self) -> None:
        """Unknown reward_type raises ValueError."""
        uow = FakeUnitOfWork()
        use_case = GrantExpertRewardUseCase(uow)

        with pytest.raises(ValueError, match="reward_type"):
            use_case.execute(
                learner_id="learner1", reward_type="unknown", entry_id="e1"
            )

    def test_raises_for_xp_without_amount(self) -> None:
        """XP reward without amount raises ValueError."""
        uow = FakeUnitOfWork()
        use_case = GrantExpertRewardUseCase(uow)

        with pytest.raises(ValueError, match="amount"):
            use_case.execute(learner_id="learner1", reward_type="xp", entry_id="e1")

    def test_raises_for_credits_without_amount(self) -> None:
        """Credits reward without amount raises ValueError."""
        uow = FakeUnitOfWork()
        use_case = GrantExpertRewardUseCase(uow)

        with pytest.raises(ValueError, match="amount"):
            use_case.execute(
                learner_id="learner1", reward_type="credits", entry_id="e1"
            )

    # ------------------------------------------------------------------
    # Infrastructure behaviour
    # ------------------------------------------------------------------

    def test_committed_after_execution(self) -> None:
        """UoW is committed after granting a reward."""
        uow = FakeUnitOfWork()
        use_case = GrantExpertRewardUseCase(uow)

        use_case.execute(
            learner_id="learner1", reward_type="xp", entry_id="e1", amount=10
        )

        assert uow.committed is True

    def test_xp_grant_emits_expert_reward_granted_event(self) -> None:
        """Granting XP emits ExpertRewardGranted domain event."""
        from shared_kernel.in_process_event_bus import InProcessEventBus
        from shared_kernel.events import DomainEvent

        captured: list[DomainEvent] = []

        class CapturingHandler:
            def handle(self, event: DomainEvent) -> None:
                captured.append(event)

        bus = InProcessEventBus()
        bus.subscribe(ExpertRewardGranted, CapturingHandler())

        uow = FakeUnitOfWork(event_bus=bus)
        use_case = GrantExpertRewardUseCase(uow)
        use_case.execute(
            learner_id="learner1", reward_type="xp", entry_id="e1", amount=10
        )

        assert len(captured) == 1
        event = captured[0]
        assert isinstance(event, ExpertRewardGranted)
        assert event.learner_id == "learner1"
        assert event.reward_type == "xp"
        assert event.amount == 10
