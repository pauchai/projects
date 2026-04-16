"""Earnings routes: REST endpoints for curator commission earnings."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends

from partnership.api.schemas import CommissionResponse, EarningsSummaryResponse
from partnership.application.get_curator_earnings import GetCuratorEarningsUseCase
from partnership.application.release_payout import ReleasePayoutUseCase
from partnership.domain.commission import Commission, CommissionStatus
from partnership.infrastructure.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork
from partnership.api.dependencies import get_current_user_id, get_partnership_uow

router = APIRouter(tags=["earnings"])


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def _commission_to_response(commission: Commission) -> CommissionResponse:
    total = commission.base_amount + commission.bonus_amount
    return CommissionResponse(
        commission_id=commission.commission_id,
        curator_id=commission.curator_id,
        cohort_id=commission.cohort_id,
        module_id=commission.module_id,
        base_amount=commission.base_amount,
        bonus_amount=commission.bonus_amount,
        total_amount=total,
        status=commission.status.value,
        earned_at=commission.earned_at,
        release_eligible_at=commission.release_eligible_at,
        released_at=commission.released_at,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/me/earnings", response_model=EarningsSummaryResponse)
def get_my_earnings_summary(
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_partnership_uow),
) -> EarningsSummaryResponse:
    """
    Get the current curator's earnings summary.

    Returns total pending and released amounts plus the full list of commissions.

    Authorization: any authenticated user (own data only).
    """
    use_case = GetCuratorEarningsUseCase(uow)
    commissions = use_case.execute(curator_id=caller_id)

    total_pending = sum(
        (c.base_amount + c.bonus_amount)
        for c in commissions
        if c.status == CommissionStatus.PENDING
    ) or Decimal("0.00")

    total_released = sum(
        (c.base_amount + c.bonus_amount)
        for c in commissions
        if c.status == CommissionStatus.RELEASED
    ) or Decimal("0.00")

    return EarningsSummaryResponse(
        curator_id=caller_id,
        total_pending=total_pending,
        total_released=total_released,
        commissions=[_commission_to_response(c) for c in commissions],
    )


@router.get("/me/earnings/history", response_model=list[CommissionResponse])
def get_my_earnings_history(
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_partnership_uow),
) -> list[CommissionResponse]:
    """
    Get the current curator's full commission history.

    Returns all commissions (PENDING and RELEASED) in no particular order.

    Authorization: any authenticated user (own data only).
    """
    use_case = GetCuratorEarningsUseCase(uow)
    commissions = use_case.execute(curator_id=caller_id)
    return [_commission_to_response(c) for c in commissions]


@router.post(
    "/me/earnings/{commission_id}/release",
    response_model=CommissionResponse,
)
def release_earning(
    commission_id: str,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_partnership_uow),
) -> CommissionResponse:
    """
    Release a pending commission payout.

    Validates hold period has elapsed and total meets minimum threshold.
    Raises 404 if commission not found, 403 if not the owner, 422 if
    release conditions are not met.

    Authorization: commission owner only.
    """
    use_case = ReleasePayoutUseCase(uow)
    commission = use_case.execute(
        commission_id=commission_id,
        curator_id=caller_id,
    )
    return _commission_to_response(commission)
