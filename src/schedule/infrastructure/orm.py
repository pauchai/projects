"""SQLAlchemy ORM mapping for the Schedule bounded context (Imperative Mapping).

Domain classes remain free of SQLAlchemy imports. Skills are stored in a
separate ``schedule_curator_skills`` table and reconstructed as a plain list.
``recommended_curator_ids`` on ConsultationRequest is stored as
comma-separated text (simple scalar field — no joins needed).
"""

from __future__ import annotations

import json

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    Time,
    event,
)
from sqlalchemy.orm import Session, registry, relationship

from schedule.domain.appointment import Appointment
from schedule.domain.consultation_offer import ConsultationOffer
from schedule.domain.consultation_request import ConsultationRequest
from schedule.domain.curator import AvailabilitySlot, Curator

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

mapper_registry = registry()
metadata = mapper_registry.metadata

# ---------------------------------------------------------------------------
# Table definitions
# ---------------------------------------------------------------------------

curators_table = Table(
    "schedule_curators",
    metadata,
    Column("curator_id", String(255), primary_key=True),
    Column("name", String(255), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

# Skills stored as child rows (free-text list)
_curator_skills_table = Table(
    "schedule_curator_skills",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "curator_id",
        String(255),
        ForeignKey("schedule_curators.curator_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("skill", String(255), nullable=False),
)

availability_slots_table = Table(
    "schedule_availability_slots",
    metadata,
    Column("slot_id", String(255), primary_key=True),
    Column(
        "curator_id",
        String(255),
        ForeignKey("schedule_curators.curator_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("weekday", Integer, nullable=False),
    Column("start_time", Time, nullable=False),
    Column("end_time", Time, nullable=False),
)

consultation_requests_table = Table(
    "schedule_consultation_requests",
    metadata,
    Column("request_id", String(255), primary_key=True),
    Column("student_name", String(255), nullable=False),
    Column("request_text", Text, nullable=False),
    Column("status", String(20), nullable=False),
    # Stored as JSON array string: '["id1","id2"]'
    Column("recommended_curator_ids", Text, nullable=False, default="[]"),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

consultation_offers_table = Table(
    "schedule_consultation_offers",
    metadata,
    Column("offer_id", String(255), primary_key=True),
    Column(
        "request_id",
        String(255),
        ForeignKey("schedule_consultation_requests.request_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("curator_id", String(255), nullable=False),
    Column("status", String(20), nullable=False),
    Column("offered_at", DateTime(timezone=True), nullable=False),
    Column("responded_at", DateTime(timezone=True), nullable=True),
)

appointments_table = Table(
    "schedule_appointments",
    metadata,
    Column("appointment_id", String(255), primary_key=True),
    Column(
        "request_id",
        String(255),
        ForeignKey("schedule_consultation_requests.request_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("curator_id", String(255), nullable=False),
    Column("scheduled_at", DateTime(timezone=True), nullable=False),
    Column("status", String(20), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

# ---------------------------------------------------------------------------
# Helper value object for skill rows
# ---------------------------------------------------------------------------


class _SkillRow:
    """Thin wrapper for a single skill row; mapped imperatively."""

    def __init__(self, curator_id: str, skill: str) -> None:
        self.curator_id = curator_id
        self.skill = skill


mapper_registry.map_imperatively(_SkillRow, _curator_skills_table)

# ---------------------------------------------------------------------------
# Imperative mappings
# ---------------------------------------------------------------------------

mapper_registry.map_imperatively(AvailabilitySlot, availability_slots_table)

mapper_registry.map_imperatively(
    Curator,
    curators_table,
    properties={
        "availability_slots": relationship(
            AvailabilitySlot,
            cascade="all, delete-orphan",
            passive_deletes=True,
        ),
        "_skill_rows": relationship(
            _SkillRow,
            cascade="all, delete-orphan",
            passive_deletes=True,
        ),
    },
)

mapper_registry.map_imperatively(ConsultationOffer, consultation_offers_table)
mapper_registry.map_imperatively(Appointment, appointments_table)
mapper_registry.map_imperatively(ConsultationRequest, consultation_requests_table)

# ---------------------------------------------------------------------------
# SQLAlchemy event hooks — serialize/deserialize recommended_curator_ids
# ---------------------------------------------------------------------------


@event.listens_for(Session, "loaded_as_persistent")
def _deserialize_request(session: Session, instance: object) -> None:
    """Deserialize recommended_curator_ids from JSON string after load."""
    if isinstance(instance, ConsultationRequest):
        raw = instance.__dict__.get("recommended_curator_ids", "[]")
        if isinstance(raw, str):
            object.__setattr__(instance, "recommended_curator_ids", json.loads(raw or "[]"))


@event.listens_for(Session, "before_flush")
def _serialize_request(session: Session, flush_context: object, instances: object) -> None:
    """Serialize recommended_curator_ids to JSON string before flush."""
    for obj in list(session.new) + list(session.dirty):
        if isinstance(obj, ConsultationRequest):
            ids = obj.__dict__.get("recommended_curator_ids", [])
            if isinstance(ids, list):
                object.__setattr__(obj, "recommended_curator_ids", json.dumps(ids))
