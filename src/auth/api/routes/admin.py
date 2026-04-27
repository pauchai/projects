"""Admin routes: invite code management.

Protected by ``X-Admin-Secret`` header. The expected secret is read from
the ``ADMIN_SECRET`` environment variable (default: ``"change-me"``).
"""

from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException

from auth.api.dependencies import get_auth_uow
from auth.api.schemas import (
    CreateInviteCodesRequest,
    CreateInviteCodesResponse,
    InviteCodeResponse,
    ListInviteCodesResponse,
)
from auth.application.create_invite_codes import CreateInviteCodesUseCase
from auth.infrastructure.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/admin", tags=["admin"])

ADMIN_USER_ID = "system-admin"


def _get_admin_secret() -> str:
    return os.environ.get("ADMIN_SECRET", "change-me")


def verify_admin_secret(
    x_admin_secret: str | None = Header(None, alias="X-Admin-Secret"),
) -> None:
    """FastAPI dependency: raise 403 if the admin secret header is missing or wrong."""
    expected = _get_admin_secret()
    if x_admin_secret is None or x_admin_secret != expected:
        raise HTTPException(status_code=403, detail="Forbidden")


def _to_response(c: object) -> InviteCodeResponse:  # type: ignore[type-arg]
    from auth.domain.invite_code import (
        InviteCode as _IC,
    )  # local import to avoid cycles

    assert isinstance(c, _IC)
    return InviteCodeResponse(
        code_id=c.code_id,
        code=c.code,
        uses_left=c.uses_left,
        max_uses=c.max_uses,
        is_active=c.is_active,
        created_at=c.created_at.isoformat(),
    )


@router.get(
    "/invite-codes",
    status_code=200,
    response_model=ListInviteCodesResponse,
    dependencies=[Depends(verify_admin_secret)],
)
def list_invite_codes(
    uow: SqlAlchemyUnitOfWork = Depends(get_auth_uow),
) -> ListInviteCodesResponse:
    """Return all invite codes (admin only)."""
    with uow:
        codes = uow.invite_codes.find_all()
        return ListInviteCodesResponse(codes=[_to_response(c) for c in codes])


@router.post(
    "/invite-codes",
    status_code=201,
    response_model=CreateInviteCodesResponse,
    dependencies=[Depends(verify_admin_secret)],
)
def create_invite_codes(
    body: CreateInviteCodesRequest,
    uow: SqlAlchemyUnitOfWork = Depends(get_auth_uow),
) -> CreateInviteCodesResponse:
    """Generate a batch of invite codes (admin only)."""
    use_case = CreateInviteCodesUseCase(uow)
    codes = use_case.execute(
        admin_user_id=ADMIN_USER_ID,
        count=body.count,
        max_uses=body.max_uses,
    )
    return CreateInviteCodesResponse(codes=[_to_response(c) for c in codes])
