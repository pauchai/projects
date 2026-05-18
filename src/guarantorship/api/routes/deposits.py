"""Deposits API router."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from auth.api.dependencies import get_current_user_id
from guarantorship.api.dependencies import get_guarantorship_uow
from guarantorship.api.schemas import DepositCreate, DepositResponse
from guarantorship.application.create_deposit import CreateDepositCommand, CreateDepositUseCase
from guarantorship.infrastructure.sqlalchemy_unit_of_work import SqlAlchemyGuarantorshipUnitOfWork

router = APIRouter(prefix="/deposits", tags=["deposits"])


@router.post("", response_model=DepositResponse, status_code=status.HTTP_201_CREATED)
def create_deposit(
    body: DepositCreate,
    user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyGuarantorshipUnitOfWork = Depends(get_guarantorship_uow),
) -> DepositResponse:
    use_case = CreateDepositUseCase(uow)
    try:
        deposit = use_case.execute(
            CreateDepositCommand(
                ward_id=user_id,
                guarantor_id=body.guarantor_id,
                amount=body.amount,
                blockchain_ref=body.blockchain_ref,
            )
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return DepositResponse.model_validate(deposit)


@router.get("/my", response_model=list[DepositResponse])
def my_deposits(
    user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyGuarantorshipUnitOfWork = Depends(get_guarantorship_uow),
) -> list[DepositResponse]:
    with uow as u:
        deposits = u.deposits.find_by_ward(user_id)
    return [DepositResponse.model_validate(d) for d in deposits]


@router.get("/held", response_model=list[DepositResponse])
def held_deposits(
    user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyGuarantorshipUnitOfWork = Depends(get_guarantorship_uow),
) -> list[DepositResponse]:
    """Deposits I hold as a guarantor for my wards."""
    with uow as u:
        deposits = u.deposits.find_by_guarantor(user_id)
    return [DepositResponse.model_validate(d) for d in deposits]
