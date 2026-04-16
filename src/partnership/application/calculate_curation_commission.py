"""CalculateCurationCommissionUseCase — creates a Commission for a curator."""

from __future__ import annotations

import uuid
from decimal import Decimal

from partnership.domain.commission import Commission
from partnership.domain.ports import UnitOfWork

BASE_RATE = Decimal("0.10")
QUALITY_BONUS_RATE = Decimal("0.05")
QUALITY_THRESHOLD = 4.5


class CalculateCurationCommissionUseCase:
    """Calculate and persist a curation commission for a single curator.

    Business rules:
    - base_amount = base_rate (10%) * cohort_size * curator_score
    - curator_score = tasks_reviewed * 3 + learners_helped * 2 (caller-computed)
    - quality_bonus = base_amount * 5% if avg_review_score > 4.5
    - Commission starts in PENDING status with a 30-day hold period
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        curator_id: str,
        cohort_id: str,
        module_id: str,
        cohort_size: int,
        curator_score: int,
        avg_review_score: float,
        commission_id: str | None = None,
    ) -> Commission:
        commission_id = commission_id or str(uuid.uuid4())

        base_amount = BASE_RATE * Decimal(cohort_size) * Decimal(curator_score)
        if avg_review_score > QUALITY_THRESHOLD:
            bonus_amount = base_amount * QUALITY_BONUS_RATE
        else:
            bonus_amount = Decimal("0.00")

        from datetime import datetime, timezone

        earned_at = datetime.now(timezone.utc)

        with self._uow as uow:
            commission = Commission.create(
                commission_id=commission_id,
                curator_id=curator_id,
                cohort_id=cohort_id,
                module_id=module_id,
                base_amount=base_amount,
                bonus_amount=bonus_amount,
                earned_at=earned_at,
            )
            uow.commissions.save(commission)
            uow.commit()
            return commission
