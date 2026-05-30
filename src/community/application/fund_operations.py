from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from community.application._helpers import get_community_or_raise, require_community_role
from community.domain.community_role import CommunityRole
from community.domain.fund import CommunityFund
from community.domain.ports import CommunityUnitOfWork


@dataclass
class DepositToFundCommand:
    community_id: str
    amount: Decimal
    source: str = "manual"
    ref_id: str | None = None


@dataclass
class DistributeFromFundCommand:
    community_id: str
    amount: Decimal
    initiated_by: str
    note: str = ""


class DepositToFundUseCase:
    def __init__(self, uow: CommunityUnitOfWork) -> None:
        self._uow = uow

    def execute(self, cmd: DepositToFundCommand, caller_id: str) -> CommunityFund:
        with self._uow as uow:
            community = get_community_or_raise(uow, cmd.community_id)
            require_community_role(community, caller_id, CommunityRole.OWNER, CommunityRole.ADMIN)

            fund = uow.fund.find_by_community(cmd.community_id)
            if fund is None:
                fund = CommunityFund(
                    fund_id=str(uuid.uuid4()),
                    community_id=cmd.community_id,
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


class DistributeFromFundUseCase:
    def __init__(self, uow: CommunityUnitOfWork) -> None:
        self._uow = uow

    def execute(self, cmd: DistributeFromFundCommand, caller_id: str) -> CommunityFund:
        with self._uow as uow:
            community = get_community_or_raise(uow, cmd.community_id)
            require_community_role(community, caller_id, CommunityRole.OWNER, CommunityRole.ADMIN)

            fund = uow.fund.find_by_community(cmd.community_id)
            if fund is None:
                raise LookupError(f"No fund found for community {cmd.community_id}")

            dist = fund.request_distribution(
                distribution_id=str(uuid.uuid4()),
                amount=cmd.amount,
                initiated_by=cmd.initiated_by,
                note=cmd.note,
            )

            uow.fund.save(fund)
            uow.fund.save_distribution(dist)
            uow.commit()

        return fund


class GetFundUseCase:
    def __init__(self, uow: CommunityUnitOfWork) -> None:
        self._uow = uow

    def execute(
        self, community_id: str, caller_id: str
    ) -> CommunityFund | None:
        with self._uow as uow:
            community = get_community_or_raise(uow, community_id)
            require_community_role(community, caller_id, CommunityRole.MEMBER)
            return uow.fund.find_by_community(community_id)
