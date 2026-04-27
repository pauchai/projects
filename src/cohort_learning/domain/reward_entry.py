"""RewardEntry value object — a single immutable entry in the RewardLedger."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RewardEntry:
    """Immutable record of a single reward granted to a learner.

    Reward types:
    - ``xp``         — Experience Points (integer amount)
    - ``badge``      — Topic Expert badge (amount=None, metadata has badge_topic_id)
    - ``credits``    — Learning credit percentage (integer amount, 1-50 total)
    - ``reputation`` — Reputation score snapshot (integer amount)

    The ledger is append-only: entries are never modified or deleted.
    """

    entry_id: str
    learner_id: str
    reward_type: str  # 'xp' | 'badge' | 'credits' | 'reputation'
    amount: int | None  # None for badge entries
    metadata: dict[str, str]
    granted_at: datetime
    triggering_event: str | None  # event class name that triggered this reward
    cohort_id: str | None  # cohort context, if applicable
