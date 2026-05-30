from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class UserDeposit:
    """Deposit held by a guarantor on behalf of a ward."""

    deposit_id: str
    ward_id: str
    guarantor_id: str
    amount: Decimal
    blockchain_ref: str | None
    created_at: datetime
