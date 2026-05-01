"""SQLAlchemy repositories for the Schedule bounded context."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from schedule.domain.appointment import Appointment
from schedule.domain.consultation_offer import ConsultationOffer
from schedule.domain.consultation_request import ConsultationRequest
from schedule.domain.curator import Curator
from schedule.infrastructure.orm import consultation_offers_table


class SqlAlchemyCuratorRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_id(self, curator_id: str) -> Curator | None:
        curator = self._session.get(
            Curator,
            curator_id,
            options=[
                selectinload(Curator.availability_slots),  # type: ignore[attr-defined]
                selectinload(Curator._skill_rows),  # type: ignore[attr-defined]
            ],
        )
        if curator is not None:
            self._sync_skills(curator)
        return curator

    def find_all(self) -> list[Curator]:
        stmt = select(Curator).options(
            selectinload(Curator.availability_slots),  # type: ignore[attr-defined]
            selectinload(Curator._skill_rows),  # type: ignore[attr-defined]
        )
        curators = list(self._session.scalars(stmt).all())
        for c in curators:
            self._sync_skills(c)
        return curators

    def save(self, curator: Curator) -> None:
        self._sync_skill_rows(curator)
        self._session.merge(curator)

    @staticmethod
    def _sync_skills(curator: Curator) -> None:
        """Populate curator.skills list from _skill_rows after load."""
        rows = curator.__dict__.get("_skill_rows", [])
        curator.skills = [r.skill for r in rows]

    @staticmethod
    def _sync_skill_rows(curator: Curator) -> None:
        """Ensure _skill_rows reflect curator.skills before save."""
        from schedule.infrastructure.orm import _SkillRow

        existing_skills = {r.skill for r in curator.__dict__.get("_skill_rows", [])}
        current_skills = set(curator.skills)

        # Add new
        for skill in current_skills - existing_skills:
            curator._skill_rows.append(  # type: ignore[attr-defined]
                _SkillRow(curator_id=curator.curator_id, skill=skill)
            )
        # Remove deleted
        to_remove = [
            r
            for r in curator.__dict__.get("_skill_rows", [])
            if r.skill not in current_skills
        ]
        for r in to_remove:
            curator._skill_rows.remove(r)  # type: ignore[attr-defined]


class SqlAlchemyConsultationRequestRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_id(self, request_id: str) -> ConsultationRequest | None:
        return self._session.get(ConsultationRequest, request_id)

    def find_all(self) -> list[ConsultationRequest]:
        stmt = select(ConsultationRequest)
        return list(self._session.scalars(stmt).all())

    def save(self, request: ConsultationRequest) -> None:
        self._session.merge(request)


class SqlAlchemyConsultationOfferRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_id(self, offer_id: str) -> ConsultationOffer | None:
        return self._session.get(ConsultationOffer, offer_id)

    def find_by_request_id(self, request_id: str) -> list[ConsultationOffer]:
        stmt = select(ConsultationOffer).where(
            consultation_offers_table.c.request_id == request_id
        )
        return list(self._session.scalars(stmt).all())

    def save(self, offer: ConsultationOffer) -> None:
        self._session.merge(offer)

    def save_many(self, offers: list[ConsultationOffer]) -> None:
        for offer in offers:
            self.save(offer)


class SqlAlchemyAppointmentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_id(self, appointment_id: str) -> Appointment | None:
        return self._session.get(Appointment, appointment_id)

    def find_by_request_id(self, request_id: str) -> Appointment | None:
        from schedule.infrastructure.orm import appointments_table

        stmt = select(Appointment).where(
            appointments_table.c.request_id == request_id
        )
        return self._session.scalars(stmt).first()

    def save(self, appointment: Appointment) -> None:
        self._session.merge(appointment)
