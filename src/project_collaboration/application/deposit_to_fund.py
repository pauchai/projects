"""DepositToFundUseCase — add funds to a project's fund balance."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from project_collaboration.domain.fund import ProjectFund
from project_collaboration.domain.ports import UnitOfWork


@dataclass
class DepositToFundCommand:
    project_id: str
    amount: Decimal
    source: str = "manual"
    ref_id: str | None = None


class DepositToFundUseCase:
    """Deposit a net amount into the project fund.

    Creates the ProjectFund record on first deposit (idempotent bootstrap).
    The *amount* is assumed to be already net of any partner commission —
    the caller is responsible for computing the net figure.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, cmd: DepositToFundCommand) -> ProjectFund:
        with self._uow as uow:
            fund = uow.fund.find_by_project(cmd.project_id)
            if fund is None:
                fund = ProjectFund(
                    fund_id=str(uuid.uuid4()),
                    project_id=cmd.project_id,
                )

            tx = fund.deposit(
                transaction_id=str(uuid.uuid4()),
                amount=cmd.amount,
                source=cmd.source,
                ref_id=cmd.ref_id,
            )

            uow.fund.save(fund)
            uow.fund.save_transaction(tx)
            uow.commit()

        return fund
