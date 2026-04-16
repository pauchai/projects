"""Commission aggregate for the Partnership bounded context."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from partnership.domain.events import CurationCommissionEarned, PayoutReleased
from partnership.domain.value_objects import HoldPolicy, Payout
from shared_kernel.events import DomainEvent


class CommissionStatus(Enum):
    PENDING = "PENDING"
    RELEASED = "RELEASED"


_DEFAULT_HOLD_POLICY = HoldPolicy()


class Commission:
    """Aggregate root representing a curation commission earned by a curator.

    Business rules:
    - A commission starts in PENDING status.
    - It can only be released after ``release_eligible_at`` (hold period).
    - It can only be released if the total (base + bonus) >= 50 (minimum threshold).
    - Once RELEASED, the status is final — subsequent release attempts raise.
    - Emits ``CurationCommissionEarned`` on creation.
    - Emits ``PayoutReleased`` on successful release.
    """

    def __init__(
        self,
        commission_id: str,
        curator_id: str,
        cohort_id: str,
        module_id: str,
        base_amount: Decimal,
        bonus_amount: Decimal,
        status: CommissionStatus,
        earned_at: datetime,
        release_eligible_at: datetime,
        released_at: datetime | None,
    ) -> None:
        self.commission_id = commission_id
        self.curator_id = curator_id
        self.cohort_id = cohort_id
        self.module_id = module_id
        self.base_amount = base_amount
        self.bonus_amount = bonus_amount
        self.status = status
        self.earned_at = earned_at
        self.release_eligible_at = release_eligible_at
        self.released_at = released_at
        self._events: list[DomainEvent] = []

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        commission_id: str,
        curator_id: str,
        cohort_id: str,
        module_id: str,
        base_amount: Decimal,
        bonus_amount: Decimal,
        earned_at: datetime,
        hold_policy: HoldPolicy = _DEFAULT_HOLD_POLICY,
    ) -> "Commission":
        """Create a new Commission and emit ``CurationCommissionEarned``."""
        commission = cls(
            commission_id=commission_id,
            curator_id=curator_id,
            cohort_id=cohort_id,
            module_id=module_id,
            base_amount=base_amount,
            bonus_amount=bonus_amount,
            status=CommissionStatus.PENDING,
            earned_at=earned_at,
            release_eligible_at=hold_policy.release_eligible_at(earned_at),
            released_at=None,
        )
        commission._emit(
            CurationCommissionEarned(
                commission_id=commission_id,
                curator_id=curator_id,
                cohort_id=cohort_id,
                module_id=module_id,
                base_amount=base_amount,
                bonus_amount=bonus_amount,
            )
        )
        return commission

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def release(self, now: datetime) -> None:
        """Release this commission payout.

        Raises:
            ValueError: if the commission is already released.
            ValueError: if the hold period has not elapsed yet.
            ValueError: if the total is below the minimum payout threshold.
        """
        if self.status == CommissionStatus.RELEASED:
            raise ValueError(f"Commission {self.commission_id} is already released.")
        if now < self.release_eligible_at:
            raise ValueError(
                f"Commission {self.commission_id} cannot be released before "
                f"hold period ends at {self.release_eligible_at} (now={now})."
            )
        payout = Payout(base_amount=self.base_amount, bonus_amount=self.bonus_amount)
        if not payout.meets_minimum_threshold():
            raise ValueError(
                f"Commission {self.commission_id} total {payout.total} is below "
                f"the minimum threshold of {payout.total.__class__.__name__}."
            )
        self.status = CommissionStatus.RELEASED
        self.released_at = now
        self._emit(
            PayoutReleased(
                commission_id=self.commission_id,
                curator_id=self.curator_id,
                total_amount=payout.total,
            )
        )

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
