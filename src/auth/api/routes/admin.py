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
    return CreateInviteCodesResponse(
        codes=[
            InviteCodeResponse(
                code_id=c.code_id,
                code=c.code,
                uses_left=c.uses_left,
                max_uses=c.max_uses,
                is_active=c.is_active,
            )
            for c in codes
        ]
    )
