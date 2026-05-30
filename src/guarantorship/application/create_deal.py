"""CreateDealUseCase — stub deal creation."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from guarantorship.domain.deal import Deal, DealStatus
from guarantorship.domain.ports import GuarantorshipUnitOfWork


@dataclass
class CreateDealCommand:
    initiator_id: str
    counterparty_id: str
    amount: Decimal


class CreateDealUseCase:
    def __init__(self, uow: GuarantorshipUnitOfWork) -> None:
        self._uow = uow

    def execute(self, cmd: CreateDealCommand) -> Deal:
        if cmd.initiator_id == cmd.counterparty_id:
            raise ValueError("A deal must be between two different users")
        if cmd.amount <= Decimal("0"):
            raise ValueError("Deal amount must be positive")

        with self._uow as uow:
            deal = Deal(
                deal_id=str(uuid.uuid4()),
                initiator_id=cmd.initiator_id,
                counterparty_id=cmd.counterparty_id,
                amount=cmd.amount,
                status=DealStatus.PENDING,
                created_at=datetime.now(timezone.utc),
            )
            uow.deals.save(deal)
            uow.commit()
            return deal
