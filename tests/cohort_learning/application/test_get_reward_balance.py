"""Tests for GetRewardBalanceUseCase."""

from __future__ import annotations

from cohort_learning.application.get_reward_balance import GetRewardBalanceUseCase
from cohort_learning.domain.reward_ledger import RewardBalance, RewardLedger
from tests.cohort_learning.fakes.fake_unit_of_work import FakeUnitOfWork


class TestGetRewardBalanceUseCase:
    """Tests for retrieving a learner's reward balance."""

    def _make_ledger(self, learner_id: str) -> RewardLedger:
        return RewardLedger(learner_id=learner_id)

    def test_returns_empty_balance_when_no_ledger_exists(self) -> None:
        """Returns zeroed balance when no ledger has been created for the learner."""
        uow = FakeUnitOfWork()
        use_case = GetRewardBalanceUseCase(uow)

        balance = use_case.execute(learner_id="learner1")

        assert isinstance(balance, RewardBalance)
        assert balance.learner_id == "learner1"
        assert balance.total_xp == 0
        assert balance.total_credits == 0
        assert balance.badges == []
        assert balance.reputation_score is None

    def test_returns_balance_with_accumulated_xp(self) -> None:
        """Returns the correct XP balance when entries exist."""
        from datetime import datetime, timezone

        ledger = self._make_ledger("learner1")
        ledger.add_xp("e1", 10, "PeerReviewSubmitted", datetime.now(timezone.utc))
        ledger.add_xp("e2", 25, None, datetime.now(timezone.utc))
        ledger.collect_events()  # clear events before saving

        uow = FakeUnitOfWork()
        uow.reward_ledgers.save(ledger)

        balance = GetRewardBalanceUseCase(uow).execute("learner1")

        assert balance.total_xp == 35

    def test_returns_balance_with_credits(self) -> None:
        """Returns the correct credits balance."""
        from datetime import datetime, timezone

        ledger = self._make_ledger("learner1")
        ledger.add_credits("e1", 5, None, datetime.now(timezone.utc))
        ledger.add_credits("e2", 10, None, datetime.now(timezone.utc))
        ledger.collect_events()

        uow = FakeUnitOfWork()
        uow.reward_ledgers.save(ledger)

        balance = GetRewardBalanceUseCase(uow).execute("learner1")

        assert balance.total_credits == 15

    def test_returns_credits_capped_at_50(self) -> None:
        """Credits are capped at 50 in the returned balance."""
        from datetime import datetime, timezone

        ledger = self._make_ledger("learner1")
        for i in range(12):
            ledger.add_credits(f"e{i}", 5, None, datetime.now(timezone.utc))
        ledger.collect_events()

        uow = FakeUnitOfWork()
        uow.reward_ledgers.save(ledger)

        balance = GetRewardBalanceUseCase(uow).execute("learner1")

        assert balance.total_credits == 50

    def test_returns_balance_with_badges(self) -> None:
        """Earned badges appear in the returned balance."""
        from datetime import datetime, timezone

        ledger = self._make_ledger("learner1")
        ledger.add_badge("e1", "topic-python", None, datetime.now(timezone.utc))
        ledger.add_badge("e2", "topic-django", None, datetime.now(timezone.utc))
        ledger.collect_events()

        uow = FakeUnitOfWork()
        uow.reward_ledgers.save(ledger)

        balance = GetRewardBalanceUseCase(uow).execute("learner1")

        assert "topic-python" in balance.badges
        assert "topic-django" in balance.badges

    def test_returns_latest_reputation_score(self) -> None:
        """The most recent reputation score is returned."""
        from datetime import datetime, timezone

        ledger = self._make_ledger("learner1")
        ledger.update_reputation("e1", 40, datetime.now(timezone.utc))
        ledger.update_reputation("e2", 85, datetime.now(timezone.utc))

        uow = FakeUnitOfWork()
        uow.reward_ledgers.save(ledger)

        balance = GetRewardBalanceUseCase(uow).execute("learner1")

        assert balance.reputation_score == 85

    def test_isolates_balances_per_learner(self) -> None:
        """Two learners have independent reward balances."""
        from datetime import datetime, timezone

        ledger_a = self._make_ledger("learner-a")
        ledger_a.add_xp("e1", 100, None, datetime.now(timezone.utc))
        ledger_a.collect_events()

        ledger_b = self._make_ledger("learner-b")
        ledger_b.add_xp("e2", 5, None, datetime.now(timezone.utc))
        ledger_b.collect_events()

        uow = FakeUnitOfWork()
        uow.reward_ledgers.save(ledger_a)
        uow.reward_ledgers.save(ledger_b)

        assert GetRewardBalanceUseCase(uow).execute("learner-a").total_xp == 100
        assert GetRewardBalanceUseCase(uow).execute("learner-b").total_xp == 5
