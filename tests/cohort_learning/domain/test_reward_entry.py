"""Tests for RewardEntry value object."""

from datetime import datetime, UTC

import pytest

from cohort_learning.domain.reward_entry import RewardEntry


_GRANTED_AT = datetime(2026, 4, 16, 12, 0, 0, tzinfo=UTC)


class TestRewardEntryCreation:
    def test_create_xp_entry(self) -> None:
        entry = RewardEntry(
            entry_id="e1",
            learner_id="learner1",
            reward_type="xp",
            amount=10,
            metadata={"action": "peer_review"},
            granted_at=_GRANTED_AT,
            triggering_event="PeerReviewSubmitted",
            cohort_id="c1",
        )

        assert entry.entry_id == "e1"
        assert entry.learner_id == "learner1"
        assert entry.reward_type == "xp"
        assert entry.amount == 10
        assert entry.metadata == {"action": "peer_review"}
        assert entry.granted_at == _GRANTED_AT
        assert entry.triggering_event == "PeerReviewSubmitted"
        assert entry.cohort_id == "c1"

    def test_create_badge_entry_amount_is_none(self) -> None:
        entry = RewardEntry(
            entry_id="e2",
            learner_id="learner1",
            reward_type="badge",
            amount=None,
            metadata={"badge_topic_id": "t1"},
            granted_at=_GRANTED_AT,
            triggering_event="TopicExpertPromoted",
            cohort_id="c1",
        )

        assert entry.reward_type == "badge"
        assert entry.amount is None
        assert entry.metadata["badge_topic_id"] == "t1"

    def test_create_credits_entry(self) -> None:
        entry = RewardEntry(
            entry_id="e3",
            learner_id="learner1",
            reward_type="credits",
            amount=5,
            metadata={"reason": "learners_helped_milestone"},
            granted_at=_GRANTED_AT,
            triggering_event=None,
            cohort_id=None,
        )

        assert entry.reward_type == "credits"
        assert entry.amount == 5
        assert entry.triggering_event is None
        assert entry.cohort_id is None

    def test_create_reputation_entry(self) -> None:
        entry = RewardEntry(
            entry_id="e4",
            learner_id="learner1",
            reward_type="reputation",
            amount=42,
            metadata={},
            granted_at=_GRANTED_AT,
            triggering_event=None,
            cohort_id="c1",
        )

        assert entry.reward_type == "reputation"
        assert entry.amount == 42

    def test_entry_is_immutable(self) -> None:
        entry = RewardEntry(
            entry_id="e1",
            learner_id="learner1",
            reward_type="xp",
            amount=10,
            metadata={},
            granted_at=_GRANTED_AT,
            triggering_event=None,
            cohort_id=None,
        )

        with pytest.raises((AttributeError, TypeError)):
            entry.amount = 999  # type: ignore[misc]

    def test_entries_with_same_id_are_equal(self) -> None:
        e1 = RewardEntry(
            entry_id="e1",
            learner_id="learner1",
            reward_type="xp",
            amount=10,
            metadata={},
            granted_at=_GRANTED_AT,
            triggering_event=None,
            cohort_id=None,
        )
        e2 = RewardEntry(
            entry_id="e1",
            learner_id="learner1",
            reward_type="xp",
            amount=10,
            metadata={},
            granted_at=_GRANTED_AT,
            triggering_event=None,
            cohort_id=None,
        )

        assert e1 == e2

    def test_entries_with_different_ids_are_not_equal(self) -> None:
        e1 = RewardEntry(
            entry_id="e1",
            learner_id="learner1",
            reward_type="xp",
            amount=10,
            metadata={},
            granted_at=_GRANTED_AT,
            triggering_event=None,
            cohort_id=None,
        )
        e2 = RewardEntry(
            entry_id="e2",
            learner_id="learner1",
            reward_type="xp",
            amount=10,
            metadata={},
            granted_at=_GRANTED_AT,
            triggering_event=None,
            cohort_id=None,
        )

        assert e1 != e2
