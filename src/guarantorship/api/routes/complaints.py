"""Complaints API router."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from auth.api.dependencies import get_current_user_id
from guarantorship.api.dependencies import get_guarantorship_uow
from guarantorship.api.schemas import ComplaintCreate, ComplaintResponse, VoteCreate
from guarantorship.application.cast_vote import CastVoteCommand, CastVoteUseCase
from guarantorship.application.escalate_complaint import (
    EscalateComplaintCommand,
    EscalateComplaintUseCase,
)
from guarantorship.application.file_complaint import FileComplaintCommand, FileComplaintUseCase
from guarantorship.domain.complaint import Verdict
from guarantorship.infrastructure.sqlalchemy_unit_of_work import SqlAlchemyGuarantorshipUnitOfWork

router = APIRouter(prefix="/complaints", tags=["complaints"])


@router.post("", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
def file_complaint(
    body: ComplaintCreate,
    user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyGuarantorshipUnitOfWork = Depends(get_guarantorship_uow),
) -> ComplaintResponse:
    use_case = FileComplaintUseCase(uow)
    try:
        complaint = use_case.execute(
            FileComplaintCommand(
                deal_id=body.deal_id,
                filed_by_id=user_id,
                against_id=body.against_id,
                description=body.description,
            )
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except (PermissionError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return ComplaintResponse.model_validate(complaint)


@router.get("/{complaint_id}", response_model=ComplaintResponse)
def get_complaint(
    complaint_id: str,
    _: str = Depends(get_current_user_id),
    uow: SqlAlchemyGuarantorshipUnitOfWork = Depends(get_guarantorship_uow),
) -> ComplaintResponse:
    with uow as u:
        complaint = u.complaints.find_by_id(complaint_id)
    if complaint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    return ComplaintResponse.model_validate(complaint)


@router.post("/{complaint_id}/vote", response_model=ComplaintResponse)
def cast_vote(
    complaint_id: str,
    body: VoteCreate,
    user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyGuarantorshipUnitOfWork = Depends(get_guarantorship_uow),
) -> ComplaintResponse:
    use_case = CastVoteUseCase(uow)
    try:
        complaint = use_case.execute(
            CastVoteCommand(
                complaint_id=complaint_id,
                voter_id=user_id,
                vote=Verdict(body.vote),
            )
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except (PermissionError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return ComplaintResponse.model_validate(complaint)


@router.post("/{complaint_id}/escalate", response_model=ComplaintResponse)
def escalate_complaint(
    complaint_id: str,
    _: str = Depends(get_current_user_id),
    uow: SqlAlchemyGuarantorshipUnitOfWork = Depends(get_guarantorship_uow),
) -> ComplaintResponse:
    use_case = EscalateComplaintUseCase(uow)
    try:
        complaint = use_case.execute(EscalateComplaintCommand(complaint_id=complaint_id))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return ComplaintResponse.model_validate(complaint)


@router.get("", response_model=list[ComplaintResponse])
def my_complaints(
    user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyGuarantorshipUnitOfWork = Depends(get_guarantorship_uow),
) -> list[ComplaintResponse]:
    """Complaints where I need to vote (active guarantor)."""
    with uow as u:
        complaints = u.complaints.find_open_for_voter(user_id)
    return [ComplaintResponse.model_validate(c) for c in complaints]
