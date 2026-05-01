"""Pydantic schemas for the Schedule API."""

from __future__ import annotations

from datetime import datetime, time
from typing import Literal

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Curator
# ---------------------------------------------------------------------------


class CreateCuratorRequest(BaseModel):
    name: str
    skills: list[str] = []


class AvailabilitySlotResponse(BaseModel):
    slot_id: str
    weekday: int
    start_time: time
    end_time: time


class CuratorResponse(BaseModel):
    curator_id: str
    name: str
    skills: list[str]
    availability_slots: list[AvailabilitySlotResponse]


class AddAvailabilitySlotRequest(BaseModel):
    weekday: int
    start_time: time
    end_time: time


class AddAvailabilitySlotResponse(BaseModel):
    slot_id: str


# ---------------------------------------------------------------------------
# Consultation Request
# ---------------------------------------------------------------------------


class SubmitConsultationRequestBody(BaseModel):
    student_name: str
    request_text: str


class ConsultationRequestResponse(BaseModel):
    request_id: str
    student_name: str
    request_text: str
    status: Literal["pending", "negotiating", "confirmed", "cancelled"]
    recommended_curator_ids: list[str]


# ---------------------------------------------------------------------------
# Negotiation
# ---------------------------------------------------------------------------


class StartNegotiationResponse(BaseModel):
    offer_ids: list[str]


class RespondToOfferRequest(BaseModel):
    action: Literal["accept", "decline"]


class RespondToOfferResponse(BaseModel):
    offer_id: str
    status: Literal["accepted", "declined"]


# ---------------------------------------------------------------------------
# Appointment
# ---------------------------------------------------------------------------


class AssignAppointmentRequest(BaseModel):
    scheduled_at: datetime


class AppointmentResponse(BaseModel):
    appointment_id: str
    request_id: str
    curator_id: str
    scheduled_at: datetime
    status: Literal["scheduled", "completed", "cancelled"]
