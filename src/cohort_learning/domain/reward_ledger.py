"""RewardLedger aggregate and RewardBalance value object."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from cohort_learning.domain.events import ExpertRewardGranted
from cohort_learning.domain.reward_entry import RewardEntry
from shared_kernel.events import DomainEvent

MAX_CREDITS = 50


@dataclass(frozen=True)
class RewardBalance:
    """Read-only projection of a learner's accumulated rewards.

    Computed on-demand from the RewardLedger entries:
    - ``total_xp``       — sum of all XP entries
    - ``total_credits``  — sum of all credits entries, capped at MAX_CREDITS (50%)
    - ``badges``         — deduplicated list of topic_ids with earned badges
    - ``reputation_score`` — value from the most recent reputation entry, or None
    """

    learner_id: str
    total_xp: int
    total_credits: int
    badges: list[str]
    reputation_score: int | None


class RewardLedger:
    """Append-only aggregate that records all rewards earned by a learner.

    Business rules:
    - Entries are immutable once added (append-only).
    - XP and credits accumulate; credits are capped at 50%.
    - Badges are per-topic and idempotent: a second badge for the same
      topic is silently ignored (no entry added, no event emitted).
    - Reputation score is stored as successive entries; ``get_balance()``
      returns the latest value.
    - Emits ``ExpertRewardGranted`` for XP, badge, and credits additions.
      Reputation updates are internal and do not emit an event.
    """

    def __init__(self, learner_id: str) -> None:
        self.learner_id = learner_id
        self._entries: list[RewardEntry] = []
        self._events: list[DomainEvent] = []

    # ------------------------------------------------------------------
    # Read interface
    # ------------------------------------------------------------------

    @property
    def entries(self) -> list[RewardEntry]:
        """Return a copy of all ledger entries (read-only snapshot)."""
        return list(self._entries)

    def get_balance(self) -> RewardBalance:
        """Compute the current reward balance from all entries."""
        total_xp = 0
        raw_credits = 0
        badge_topics: list[str] = []
        reputation_score: int | None = None

        for entry in self._entries:
            if entry.reward_type == "xp" and entry.amount is not None:
                total_xp += entry.amount
            elif entry.reward_type == "credits" and entry.amount is not None:
                raw_credits += entry.amount
            elif entry.reward_type == "badge":
                topic_id = entry.metadata.get("badge_topic_id", "")
                if topic_id and topic_id not in badge_topics:
                    badge_topics.append(topic_id)
            elif entry.reward_type == "reputation" and entry.amount is not None:
                reputation_score = entry.amount  # latest wins

        return RewardBalance(
            learner_id=self.learner_id,
            total_xp=total_xp,
            total_credits=min(raw_credits, MAX_CREDITS),
            badges=badge_topics,
            reputation_score=reputation_score,
        )

    # ------------------------------------------------------------------
    # Write interface
    # ------------------------------------------------------------------

    def add_xp(
        self,
        entry_id: str,
        amount: int,
        triggering_event: str | None,
        granted_at: datetime,
        cohort_id: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> None:
        """Grant XP to the learner."""
        entry = RewardEntry(
            entry_id=entry_id,
            learner_id=self.learner_id,
            reward_type="xp",
            amount=amount,
            metadata=metadata or {},
            granted_at=granted_at,
            triggering_event=triggering_event,
            cohort_id=cohort_id,
        )
        self._entries.append(entry)
        self._emit(
            ExpertRewardGranted(
                learner_id=self.learner_id,
                reward_type="xp",
                amount=amount,
                cohort_id=cohort_id,
            )
        )

    def add_badge(
        self,
        entry_id: str,
        topic_id: str,
        triggering_event: str | None,
        granted_at: datetime,
        cohort_id: str | None = None,
    ) -> None:
        """Grant a Topic Expert badge. Idempotent: duplicate topics are ignored."""
        # Check if badge already earned for this topic
        already_earned = any(
            e.reward_type == "badge" and e.metadata.get("badge_topic_id") == topic_id
            for e in self._entries
        )
        if already_earned:
            return

        entry = RewardEntry(
            entry_id=entry_id,
            learner_id=self.learner_id,
            reward_type="badge",
            amount=None,
            metadata={"badge_topic_id": topic_id},
            granted_at=granted_at,
            triggering_event=triggering_event,
            cohort_id=cohort_id,
        )
        self._entries.append(entry)
        self._emit(
            ExpertRewardGranted(
                learner_id=self.learner_id,
                reward_type="badge",
                amount=None,
                cohort_id=cohort_id,
            )
        )

    def add_credits(
        self,
        entry_id: str,
        amount: int,
        triggering_event: str | None,
        granted_at: datetime,
        cohort_id: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> None:
        """Grant learning credits (percentage). Accumulated total is capped at 50%."""
        entry = RewardEntry(
            entry_id=entry_id,
            learner_id=self.learner_id,
            reward_type="credits",
            amount=amount,
            metadata=metadata or {},
            granted_at=granted_at,
            triggering_event=triggering_event,
            cohort_id=cohort_id,
        )
        self._entries.append(entry)
        self._emit(
            ExpertRewardGranted(
                learner_id=self.learner_id,
                reward_type="credits",
                amount=amount,
                cohort_id=cohort_id,
            )
        )

    def update_reputation(
        self,
        entry_id: str,
        score: int,
        granted_at: datetime,
        cohort_id: str | None = None,
    ) -> None:
        """Store a reputation score snapshot. No event emitted (internal update)."""
        entry = RewardEntry(
            entry_id=entry_id,
            learner_id=self.learner_id,
            reward_type="reputation",
            amount=score,
            metadata={},
            granted_at=granted_at,
            triggering_event=None,
            cohort_id=cohort_id,
        )
        self._entries.append(entry)

    # ------------------------------------------------------------------
    # Event collection
    # ------------------------------------------------------------------

    def collect_events(self) -> list[DomainEvent]:
        """Return and clear all pending domain events."""
        events = list(self._events)
        self._events.clear()
        return events

    def _emit(self, event: DomainEvent) -> None:
        self._events.append(event)
