"""Deals API router (stub)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from auth.api.dependencies import get_current_user_id
from guarantorship.api.dependencies import get_guarantorship_uow
from guarantorship.api.schemas import DealCreate, DealResponse
from guarantorship.application.create_deal import CreateDealCommand, CreateDealUseCase
from guarantorship.infrastructure.sqlalchemy_unit_of_work import SqlAlchemyGuarantorshipUnitOfWork

router = APIRouter(prefix="/deals", tags=["deals"])


@router.post("", response_model=DealResponse, status_code=status.HTTP_201_CREATED)
def create_deal(
    body: DealCreate,
    user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyGuarantorshipUnitOfWork = Depends(get_guarantorship_uow),
) -> DealResponse:
    use_case = CreateDealUseCase(uow)
    try:
        deal = use_case.execute(
            CreateDealCommand(
                initiator_id=user_id,
                counterparty_id=body.counterparty_id,
                amount=body.amount,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return DealResponse.model_validate(deal)


@router.get("/my", response_model=list[DealResponse])
def my_deals(
    user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyGuarantorshipUnitOfWork = Depends(get_guarantorship_uow),
) -> list[DealResponse]:
    with uow as u:
        deals = u.deals.find_by_participant(user_id)
    return [DealResponse.model_validate(d) for d in deals]
