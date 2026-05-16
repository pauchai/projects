"""Guarantorship API routes — requests and zero circles."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from guarantorship.api.dependencies import get_guarantorship_uow
from guarantorship.api.schemas import (
    GuaranteeRequestCreate,
    GuaranteeRequestResponse,
    ZeroCircleCreate,
    ZeroCircleResponse,
)
from guarantorship.application.accept_guarantee_request import (
    AcceptGuaranteeRequestCommand,
    AcceptGuaranteeRequestUseCase,
)
from guarantorship.application.create_zero_circle import (
    CreateZeroCircleCommand,
    CreateZeroCircleUseCase,
)
from guarantorship.application.join_zero_circle import (
    JoinZeroCircleCommand,
    JoinZeroCircleUseCase,
)
from guarantorship.application.reject_guarantee_request import (
    RejectGuaranteeRequestCommand,
    RejectGuaranteeRequestUseCase,
)
from guarantorship.application.request_guarantor import (
    RequestGuarantorCommand,
    RequestGuarantorUseCase,
)
from guarantorship.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyGuarantorshipUnitOfWork,
)
from project_collaboration.api.dependencies import get_current_user_id

router = APIRouter(prefix="/guarantorships", tags=["guarantorships"])
circles_router = APIRouter(prefix="/zero-circles", tags=["zero-circles"])


# ─── Guarantee Requests ────────────────────────────────────────────────────────

@router.post(
    "/request",
    response_model=GuaranteeRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a guarantorship request",
)
def request_guarantor(
    body: GuaranteeRequestCreate,
    current_user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyGuarantorshipUnitOfWork = Depends(get_guarantorship_uow),
) -> GuaranteeRequestResponse:
    use_case = RequestGuarantorUseCase(uow)
    request = use_case.execute(
        RequestGuarantorCommand(
            ward_id=current_user_id,
            guarantor_id=body.guarantor_id,
            message=body.message,
        )
    )
    return GuaranteeRequestResponse.model_validate(request)


@router.post(
    "/{request_id}/accept",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Accept a guarantorship request",
)
def accept_request(
    request_id: str,
    current_user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyGuarantorshipUnitOfWork = Depends(get_guarantorship_uow),
) -> None:
    AcceptGuaranteeRequestUseCase(uow).execute(
        AcceptGuaranteeRequestCommand(
            request_id=request_id,
            guarantor_id=current_user_id,
        )
    )


@router.post(
    "/{request_id}/reject",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reject a guarantorship request",
)
def reject_request(
    request_id: str,
    current_user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyGuarantorshipUnitOfWork = Depends(get_guarantorship_uow),
) -> None:
    RejectGuaranteeRequestUseCase(uow).execute(
        RejectGuaranteeRequestCommand(
            request_id=request_id,
            guarantor_id=current_user_id,
        )
    )


@router.get(
    "/incoming",
    response_model=list[GuaranteeRequestResponse],
    summary="List incoming guarantorship requests (I am the intended guarantor)",
)
def list_incoming(
    current_user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyGuarantorshipUnitOfWork = Depends(get_guarantorship_uow),
) -> list[GuaranteeRequestResponse]:
    with uow as u:
        requests = u.requests.find_incoming(current_user_id)
    return [GuaranteeRequestResponse.model_validate(r) for r in requests]


@router.get(
    "/outgoing",
    response_model=list[GuaranteeRequestResponse],
    summary="List my outgoing guarantorship requests",
)
def list_outgoing(
    current_user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyGuarantorshipUnitOfWork = Depends(get_guarantorship_uow),
) -> list[GuaranteeRequestResponse]:
    with uow as u:
        requests = u.requests.find_outgoing(current_user_id)
    return [GuaranteeRequestResponse.model_validate(r) for r in requests]


# ─── Zero Circles ──────────────────────────────────────────────────────────────

@circles_router.get(
    "",
    response_model=list[ZeroCircleResponse],
    summary="List all open zero-guarantee circles",
)
def list_circles(
    current_user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyGuarantorshipUnitOfWork = Depends(get_guarantorship_uow),
) -> list[ZeroCircleResponse]:
    with uow as u:
        circles = u.circles.find_open()
    return [_circle_to_response(c) for c in circles]


@circles_router.post(
    "",
    response_model=ZeroCircleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new zero-guarantee DAO circle",
)
def create_circle(
    body: ZeroCircleCreate,
    current_user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyGuarantorshipUnitOfWork = Depends(get_guarantorship_uow),
) -> ZeroCircleResponse:
    circle = CreateZeroCircleUseCase(uow).execute(
        CreateZeroCircleCommand(
            initiated_by=current_user_id,
            name=body.name,
            deposit_stub=body.deposit_stub,
        )
    )
    return _circle_to_response(circle)


@circles_router.post(
    "/{circle_id}/join",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Join a zero-guarantee circle",
)
def join_circle(
    circle_id: str,
    current_user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyGuarantorshipUnitOfWork = Depends(get_guarantorship_uow),
) -> None:
    JoinZeroCircleUseCase(uow).execute(
        JoinZeroCircleCommand(circle_id=circle_id, user_id=current_user_id)
    )


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _circle_to_response(circle) -> ZeroCircleResponse:
    from guarantorship.api.schemas import ZeroCircleMemberResponse
    return ZeroCircleResponse(
        circle_id=circle.circle_id,
        name=circle.name,
        initiated_by=circle.initiated_by,
        status=circle.status if isinstance(circle.status, str) else circle.status.value,
        deposit_stub=float(circle.deposit_stub) if circle.deposit_stub is not None else None,
        created_at=circle.created_at,
        members=[
            ZeroCircleMemberResponse(user_id=m.user_id, joined_at=m.joined_at)
            for m in circle.members
        ],
    )
