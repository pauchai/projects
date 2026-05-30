"""DistributeFundUseCase — create a distribution request from the project fund.

MVP stub: records the distribution with status='pending'.
The actual disbursement mechanism (voting, scheduling, per-member lines)
is a future feature in the partnership context.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from project_collaboration.domain.fund import FundDistribution
from project_collaboration.domain.ports import UnitOfWork


@dataclass
class DistributeFundCommand:
    project_id: str
    amount: Decimal
    initiated_by: str
    note: str = ""


class DistributeFundUseCase:
    """Reserve *amount* from the fund and record a pending distribution.

    Raises:
        LookupError: if no fund exists for the project.
        ValueError: if the requested amount exceeds the current balance.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, cmd: DistributeFundCommand) -> FundDistribution:
        with self._uow as uow:
            fund = uow.fund.find_by_project(cmd.project_id)
            if fund is None:
                raise LookupError(
                    f"No fund found for project '{cmd.project_id}'"
                )

            dist = fund.request_distribution(
                distribution_id=str(uuid.uuid4()),
                amount=cmd.amount,
                initiated_by=cmd.initiated_by,
                note=cmd.note,
            )

            uow.fund.save(fund)
            uow.fund.save_distribution(dist)
            uow.commit()

        return dist
