"""FastAPI dependencies for the Schedule bounded context."""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy.orm import Session, sessionmaker

from auth.infrastructure.database import get_engine, get_session_factory
from schedule.application.add_availability_slot import AddAvailabilitySlotUseCase
from schedule.application.assign_appointment import AssignAppointmentUseCase
from schedule.application.create_curator import CreateCuratorUseCase
from schedule.application.respond_to_offer import RespondToOfferUseCase
from schedule.application.start_negotiation import StartNegotiationUseCase
from schedule.application.submit_consultation_request import SubmitConsultationRequestUseCase
from schedule.infrastructure.ai_recommender_stub import KeywordAiRecommenderStub
from schedule.infrastructure.sqlalchemy_unit_of_work import SqlAlchemyScheduleUnitOfWork

# Ensure ORM mappings are registered
import schedule.infrastructure.orm  # noqa: F401


@lru_cache
def _get_session_factory() -> sessionmaker[Session]:
    engine = get_engine()
    return get_session_factory(engine)


def get_schedule_uow() -> SqlAlchemyScheduleUnitOfWork:
    return SqlAlchemyScheduleUnitOfWork(_get_session_factory())


def get_create_curator() -> CreateCuratorUseCase:
    return CreateCuratorUseCase(get_schedule_uow())


def get_add_slot() -> AddAvailabilitySlotUseCase:
    return AddAvailabilitySlotUseCase(get_schedule_uow())


def get_submit_request() -> SubmitConsultationRequestUseCase:
    return SubmitConsultationRequestUseCase(
        get_schedule_uow(), KeywordAiRecommenderStub()
    )


def get_start_negotiation() -> StartNegotiationUseCase:
    return StartNegotiationUseCase(get_schedule_uow())


def get_respond_to_offer() -> RespondToOfferUseCase:
    return RespondToOfferUseCase(get_schedule_uow())


def get_assign_appointment() -> AssignAppointmentUseCase:
    return AssignAppointmentUseCase(get_schedule_uow())
