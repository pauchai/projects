"""Integration tests for SqlAlchemyRewardLedgerRepository.

Tests verify that RewardLedger aggregates can be saved to and loaded from
a real PostgreSQL database through the SQLAlchemy repository.  The ledger
is append-only — once entries are written they are never modified.

Covers:
- Round-trip persistence of all reward types (xp, badge, credits, reputation)
- ``find_by_learner`` returns None when no entries exist
- ``find_by_learner`` reconstructs the aggregate with correct entries
- Metadata dict[str, str] is serialised as JSON and deserialised on load
- ``get_balance()`` computes correct balances after load
- Badge idempotency survives a save/load cycle
- Credits cap (50%) is preserved through get_balance after load
- Multiple learners are isolated from each other
- Saving the same ledger twice (append-only idempotency via merge)
"""

from datetime import datetime, timezone

import pytest

from cohort_learning.domain.reward_ledger import RewardLedger
from cohort_learning.infrastructure.sqlalchemy_repository import (
    SqlAlchemyRewardLedgerRepository,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TS = datetime(2026, 4, 16, 10, 0, 0, tzinfo=timezone.utc)


def _make_ledger(learner_id: str = "learner-1") -> RewardLedger:
    """Return a fresh empty ledger."""
    return RewardLedger(learner_id)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def repo(integration_session):
    """Provide a RewardLedger repository backed by a real database session."""
    return SqlAlchemyRewardLedgerRepository(integration_session)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSqlAlchemyRewardLedgerRepository:
    """Integration tests for RewardLedger persistence."""

    # ------------------------------------------------------------------
    # find_by_learner — not found
    # ------------------------------------------------------------------

    def test_find_by_learner_returns_none_when_no_entries(self, repo):
        """Finding a learner with no ledger entries returns None."""
        # Act
        result = repo.find_by_learner("nonexistent-learner")

        # Assert
        assert result is None

    # ------------------------------------------------------------------
    # XP round-trip
    # ------------------------------------------------------------------

    def test_save_and_find_xp_entry(self, repo):
        """Saving an XP entry and loading it preserves all fields."""
        # Arrange
        ledger = _make_ledger()
        ledger.add_xp(
            entry_id="entry-xp-1",
            amount=100,
            triggering_event="PeerReviewSubmitted",
            granted_at=_TS,
            cohort_id="cohort-1",
            metadata={"review_id": "rev-1"},
        )

        # Act
        repo.save(ledger)
        loaded = repo.find_by_learner("learner-1")

        # Assert
        assert loaded is not None
        assert loaded.learner_id == "learner-1"
        assert len(loaded.entries) == 1

        entry = loaded.entries[0]
        assert entry.entry_id == "entry-xp-1"
        assert entry.reward_type == "xp"
        assert entry.amount == 100
        assert entry.triggering_event == "PeerReviewSubmitted"
        assert entry.cohort_id == "cohort-1"
        assert entry.metadata == {"review_id": "rev-1"}

    def test_xp_balance_computed_correctly_after_load(self, repo):
        """get_balance() on the loaded ledger sums XP entries correctly."""
        # Arrange
        ledger = _make_ledger("learner-xp-bal")
        ledger.add_xp("e1", 50, None, _TS)
        ledger.add_xp("e2", 75, None, _TS)

        # Act
        repo.save(ledger)
        loaded = repo.find_by_learner("learner-xp-bal")

        # Assert
        assert loaded is not None
        balance = loaded.get_balance()
        assert balance.total_xp == 125

    # ------------------------------------------------------------------
    # Badge round-trip
    # ------------------------------------------------------------------

    def test_save_and_find_badge_entry(self, repo):
        """Saving a badge entry preserves badge_topic_id in metadata."""
        # Arrange
        ledger = _make_ledger("learner-badge")
        ledger.add_badge(
            entry_id="entry-badge-1",
            topic_id="topic-python",
            triggering_event="TopicExpertPromoted",
            granted_at=_TS,
            cohort_id="cohort-1",
        )

        # Act
        repo.save(ledger)
        loaded = repo.find_by_learner("learner-badge")

        # Assert
        assert loaded is not None
        assert len(loaded.entries) == 1
        entry = loaded.entries[0]
        assert entry.reward_type == "badge"
        assert entry.amount is None
        assert entry.metadata == {"badge_topic_id": "topic-python"}

    def test_badge_list_in_balance_after_load(self, repo):
        """get_balance().badges reflects badge entries after load."""
        # Arrange
        ledger = _make_ledger("learner-badge-bal")
        ledger.add_badge("b1", "topic-1", None, _TS)
        ledger.add_badge("b2", "topic-2", None, _TS)

        # Act
        repo.save(ledger)
        loaded = repo.find_by_learner("learner-badge-bal")

        # Assert
        assert loaded is not None
        balance = loaded.get_balance()
        assert set(balance.badges) == {"topic-1", "topic-2"}

    def test_duplicate_badge_is_not_persisted(self, repo):
        """Badge idempotency: second badge for same topic produces only one entry."""
        # Arrange
        ledger = _make_ledger("learner-dup-badge")
        ledger.add_badge("b1", "topic-dup", None, _TS)
        ledger.add_badge("b2", "topic-dup", None, _TS)  # ignored by domain

        # Act
        repo.save(ledger)
        loaded = repo.find_by_learner("learner-dup-badge")

        # Assert
        assert loaded is not None
        badge_entries = [e for e in loaded.entries if e.reward_type == "badge"]
        assert len(badge_entries) == 1

    # ------------------------------------------------------------------
    # Credits round-trip
    # ------------------------------------------------------------------

    def test_save_and_find_credits_entry(self, repo):
        """Saving a credits entry preserves amount correctly."""
        # Arrange
        ledger = _make_ledger("learner-credits")
        ledger.add_credits(
            entry_id="entry-credits-1",
            amount=10,
            triggering_event="HelperMetricsUpdated",
            granted_at=_TS,
            cohort_id="cohort-2",
        )

        # Act
        repo.save(ledger)
        loaded = repo.find_by_learner("learner-credits")

        # Assert
        assert loaded is not None
        entry = loaded.entries[0]
        assert entry.reward_type == "credits"
        assert entry.amount == 10

    def test_credits_cap_applied_by_get_balance_after_load(self, repo):
        """Credits exceeding 50 are capped at 50 by get_balance() after load."""
        # Arrange
        ledger = _make_ledger("learner-credits-cap")
        ledger.add_credits("c1", 30, None, _TS)
        ledger.add_credits("c2", 30, None, _TS)  # total=60, capped to 50

        # Act
        repo.save(ledger)
        loaded = repo.find_by_learner("learner-credits-cap")

        # Assert
        assert loaded is not None
        balance = loaded.get_balance()
        assert balance.total_credits == 50

    # ------------------------------------------------------------------
    # Reputation round-trip
    # ------------------------------------------------------------------

    def test_save_and_find_reputation_entry(self, repo):
        """Saving a reputation entry preserves the score."""
        # Arrange
        ledger = _make_ledger("learner-rep")
        ledger.update_reputation("entry-rep-1", score=42, granted_at=_TS)

        # Act
        repo.save(ledger)
        loaded = repo.find_by_learner("learner-rep")

        # Assert
        assert loaded is not None
        balance = loaded.get_balance()
        assert balance.reputation_score == 42

    def test_latest_reputation_entry_wins_after_load(self, repo):
        """Most recent reputation entry is returned by get_balance() after load."""
        # Arrange
        ledger = _make_ledger("learner-rep-latest")
        ledger.update_reputation("r1", 10, _TS)
        ledger.update_reputation(
            "r2",
            99,
            datetime(2026, 4, 16, 11, 0, 0, tzinfo=timezone.utc),
        )

        # Act
        repo.save(ledger)
        loaded = repo.find_by_learner("learner-rep-latest")

        # Assert
        assert loaded is not None
        balance = loaded.get_balance()
        assert balance.reputation_score == 99

    # ------------------------------------------------------------------
    # Multiple reward types
    # ------------------------------------------------------------------

    def test_multiple_reward_types_in_single_ledger(self, repo):
        """A ledger with xp, badge, credits, and reputation all round-trips."""
        # Arrange
        ledger = _make_ledger("learner-mixed")
        ledger.add_xp("e-xp", 200, None, _TS)
        ledger.add_badge("e-badge", "topic-x", None, _TS)
        ledger.add_credits("e-credits", 15, None, _TS)
        ledger.update_reputation("e-rep", 55, _TS)

        # Act
        repo.save(ledger)
        loaded = repo.find_by_learner("learner-mixed")

        # Assert
        assert loaded is not None
        assert len(loaded.entries) == 4
        balance = loaded.get_balance()
        assert balance.total_xp == 200
        assert balance.total_credits == 15
        assert balance.badges == ["topic-x"]
        assert balance.reputation_score == 55

    # ------------------------------------------------------------------
    # Isolation between learners
    # ------------------------------------------------------------------

    def test_learners_are_isolated(self, repo):
        """Entries for one learner do not appear in another learner's ledger."""
        # Arrange
        ledger_a = RewardLedger("learner-iso-a")
        ledger_a.add_xp("xa1", 50, None, _TS)

        ledger_b = RewardLedger("learner-iso-b")
        ledger_b.add_xp("xb1", 75, None, _TS)

        # Act
        repo.save(ledger_a)
        repo.save(ledger_b)

        loaded_a = repo.find_by_learner("learner-iso-a")
        loaded_b = repo.find_by_learner("learner-iso-b")

        # Assert
        assert loaded_a is not None
        assert len(loaded_a.entries) == 1
        assert loaded_a.entries[0].amount == 50

        assert loaded_b is not None
        assert len(loaded_b.entries) == 1
        assert loaded_b.entries[0].amount == 75

    # ------------------------------------------------------------------
    # Empty metadata
    # ------------------------------------------------------------------

    def test_empty_metadata_serialised_and_deserialised(self, repo):
        """An entry with empty metadata round-trips as an empty dict."""
        # Arrange
        ledger = _make_ledger("learner-empty-meta")
        ledger.add_xp("e-empty", 10, None, _TS, metadata={})

        # Act
        repo.save(ledger)
        loaded = repo.find_by_learner("learner-empty-meta")

        # Assert
        assert loaded is not None
        assert loaded.entries[0].metadata == {}

    # ------------------------------------------------------------------
    # Append-only: saving a loaded ledger with new entries
    # ------------------------------------------------------------------

    def test_appending_entries_to_existing_ledger(self, repo):
        """Saving additional entries on a previously persisted ledger appends them."""
        # Arrange — first save
        ledger = _make_ledger("learner-append")
        ledger.add_xp("e1", 10, None, _TS)
        repo.save(ledger)

        # Load, add more, save again
        loaded = repo.find_by_learner("learner-append")
        assert loaded is not None
        loaded.add_xp("e2", 20, None, _TS)
        repo.save(loaded)

        # Act — final load
        final = repo.find_by_learner("learner-append")

        # Assert
        assert final is not None
        assert len(final.entries) == 2
        total_xp = sum(e.amount or 0 for e in final.entries if e.reward_type == "xp")
        assert total_xp == 30
