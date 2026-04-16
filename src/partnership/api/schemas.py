"""Pydantic schemas for Partnership API request/response serialization."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, computed_field


# ---------------------------------------------------------------------------
# Response schemas — Commissions / Earnings
# ---------------------------------------------------------------------------


class CommissionResponse(BaseModel):
    """Serialized Commission aggregate."""

    commission_id: str
    curator_id: str
    cohort_id: str
    module_id: str
    base_amount: Decimal
    bonus_amount: Decimal
    total_amount: Decimal
    status: str
    earned_at: datetime
    release_eligible_at: datetime
    released_at: datetime | None


class EarningsSummaryResponse(BaseModel):
    """Aggregated earnings summary for a curator."""

    curator_id: str
    total_pending: Decimal
    total_released: Decimal
    commissions: list[CommissionResponse]
