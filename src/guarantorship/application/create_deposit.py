"""CreateDepositUseCase — ward creates a deposit record held by a guarantor."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from guarantorship.domain.ports import GuarantorshipUnitOfWork
from guarantorship.domain.user_deposit import UserDeposit


@dataclass
class CreateDepositCommand:
    ward_id: str
    guarantor_id: str
    amount: Decimal
    blockchain_ref: str | None = None


class CreateDepositUseCase:
    def __init__(self, uow: GuarantorshipUnitOfWork) -> None:
        self._uow = uow

    def execute(self, cmd: CreateDepositCommand) -> UserDeposit:
        if cmd.amount <= Decimal("0"):
            raise ValueError("Deposit amount must be positive")

        with self._uow as uow:
            # guarantorship must exist between ward and guarantor
            guarantorships = uow.guarantorships.find_by_ward(cmd.ward_id)
            is_guarantor = any(g.guarantor_id == cmd.guarantor_id for g in guarantorships)
            if not is_guarantor:
                raise PermissionError(
                    "A deposit can only be created with an active guarantor"
                )

            deposit = UserDeposit(
                deposit_id=str(uuid.uuid4()),
                ward_id=cmd.ward_id,
                guarantor_id=cmd.guarantor_id,
                amount=cmd.amount,
                blockchain_ref=cmd.blockchain_ref,
                created_at=datetime.now(timezone.utc),
            )
            uow.deposits.save(deposit)
            uow.commit()
            return deposit
