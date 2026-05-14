"""Fund routes: GET/POST /projects/{project_id}/fund."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, status

from project_collaboration.api.dependencies import get_current_user_id, get_uow
from project_collaboration.api.schemas import (
    DepositRequest,
    DistributeRequest,
    FundDistributionResponse,
    FundResponse,
    FundTransactionResponse,
)
from project_collaboration.application.deposit_to_fund import (
    DepositToFundCommand,
    DepositToFundUseCase,
)
from project_collaboration.application.distribute_fund import (
    DistributeFundCommand,
    DistributeFundUseCase,
)
from project_collaboration.domain.fund import FundDistribution, FundTransaction, ProjectFund

router = APIRouter(prefix="/projects", tags=["fund"])


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

def _serialize_tx(tx: FundTransaction) -> FundTransactionResponse:
    return FundTransactionResponse(
        transaction_id=tx.transaction_id,
        fund_id=tx.fund_id,
        amount=float(tx.amount),
        source=tx.source,
        ref_id=tx.ref_id,
        created_at=tx.created_at,
    )


def _serialize_dist(dist: FundDistribution) -> FundDistributionResponse:
    return FundDistributionResponse(
        distribution_id=dist.distribution_id,
        fund_id=dist.fund_id,
        amount=float(dist.amount),
        initiated_by=dist.initiated_by,
        note=dist.note,
        status=dist.status,
        created_at=dist.created_at,
    )


def _serialize_fund(
    fund: ProjectFund | None,
    project_id: str,
    transactions: list[FundTransaction],
    distributions: list[FundDistribution],
) -> FundResponse:
    if fund is None:
        return FundResponse(
            fund_id=None,
            project_id=project_id,
            balance=0.0,
        )
    return FundResponse(
        fund_id=fund.fund_id,
        project_id=fund.project_id,
        balance=float(fund.balance),
        transactions=[_serialize_tx(tx) for tx in transactions],
        distributions=[_serialize_dist(d) for d in distributions],
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get(
    "/{project_id}/fund",
    response_model=FundResponse,
    summary="Get project fund balance and history",
)
def get_fund(
    project_id: str,
    uow: object = Depends(get_uow),
    _: str = Depends(get_current_user_id),
) -> FundResponse:
    with uow as u:
        fund = u.fund.find_by_project(project_id)
        if fund is None:
            return _serialize_fund(None, project_id, [], [])
        transactions = u.fund.list_transactions(fund.fund_id)
        distributions = u.fund.list_distributions(fund.fund_id)
    return _serialize_fund(fund, project_id, transactions, distributions)


@router.post(
    "/{project_id}/fund/deposit",
    response_model=FundResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Deposit net amount into the project fund",
)
def deposit(
    project_id: str,
    body: DepositRequest,
    uow: object = Depends(get_uow),
    current_user_id: str = Depends(get_current_user_id),
) -> FundResponse:
    cmd = DepositToFundCommand(
        project_id=project_id,
        amount=Decimal(str(body.amount)),
        source=body.source,
        ref_id=body.ref_id,
    )
    fund = DepositToFundUseCase(uow).execute(cmd)

    with uow as u:
        transactions = u.fund.list_transactions(fund.fund_id)
        distributions = u.fund.list_distributions(fund.fund_id)

    return _serialize_fund(fund, project_id, transactions, distributions)


@router.post(
    "/{project_id}/fund/distribute",
    response_model=FundDistributionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a pending distribution request from the project fund",
)
def distribute(
    project_id: str,
    body: DistributeRequest,
    uow: object = Depends(get_uow),
    current_user_id: str = Depends(get_current_user_id),
) -> FundDistributionResponse:
    cmd = DistributeFundCommand(
        project_id=project_id,
        amount=Decimal(str(body.amount)),
        initiated_by=current_user_id,
        note=body.note,
    )
    dist = DistributeFundUseCase(uow).execute(cmd)
    return _serialize_dist(dist)
