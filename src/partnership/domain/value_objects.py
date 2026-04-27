"""Value objects for the Partnership bounded context."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

MINIMUM_PAYOUT_THRESHOLD = Decimal("50.00")
DEFAULT_HOLD_DAYS = 30


@dataclass(frozen=True)
class HoldPolicy:
    """Defines the hold period before a payout can be released.

    Business rule: commissions cannot be released before
    ``hold_days`` have elapsed since ``earned_at``.
    """

    hold_days: int = DEFAULT_HOLD_DAYS

    def release_eligible_at(self, earned_at: datetime) -> datetime:
        """Return the datetime when the commission becomes releasable."""
        return earned_at + timedelta(days=self.hold_days)


@dataclass(frozen=True)
class Payout:
    """Represents the monetary amounts for a single commission.

    ``base_amount`` — calculated from cohort_size * curator_score * base_rate.
    ``bonus_amount`` — quality bonus (0 if no bonus applies).
    ``total``        — sum of both amounts.
    """

    base_amount: Decimal
    bonus_amount: Decimal

    @property
    def total(self) -> Decimal:
        return self.base_amount + self.bonus_amount

    def meets_minimum_threshold(self) -> bool:
        """Return True if total is at or above the minimum payout threshold."""
        return self.total >= MINIMUM_PAYOUT_THRESHOLD
