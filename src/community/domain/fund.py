from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal


class FundTransaction:
    def __init__(
        self,
        transaction_id: str,
        fund_id: str,
        amount: Decimal,
        source: str,
        *,
        ref_id: str | None = None,
        created_at: datetime | None = None,
    ) -> None:
        if amount <= Decimal("0"):
            raise ValueError("Transaction amount must be positive")
        self.transaction_id = transaction_id
        self.fund_id = fund_id
        self.amount = amount
        self.source = source
        self.ref_id = ref_id
        self.created_at = created_at or datetime.now(timezone.utc)


class FundDistribution:
    def __init__(
        self,
        distribution_id: str,
        fund_id: str,
        amount: Decimal,
        initiated_by: str,
        *,
        note: str = "",
        status: str = "pending",
        created_at: datetime | None = None,
    ) -> None:
        if amount <= Decimal("0"):
            raise ValueError("Distribution amount must be positive")
        self.distribution_id = distribution_id
        self.fund_id = fund_id
        self.amount = amount
        self.initiated_by = initiated_by
        self.note = note
        self.status = status
        self.created_at = created_at or datetime.now(timezone.utc)


class CommunityFund:
    def __init__(
        self,
        fund_id: str,
        community_id: str,
        *,
        balance: Decimal = Decimal("0"),
        updated_at: datetime | None = None,
    ) -> None:
        self.fund_id = fund_id
        self.community_id = community_id
        self.balance = balance
        self.updated_at = updated_at or datetime.now(timezone.utc)

    def deposit(
        self,
        transaction_id: str,
        amount: Decimal,
        source: str,
        ref_id: str | None = None,
    ) -> FundTransaction:
        tx = FundTransaction(
            transaction_id=transaction_id,
            fund_id=self.fund_id,
            amount=amount,
            source=source,
            ref_id=ref_id,
        )
        self.balance += amount
        self.updated_at = datetime.now(timezone.utc)
        return tx

    def request_distribution(
        self,
        distribution_id: str,
        amount: Decimal,
        initiated_by: str,
        note: str = "",
    ) -> FundDistribution:
        if amount > self.balance:
            raise ValueError(
                f"Insufficient fund balance: requested {amount}, available {self.balance}"
            )
        dist = FundDistribution(
            distribution_id=distribution_id,
            fund_id=self.fund_id,
            amount=amount,
            initiated_by=initiated_by,
            note=note,
        )
        self.balance -= amount
        self.updated_at = datetime.now(timezone.utc)
        return dist
