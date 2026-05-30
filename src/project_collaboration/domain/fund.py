"""ProjectFund domain entities.

ProjectFund   — holds the current balance for a project.
FundTransaction — immutable record of every deposit into the fund.
FundDistribution — record of a distribution event (MVP: always 'pending',
                   actual payout mechanism is a future voting/scheduling feature).
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal


class FundTransaction:
    """An immutable record of a single deposit into the project fund."""

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
    """A distribution request — money to be paid out from the fund.

    MVP: status is always 'pending'. The actual disbursement mechanism
    (voting, scheduling) is a future concern.
    """

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


class ProjectFund:
    """Aggregate root: holds the current balance for a project fund.

    All mutations go through this class to keep the invariant:
    balance >= 0 at all times.
    """

    def __init__(
        self,
        fund_id: str,
        project_id: str,
        *,
        balance: Decimal = Decimal("0"),
        updated_at: datetime | None = None,
    ) -> None:
        self.fund_id = fund_id
        self.project_id = project_id
        self.balance = balance
        self.updated_at = updated_at or datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Domain behaviour
    # ------------------------------------------------------------------

    def deposit(
        self,
        transaction_id: str,
        amount: Decimal,
        source: str,
        ref_id: str | None = None,
    ) -> FundTransaction:
        """Deposit *amount* into the fund and return the transaction record."""
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
        """Create a distribution request, reserving *amount* from balance.

        Raises ValueError if balance is insufficient.
        """
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
