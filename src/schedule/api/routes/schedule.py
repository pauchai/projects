"""Schedule API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from schedule.api.dependencies import (
    get_add_slot,
    get_assign_appointment,
    get_create_curator,
    get_respond_to_offer,
    get_schedule_uow,
    get_start_negotiation,
    get_submit_request,
)
from schedule.api.schemas import (
    AddAvailabilitySlotRequest,
    AddAvailabilitySlotResponse,
    AppointmentResponse,
    AssignAppointmentRequest,
    AvailabilitySlotResponse,
    ConsultationRequestResponse,
    CreateCuratorRequest,
    CuratorResponse,
    OfferResponse,
    RespondToOfferRequest,
    RespondToOfferResponse,
    StartNegotiationResponse,
    SubmitConsultationRequestBody,
)
from schedule.application.add_availability_slot import AddAvailabilitySlotUseCase
from schedule.application.assign_appointment import AssignAppointmentUseCase
from schedule.application.create_curator import CreateCuratorUseCase
from schedule.application.respond_to_offer import RespondToOfferUseCase
from schedule.application.start_negotiation import StartNegotiationUseCase
from schedule.application.submit_consultation_request import SubmitConsultationRequestUseCase
from schedule.infrastructure.sqlalchemy_unit_of_work import SqlAlchemyScheduleUnitOfWork

router = APIRouter(prefix="/schedule", tags=["schedule"])


# ---------------------------------------------------------------------------
# Curators
# ---------------------------------------------------------------------------


@router.post("/curators", status_code=201, response_model=CuratorResponse)
def create_curator(
    body: CreateCuratorRequest,
    use_case: CreateCuratorUseCase = Depends(get_create_curator),
    uow: SqlAlchemyScheduleUnitOfWork = Depends(get_schedule_uow),
) -> CuratorResponse:
    curator_id = use_case.execute(name=body.name, skills=body.skills)
    with uow as u:
        curator = u.curators.find_by_id(curator_id)
    assert curator is not None
    return CuratorResponse(
        curator_id=curator.curator_id,
        name=curator.name,
        skills=curator.skills,
        availability_slots=[
            AvailabilitySlotResponse(
                slot_id=s.slot_id,
                weekday=s.weekday,
                start_time=s.start_time,
                end_time=s.end_time,
            )
            for s in curator.availability_slots
        ],
    )


@router.get("/curators", response_model=list[CuratorResponse])
def list_curators(
    uow: SqlAlchemyScheduleUnitOfWork = Depends(get_schedule_uow),
) -> list[CuratorResponse]:
    with uow as u:
        curators = u.curators.find_all()
    return [
        CuratorResponse(
            curator_id=c.curator_id,
            name=c.name,
            skills=c.skills,
            availability_slots=[
                AvailabilitySlotResponse(
                    slot_id=s.slot_id,
                    weekday=s.weekday,
                    start_time=s.start_time,
                    end_time=s.end_time,
                )
                for s in c.availability_slots
            ],
        )
        for c in curators
    ]


@router.post(
    "/curators/{curator_id}/slots",
    status_code=201,
    response_model=AddAvailabilitySlotResponse,
)
def add_availability_slot(
    curator_id: str,
    body: AddAvailabilitySlotRequest,
    use_case: AddAvailabilitySlotUseCase = Depends(get_add_slot),
) -> AddAvailabilitySlotResponse:
    slot_id = use_case.execute(
        curator_id=curator_id,
        weekday=body.weekday,
        start_time=body.start_time,
        end_time=body.end_time,
    )
    return AddAvailabilitySlotResponse(slot_id=slot_id)


# ---------------------------------------------------------------------------
# Consultation requests
# ---------------------------------------------------------------------------


@router.post("/requests", status_code=201, response_model=ConsultationRequestResponse)
def submit_consultation_request(
    body: SubmitConsultationRequestBody,
    use_case: SubmitConsultationRequestUseCase = Depends(get_submit_request),
    uow: SqlAlchemyScheduleUnitOfWork = Depends(get_schedule_uow),
) -> ConsultationRequestResponse:
    request_id = use_case.execute(
        student_name=body.student_name,
        request_text=body.request_text,
    )
    with uow as u:
        req = u.requests.find_by_id(request_id)
    assert req is not None
    return ConsultationRequestResponse(
        request_id=req.request_id,
        student_name=req.student_name,
        request_text=req.request_text,
        status=req.status,
        recommended_curator_ids=req.recommended_curator_ids,
    )


@router.get("/requests", response_model=list[ConsultationRequestResponse])
def list_requests(
    uow: SqlAlchemyScheduleUnitOfWork = Depends(get_schedule_uow),
) -> list[ConsultationRequestResponse]:
    with uow as u:
        requests = u.requests.find_all()
    return [
        ConsultationRequestResponse(
            request_id=r.request_id,
            student_name=r.student_name,
            request_text=r.request_text,
            status=r.status,
            recommended_curator_ids=r.recommended_curator_ids,
        )
        for r in requests
    ]


# ---------------------------------------------------------------------------
# Negotiation
# ---------------------------------------------------------------------------


@router.get("/offers", response_model=list[OfferResponse])
def list_offers(
    curator_id: str,
    uow: SqlAlchemyScheduleUnitOfWork = Depends(get_schedule_uow),
) -> list[OfferResponse]:
    with uow as u:
        offers = u.offers.find_by_curator_id(curator_id)
        result = []
        for offer in offers:
            req = u.requests.find_by_id(offer.request_id)
            result.append(
                OfferResponse(
                    offer_id=offer.offer_id,
                    request_id=offer.request_id,
                    curator_id=offer.curator_id,
                    status=offer.status,
                    student_name=req.student_name if req else "",
                    request_text=req.request_text if req else "",
                )
            )
    return result


@router.post(
    "/requests/{request_id}/negotiate",
    status_code=201,
    response_model=StartNegotiationResponse,
)
def start_negotiation(
    request_id: str,
    use_case: StartNegotiationUseCase = Depends(get_start_negotiation),
) -> StartNegotiationResponse:
    offer_ids = use_case.execute(request_id)
    return StartNegotiationResponse(offer_ids=offer_ids)


@router.post("/offers/{offer_id}/respond", response_model=RespondToOfferResponse)
def respond_to_offer(    offer_id: str,
    body: RespondToOfferRequest,
    use_case: RespondToOfferUseCase = Depends(get_respond_to_offer),
    uow: SqlAlchemyScheduleUnitOfWork = Depends(get_schedule_uow),
) -> RespondToOfferResponse:
    if body.action == "accept":
        use_case.accept(offer_id)
    else:
        use_case.decline(offer_id)

    with uow as u:
        offer = u.offers.find_by_id(offer_id)
    assert offer is not None
    return RespondToOfferResponse(offer_id=offer.offer_id, status=offer.status)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Appointment
# ---------------------------------------------------------------------------


@router.post(
    "/requests/{request_id}/assign",
    status_code=201,
    response_model=AppointmentResponse,
)
def assign_appointment(
    request_id: str,
    body: AssignAppointmentRequest,
    use_case: AssignAppointmentUseCase = Depends(get_assign_appointment),
    uow: SqlAlchemyScheduleUnitOfWork = Depends(get_schedule_uow),
) -> AppointmentResponse:
    appointment_id = use_case.execute(request_id, body.scheduled_at)
    with uow as u:
        appt = u.appointments.find_by_id(appointment_id)
    assert appt is not None
    return AppointmentResponse(
        appointment_id=appt.appointment_id,
        request_id=appt.request_id,
        curator_id=appt.curator_id,
        scheduled_at=appt.scheduled_at,
        status=appt.status,
    )
