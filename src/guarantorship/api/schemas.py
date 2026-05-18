"""Pydantic schemas for the Guarantorship API."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# ── Guarantee Requests ────────────────────────────────────────────────────────

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
    converted_to_guarantorship_id: str | None = None

    model_config = {"from_attributes": True}


# ── Guarantorships ────────────────────────────────────────────────────────────

class GuarantorshipResponse(BaseModel):
    guarantorship_id: str
    guarantor_id: str
    ward_id: str
    request_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── User Deposits ─────────────────────────────────────────────────────────────

class DepositCreate(BaseModel):
    guarantor_id: str
    amount: Decimal = Field(..., gt=0)
    blockchain_ref: str | None = Field(None, max_length=512)


class DepositResponse(BaseModel):
    deposit_id: str
    ward_id: str
    guarantor_id: str
    amount: Decimal
    blockchain_ref: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Platform Settings ─────────────────────────────────────────────────────────

class PlatformSettingsResponse(BaseModel):
    required_guarantors_count: int
    guarantor_ward_limit: int
    escalation_levels: int

    model_config = {"from_attributes": True}


class PlatformSettingsUpdate(BaseModel):
    required_guarantors_count: int | None = Field(None, ge=1)
    guarantor_ward_limit: int | None = Field(None, ge=1)
    escalation_levels: int | None = Field(None, ge=0)


# ── Deals ─────────────────────────────────────────────────────────────────────

class DealCreate(BaseModel):
    counterparty_id: str
    amount: Decimal = Field(..., gt=0)


class DealResponse(BaseModel):
    deal_id: str
    initiator_id: str
    counterparty_id: str
    amount: Decimal
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Complaints ────────────────────────────────────────────────────────────────

class ComplaintCreate(BaseModel):
    deal_id: str
    against_id: str
    description: str = Field(..., min_length=10, max_length=5000)


class VoteCreate(BaseModel):
    vote: str = Field(..., pattern="^(compensate_initiator|compensate_counterparty|dismiss)$")


class ComplaintResponse(BaseModel):
    complaint_id: str
    deal_id: str
    filed_by_id: str
    against_id: str
    description: str
    status: str
    verdict: str | None
    voting_deadline: datetime | None
    escalation_level: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Zero Circles ──────────────────────────────────────────────────────────────

class ZeroCircleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)
    deposit_stub: Decimal | None = Field(
        None, gt=0, description="Placeholder deposit amount (stub — no real funds)"
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
