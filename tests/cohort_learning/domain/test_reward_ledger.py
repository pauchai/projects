"""Tests for RewardLedger aggregate and RewardBalance value object."""

from datetime import datetime, UTC

import pytest

from cohort_learning.domain.reward_ledger import RewardBalance, RewardLedger
from cohort_learning.domain.events import ExpertRewardGranted


_T = datetime(2026, 4, 16, 12, 0, 0, tzinfo=UTC)
_T2 = datetime(2026, 4, 16, 13, 0, 0, tzinfo=UTC)
_T3 = datetime(2026, 4, 16, 14, 0, 0, tzinfo=UTC)


class TestRewardLedgerCreation:
    def test_new_ledger_has_zero_xp(self) -> None:
        ledger = RewardLedger(learner_id="learner1")

        balance = ledger.get_balance()

        assert balance.total_xp == 0

    def test_new_ledger_has_zero_credits(self) -> None:
        ledger = RewardLedger(learner_id="learner1")

        balance = ledger.get_balance()

        assert balance.total_credits == 0

    def test_new_ledger_has_no_badges(self) -> None:
        ledger = RewardLedger(learner_id="learner1")

        balance = ledger.get_balance()

        assert balance.badges == []

    def test_new_ledger_has_no_reputation(self) -> None:
        ledger = RewardLedger(learner_id="learner1")

        balance = ledger.get_balance()

        assert balance.reputation_score is None

    def test_new_ledger_has_no_entries(self) -> None:
        ledger = RewardLedger(learner_id="learner1")

        assert ledger.entries == []


class TestAddXp:
    def test_add_xp_increases_total(self) -> None:
        ledger = RewardLedger(learner_id="learner1")

        ledger.add_xp(
            entry_id="e1",
            amount=10,
            triggering_event="PeerReviewSubmitted",
            granted_at=_T,
        )

        assert ledger.get_balance().total_xp == 10

    def test_add_xp_multiple_times_accumulates(self) -> None:
        ledger = RewardLedger(learner_id="learner1")

        ledger.add_xp(entry_id="e1", amount=10, triggering_event=None, granted_at=_T)
        ledger.add_xp(entry_id="e2", amount=25, triggering_event=None, granted_at=_T2)

        assert ledger.get_balance().total_xp == 35

    def test_add_xp_appends_entry(self) -> None:
        ledger = RewardLedger(learner_id="learner1")

        ledger.add_xp(entry_id="e1", amount=10, triggering_event=None, granted_at=_T)

        assert len(ledger.entries) == 1
        assert ledger.entries[0].reward_type == "xp"
        assert ledger.entries[0].amount == 10

    def test_add_xp_emits_reward_granted_event(self) -> None:
        ledger = RewardLedger(learner_id="learner1")

        ledger.add_xp(
            entry_id="e1",
            amount=10,
            triggering_event="PeerReviewSubmitted",
            granted_at=_T,
            cohort_id="c1",
        )
        events = ledger.collect_events()

        assert len(events) == 1
        assert isinstance(events[0], ExpertRewardGranted)
        assert events[0].learner_id == "learner1"
        assert events[0].reward_type == "xp"
        assert events[0].amount == 10
        assert events[0].cohort_id == "c1"

    def test_add_xp_with_metadata(self) -> None:
        ledger = RewardLedger(learner_id="learner1")

        ledger.add_xp(
            entry_id="e1",
            amount=10,
            triggering_event=None,
            granted_at=_T,
            metadata={"action": "peer_review"},
        )

        assert ledger.entries[0].metadata == {"action": "peer_review"}


class TestAddBadge:
    def test_add_badge_appears_in_balance(self) -> None:
        ledger = RewardLedger(learner_id="learner1")

        ledger.add_badge(
            entry_id="e1",
            topic_id="t1",
            triggering_event="TopicExpertPromoted",
            granted_at=_T,
            cohort_id="c1",
        )

        assert "t1" in ledger.get_balance().badges

    def test_add_badge_for_different_topics(self) -> None:
        ledger = RewardLedger(learner_id="learner1")

        ledger.add_badge(
            entry_id="e1", topic_id="t1", triggering_event=None, granted_at=_T
        )
        ledger.add_badge(
            entry_id="e2", topic_id="t2", triggering_event=None, granted_at=_T2
        )

        balance = ledger.get_balance()
        assert "t1" in balance.badges
        assert "t2" in balance.badges
        assert len(balance.badges) == 2

    def test_add_badge_same_topic_is_idempotent(self) -> None:
        """Second badge for the same topic is silently ignored."""
        ledger = RewardLedger(learner_id="learner1")

        ledger.add_badge(
            entry_id="e1", topic_id="t1", triggering_event=None, granted_at=_T
        )
        ledger.add_badge(
            entry_id="e2", topic_id="t1", triggering_event=None, granted_at=_T2
        )

        assert len(ledger.get_balance().badges) == 1
        # Only one entry in the ledger
        badge_entries = [e for e in ledger.entries if e.reward_type == "badge"]
        assert len(badge_entries) == 1

    def test_add_badge_emits_event(self) -> None:
        ledger = RewardLedger(learner_id="learner1")

        ledger.add_badge(
            entry_id="e1",
            topic_id="t1",
            triggering_event="TopicExpertPromoted",
            granted_at=_T,
            cohort_id="c1",
        )
        events = ledger.collect_events()

        assert len(events) == 1
        assert isinstance(events[0], ExpertRewardGranted)
        assert events[0].reward_type == "badge"
        assert events[0].amount is None

    def test_add_badge_duplicate_does_not_emit_event(self) -> None:
        """Idempotent add: no event when badge already exists."""
        ledger = RewardLedger(learner_id="learner1")

        ledger.add_badge(
            entry_id="e1", topic_id="t1", triggering_event=None, granted_at=_T
        )
        ledger.collect_events()  # consume first event

        ledger.add_badge(
            entry_id="e2", topic_id="t1", triggering_event=None, granted_at=_T2
        )
        events = ledger.collect_events()

        assert events == []


class TestAddCredits:
    def test_add_credits_increases_total(self) -> None:
        ledger = RewardLedger(learner_id="learner1")

        ledger.add_credits(
            entry_id="e1",
            amount=5,
            triggering_event="LearnersMilestone",
            granted_at=_T,
        )

        assert ledger.get_balance().total_credits == 5

    def test_add_credits_accumulates(self) -> None:
        ledger = RewardLedger(learner_id="learner1")

        ledger.add_credits(
            entry_id="e1", amount=5, triggering_event=None, granted_at=_T
        )
        ledger.add_credits(
            entry_id="e2", amount=10, triggering_event=None, granted_at=_T2
        )

        assert ledger.get_balance().total_credits == 15

    def test_credits_capped_at_50(self) -> None:
        ledger = RewardLedger(learner_id="learner1")

        ledger.add_credits(
            entry_id="e1", amount=30, triggering_event=None, granted_at=_T
        )
        ledger.add_credits(
            entry_id="e2", amount=30, triggering_event=None, granted_at=_T2
        )

        assert ledger.get_balance().total_credits == 50

    def test_credits_at_cap_no_further_increase(self) -> None:
        ledger = RewardLedger(learner_id="learner1")

        ledger.add_credits(
            entry_id="e1", amount=50, triggering_event=None, granted_at=_T
        )
        ledger.add_credits(
            entry_id="e2", amount=5, triggering_event=None, granted_at=_T2
        )

        assert ledger.get_balance().total_credits == 50

    def test_add_credits_emits_event(self) -> None:
        ledger = RewardLedger(learner_id="learner1")

        ledger.add_credits(
            entry_id="e1",
            amount=5,
            triggering_event="LearnersMilestone",
            granted_at=_T,
            cohort_id="c1",
        )
        events = ledger.collect_events()

        assert len(events) == 1
        assert isinstance(events[0], ExpertRewardGranted)
        assert events[0].reward_type == "credits"
        assert events[0].amount == 5


class TestUpdateReputation:
    def test_update_reputation_sets_score(self) -> None:
        ledger = RewardLedger(learner_id="learner1")

        ledger.update_reputation(
            entry_id="e1",
            score=75,
            granted_at=_T,
            cohort_id="c1",
        )

        assert ledger.get_balance().reputation_score == 75

    def test_update_reputation_keeps_latest(self) -> None:
        """Reputation score is the most recently added entry's value."""
        ledger = RewardLedger(learner_id="learner1")

        ledger.update_reputation(entry_id="e1", score=60, granted_at=_T, cohort_id="c1")
        ledger.update_reputation(
            entry_id="e2", score=80, granted_at=_T2, cohort_id="c1"
        )

        assert ledger.get_balance().reputation_score == 80

    def test_update_reputation_appends_entry(self) -> None:
        """Each update is stored as a new entry (immutable ledger)."""
        ledger = RewardLedger(learner_id="learner1")

        ledger.update_reputation(entry_id="e1", score=60, granted_at=_T, cohort_id="c1")
        ledger.update_reputation(
            entry_id="e2", score=80, granted_at=_T2, cohort_id="c1"
        )

        rep_entries = [e for e in ledger.entries if e.reward_type == "reputation"]
        assert len(rep_entries) == 2

    def test_update_reputation_does_not_emit_event(self) -> None:
        """Reputation recalculation is internal — no ExpertRewardGranted event."""
        ledger = RewardLedger(learner_id="learner1")

        ledger.update_reputation(entry_id="e1", score=75, granted_at=_T, cohort_id="c1")
        events = ledger.collect_events()

        assert events == []


class TestGetBalance:
    def test_balance_contains_learner_id(self) -> None:
        ledger = RewardLedger(learner_id="learner1")

        assert ledger.get_balance().learner_id == "learner1"

    def test_balance_with_mixed_rewards(self) -> None:
        ledger = RewardLedger(learner_id="learner1")

        ledger.add_xp(entry_id="e1", amount=10, triggering_event=None, granted_at=_T)
        ledger.add_xp(entry_id="e2", amount=20, triggering_event=None, granted_at=_T2)
        ledger.add_badge(
            entry_id="e3", topic_id="t1", triggering_event=None, granted_at=_T
        )
        ledger.add_badge(
            entry_id="e4", topic_id="t2", triggering_event=None, granted_at=_T2
        )
        ledger.add_credits(
            entry_id="e5", amount=5, triggering_event=None, granted_at=_T
        )
        ledger.update_reputation(entry_id="e6", score=70, granted_at=_T, cohort_id="c1")

        balance = ledger.get_balance()

        assert balance.total_xp == 30
        assert len(balance.badges) == 2
        assert balance.total_credits == 5
        assert balance.reputation_score == 70

    def test_balance_is_immutable_value_object(self) -> None:
        ledger = RewardLedger(learner_id="learner1")
        balance = ledger.get_balance()

        with pytest.raises((AttributeError, TypeError)):
            balance.total_xp = 999  # type: ignore[misc]


class TestCollectEvents:
    def test_collect_events_clears_the_list(self) -> None:
        ledger = RewardLedger(learner_id="learner1")
        ledger.add_xp(entry_id="e1", amount=10, triggering_event=None, granted_at=_T)

        first = ledger.collect_events()
        second = ledger.collect_events()

        assert len(first) == 1
        assert second == []

    def test_multiple_actions_produce_multiple_events(self) -> None:
        ledger = RewardLedger(learner_id="learner1")

        ledger.add_xp(entry_id="e1", amount=10, triggering_event=None, granted_at=_T)
        ledger.add_badge(
            entry_id="e2", topic_id="t1", triggering_event=None, granted_at=_T2
        )
        ledger.add_credits(
            entry_id="e3", amount=5, triggering_event=None, granted_at=_T3
        )

        events = ledger.collect_events()

        assert len(events) == 3

    def test_entries_list_is_readonly_copy(self) -> None:
        """Mutating the returned entries list does not affect the ledger."""
        ledger = RewardLedger(learner_id="learner1")
        ledger.add_xp(entry_id="e1", amount=10, triggering_event=None, granted_at=_T)

        entries = ledger.entries
        entries.clear()

        assert len(ledger.entries) == 1
