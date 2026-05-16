"""Pydantic schemas for the Guarantorship API."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# ---- Guarantee Requests ----

class GuaranteeRequestCreate(BaseModel):
    guarantor_id: str = Field(..., description="User ID of the intended guarantor")
    message: str | None = Field(None, max_length=1000)


class GuaranteeRequestResponse(BaseModel):
    request_id: str
    ward_id: str
    guarantor_id: str
    status: str
    message: str | None
    created_at: datetime
    responded_at: datetime | None

    model_config = {"from_attributes": True}


# ---- Zero Circles ----

class ZeroCircleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)
    deposit_stub: Decimal | None = Field(
        None,
        gt=0,
        description="Placeholder deposit amount (stub — no real funds)",
    )


class ZeroCircleMemberResponse(BaseModel):
    user_id: str
    joined_at: datetime

    model_config = {"from_attributes": True}


class ZeroCircleResponse(BaseModel):
    circle_id: str
    name: str
    initiated_by: str
    status: str
    deposit_stub: float | None
    created_at: datetime
    members: list[ZeroCircleMemberResponse]

    model_config = {"from_attributes": True}
