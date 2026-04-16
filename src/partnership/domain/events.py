"""Domain events for the Partnership bounded context."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from shared_kernel.events import DomainEvent


@dataclass(frozen=True)
class CurationCommissionEarned(DomainEvent):
    """Emitted when a Commission aggregate is created for a curator."""

    commission_id: str
    curator_id: str
    cohort_id: str
    module_id: str
    base_amount: Decimal
    bonus_amount: Decimal


@dataclass(frozen=True)
class QualityBonusEarned(DomainEvent):
    """Emitted when a quality bonus is included in a commission.

    This is a supplementary event to ``CurationCommissionEarned`` and is
    emitted alongside it when the avg peer review score exceeds 4.5.
    """

    commission_id: str
    curator_id: str
    cohort_id: str
    bonus_amount: Decimal


@dataclass(frozen=True)
class PayoutReleased(DomainEvent):
    """Emitted when a curator successfully releases a pending payout."""

    commission_id: str
    curator_id: str
    total_amount: Decimal
