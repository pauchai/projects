from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, Field

from community.api.dependencies import (
    AuthenticationError,
    get_current_user_id,
    get_uow,
)
from community.application.add_member import (
    AddMemberUseCase,
    ChangeMemberRoleUseCase,
    RemoveMemberUseCase,
)
from community.application.change_community_status import (
    ChangeCommunityStatusUseCase,
)
from community.application.create_community import CreateCommunityUseCase
from community.application.feature_request_operations import (
    ListFeatureRequestsUseCase,
    SubmitFeatureRequestUseCase,
    UpdateFeatureStatusUseCase,
)
from community.application.fund_operations import (
    DepositToFundCommand,
    DepositToFundUseCase,
    DistributeFromFundCommand,
    DistributeFromFundUseCase,
    GetFundUseCase,
)
from community.application.list_communities import GetCommunityUseCase, ListCommunitiesUseCase
from community.application.update_community import UpdateCommunityUseCase
from community.domain.community_role import CommunityRole
from community.domain.community_status import CommunityStatus
from community.domain.feature_status import FeatureStatus
from community.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyCommunityUnitOfWork,
)

router = APIRouter(prefix="/communities", tags=["communities"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class CommunityCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: str = Field(default="", max_length=5000)
    avatar_url: str | None = None


class CommunityUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = Field(None, max_length=5000)
    avatar_url: str | None = None


class CommunityStatusChangeRequest(BaseModel):
    status: str  # "active", "suspended", "archived"


class AddMemberRequest(BaseModel):
    user_id: str
    role: str = "member"


class ChangeMemberRoleRequest(BaseModel):
    role: str


class DepositRequest(BaseModel):
    amount: str  # Decimal as string to avoid float issues
    source: str = "manual"
    ref_id: str | None = None


class DistributeRequest(BaseModel):
    amount: str
    note: str = ""


class FeatureRequestCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=500)
    description: str = Field(..., max_length=10000)
    category: str | None = None
    priority: str | None = None


class FeatureRequestStatusUpdate(BaseModel):
    status: str
    admin_notes: str | None = None


# ---------------------------------------------------------------------------
# Error mapping
# ---------------------------------------------------------------------------

_EXCEPTION_MAP: dict[type, int] = {
    LookupError: 404,
    ValueError: 422,
    PermissionError: 403,
    AuthenticationError: 401,
}


def _map_error(exc: Exception) -> HTTPException:
    status = _EXCEPTION_MAP.get(type(exc), 500)
    return HTTPException(status_code=status, detail=str(exc))


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("", status_code=201)
def create_community(
    body: CommunityCreateRequest,
    user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyCommunityUnitOfWork = Depends(get_uow),
) -> dict:
    try:
        use_case = CreateCommunityUseCase(uow)
        community = use_case.execute(
            community_id=str(uuid.uuid4()),
            name=body.name,
            description=body.description,
            owner_id=user_id,
            avatar_url=body.avatar_url,
        )
    except Exception as exc:
        raise _map_error(exc) from exc

    return {
        "community_id": community.community_id,
        "name": community.name,
        "description": community.description,
        "owner_id": community.owner_id,
        "status": community.status.value,
        "created_at": community.created_at.isoformat(),
    }


@router.get("")
def list_communities(
    user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyCommunityUnitOfWork = Depends(get_uow),
) -> list[dict]:
    try:
        use_case = ListCommunitiesUseCase(uow)
        communities = use_case.execute(caller_id=user_id)
    except Exception as exc:
        raise _map_error(exc) from exc

    return [
        {
            "community_id": c.community_id,
            "name": c.name,
            "description": c.description,
            "owner_id": c.owner_id,
            "status": c.status.value,
            "member_count": len([m for m in c.memberships if m.is_active]),
            "created_at": c.created_at.isoformat(),
        }
        for c in communities
    ]


@router.get("/{community_id}")
def get_community(
    community_id: str,
    user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyCommunityUnitOfWork = Depends(get_uow),
) -> dict:
    try:
        use_case = GetCommunityUseCase(uow)
        community = use_case.execute(community_id=community_id, caller_id=user_id)
    except Exception as exc:
        raise _map_error(exc) from exc

    members = [
        {
            "membership_id": m.membership_id,
            "user_id": m.user_id,
            "role": m.role.value,
            "is_active": m.is_active,
            "joined_at": m.joined_at.isoformat(),
        }
        for m in community.memberships
    ]

    return {
        "community_id": community.community_id,
        "name": community.name,
        "description": community.description,
        "owner_id": community.owner_id,
        "avatar_url": community.avatar_url,
        "status": community.status.value,
        "created_at": community.created_at.isoformat(),
        "members": members,
    }


@router.patch("/{community_id}")
def update_community(
    community_id: str,
    body: CommunityUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyCommunityUnitOfWork = Depends(get_uow),
) -> dict:
    try:
        use_case = UpdateCommunityUseCase(uow)
        use_case.execute(
            community_id=community_id,
            caller_id=user_id,
            name=body.name,
            description=body.description,
            avatar_url=body.avatar_url,
        )
    except Exception as exc:
        raise _map_error(exc) from exc

    return {"message": "Community updated"}


@router.patch("/{community_id}/status")
def change_community_status(
    community_id: str,
    body: CommunityStatusChangeRequest,
    user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyCommunityUnitOfWork = Depends(get_uow),
) -> dict:
    try:
        target = CommunityStatus(body.status)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid status: {body.status}")

    try:
        use_case = ChangeCommunityStatusUseCase(uow)
        use_case.execute(community_id=community_id, caller_id=user_id, target_status=target)
    except Exception as exc:
        raise _map_error(exc) from exc

    return {"message": f"Community status changed to {target.value}"}


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------


@router.get("/{community_id}/members")
def list_members(
    community_id: str,
    user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyCommunityUnitOfWork = Depends(get_uow),
) -> list[dict]:
    try:
        use_case = GetCommunityUseCase(uow)
        community = use_case.execute(community_id=community_id, caller_id=user_id)
    except Exception as exc:
        raise _map_error(exc) from exc

    return [
        {
            "membership_id": m.membership_id,
            "user_id": m.user_id,
            "role": m.role.value,
            "is_active": m.is_active,
            "joined_at": m.joined_at.isoformat(),
        }
        for m in community.memberships
    ]


@router.post("/{community_id}/members", status_code=201)
def add_member(
    community_id: str,
    body: AddMemberRequest,
    user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyCommunityUnitOfWork = Depends(get_uow),
) -> dict:
    try:
        role = CommunityRole(body.role)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid role: {body.role}")

    try:
        use_case = AddMemberUseCase(uow)
        membership = use_case.execute(
            community_id=community_id,
            caller_id=user_id,
            user_id=body.user_id,
            role=role,
        )
    except Exception as exc:
        raise _map_error(exc) from exc

    return {
        "membership_id": membership.membership_id,
        "user_id": membership.user_id,
        "role": membership.role.value,
    }


@router.patch("/{community_id}/members/{target_user_id}/role")
def change_member_role(
    community_id: str,
    target_user_id: str,
    body: ChangeMemberRoleRequest,
    user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyCommunityUnitOfWork = Depends(get_uow),
) -> dict:
    try:
        role = CommunityRole(body.role)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid role: {body.role}")

    try:
        use_case = ChangeMemberRoleUseCase(uow)
        use_case.execute(
            community_id=community_id,
            caller_id=user_id,
            user_id=target_user_id,
            new_role=role,
        )
    except Exception as exc:
        raise _map_error(exc) from exc

    return {"message": "Member role updated"}


@router.delete("/{community_id}/members/{target_user_id}")
def remove_member(
    community_id: str,
    target_user_id: str,
    user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyCommunityUnitOfWork = Depends(get_uow),
) -> dict:
    try:
        use_case = RemoveMemberUseCase(uow)
        use_case.execute(
            community_id=community_id,
            caller_id=user_id,
            user_id=target_user_id,
        )
    except Exception as exc:
        raise _map_error(exc) from exc

    return {"message": "Member removed"}


# ---------------------------------------------------------------------------
# Fund
# ---------------------------------------------------------------------------


@router.get("/{community_id}/fund")
def get_fund(
    community_id: str,
    user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyCommunityUnitOfWork = Depends(get_uow),
) -> dict:
    try:
        use_case = GetFundUseCase(uow)
        fund = use_case.execute(community_id=community_id, caller_id=user_id)
    except Exception as exc:
        raise _map_error(exc) from exc

    if fund is None:
        return {"community_id": community_id, "balance": "0", "transactions": [], "distributions": []}

    txns = uow.fund.list_transactions(fund.fund_id)
    dists = uow.fund.list_distributions(fund.fund_id)

    return {
        "fund_id": fund.fund_id,
        "community_id": fund.community_id,
        "balance": str(fund.balance),
        "transactions": [
            {
                "transaction_id": t.transaction_id,
                "amount": str(t.amount),
                "source": t.source,
                "ref_id": t.ref_id,
                "created_at": t.created_at.isoformat(),
            }
            for t in txns
        ],
        "distributions": [
            {
                "distribution_id": d.distribution_id,
                "amount": str(d.amount),
                "initiated_by": d.initiated_by,
                "note": d.note,
                "status": d.status,
                "created_at": d.created_at.isoformat(),
            }
            for d in dists
        ],
    }


@router.post("/{community_id}/fund/deposit")
def deposit_to_fund(
    community_id: str,
    body: DepositRequest,
    user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyCommunityUnitOfWork = Depends(get_uow),
) -> dict:
    try:
        amount = Decimal(body.amount)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid amount")

    cmd = DepositToFundCommand(
        community_id=community_id,
        amount=amount,
        source=body.source,
        ref_id=body.ref_id,
    )

    try:
        use_case = DepositToFundUseCase(uow)
        fund = use_case.execute(cmd, caller_id=user_id)
    except Exception as exc:
        raise _map_error(exc) from exc

    return {"fund_id": fund.fund_id, "balance": str(fund.balance)}


@router.post("/{community_id}/fund/distribute")
def distribute_from_fund(
    community_id: str,
    body: DistributeRequest,
    user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyCommunityUnitOfWork = Depends(get_uow),
) -> dict:
    try:
        amount = Decimal(body.amount)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid amount")

    cmd = DistributeFromFundCommand(
        community_id=community_id,
        amount=amount,
        initiated_by=user_id,
        note=body.note,
    )

    try:
        use_case = DistributeFromFundUseCase(uow)
        fund = use_case.execute(cmd, caller_id=user_id)
    except Exception as exc:
        raise _map_error(exc) from exc

    return {"fund_id": fund.fund_id, "balance": str(fund.balance)}


# ---------------------------------------------------------------------------
# Feature Requests
# ---------------------------------------------------------------------------


@router.get("/{community_id}/feature-requests")
def list_feature_requests(
    community_id: str,
    status: str | None = None,
    user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyCommunityUnitOfWork = Depends(get_uow),
) -> list[dict]:
    fs = None
    if status is not None:
        try:
            fs = FeatureStatus(status)
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid status: {status}")

    try:
        use_case = ListFeatureRequestsUseCase(uow)
        requests = use_case.execute(
            community_id=community_id,
            caller_id=user_id,
            status=fs,
        )
    except Exception as exc:
        raise _map_error(exc) from exc

    return [
        {
            "request_id": r.request_id,
            "author_id": r.author_id,
            "title": r.title,
            "description": r.description,
            "status": r.status.value,
            "category": r.category,
            "priority": r.priority,
            "created_at": r.created_at.isoformat(),
        }
        for r in requests
    ]


@router.post("/{community_id}/feature-requests", status_code=201)
def submit_feature_request(
    community_id: str,
    body: FeatureRequestCreate,
    user_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyCommunityUnitOfWork = Depends(get_uow),
) -> dict:
    try:
        use_case = SubmitFeatureRequestUseCase(uow)
        fr = use_case.execute(
            request_id=str(uuid.uuid4()),
            community_id=community_id,
            author_id=user_id,
            title=body.title,
            description=body.description,
            category=body.category,
            priority=body.priority,
        )
    except Exception as exc:
        raise _map_error(exc) from exc

    return {
        "request_id": fr.request_id,
        "title": fr.title,
        "status": fr.status.value,
    }
