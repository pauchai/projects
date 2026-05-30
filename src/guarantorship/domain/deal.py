from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


class DealStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    DISPUTED = "disputed"
    RESOLVED = "resolved"


@dataclass
class Deal:
    """Stub: a deal between two platform users.

    Full product/service deal logic is out of scope for this MVP.
    """

    deal_id: str
    initiator_id: str
    counterparty_id: str
    amount: Decimal
    status: DealStatus
    created_at: datetime
