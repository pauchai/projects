"""Auth routes: REST endpoints for user registration, authentication, and profile."""

import logging
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth.api.dependencies import (
    get_auth_uow,
    get_current_user_id,
    get_password_hasher,
    get_pending_user_id,
    get_token_service,
    require_active_user,
)
from auth.api.schemas import (
    ActivateAccountRequest,
    LoginRequest,
    MessageResponse,
    ReferralResponse,
    ReferralsListResponse,
    RegisterRequest,
    SetPasswordRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserInviteCodeRequest,
    UserInviteCodeResponse,
    UserResponse,
)
from auth.application.authenticate import AuthenticateUseCase
from auth.application.activate_user_with_invite import ActivateUserWithInviteUseCase
from auth.application.create_user_invite_code import CreateUserInviteCodeUseCase
from auth.application.register_user_with_invite import RegisterUserWithInviteUseCase
from auth.application.set_password import SetPasswordUseCase
from auth.application.update_profile import UpdateProfileUseCase
from auth.infrastructure.bcrypt_password_hasher import BcryptPasswordHasher
from auth.infrastructure.jwt_token_service import JwtTokenService
from auth.infrastructure.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork
from community.api.dependencies import get_uow as get_community_uow
from community.application.redeem_community_invite import RedeemCommunityInviteUseCase
from community.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyCommunityUnitOfWork as CommunityUoW,
)
from project_collaboration.api.dependencies import get_uow as get_collab_uow
from project_collaboration.application.redeem_project_invite import (
    RedeemProjectInviteUseCase,
)
from project_collaboration.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork as CollabUnitOfWork,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/register", status_code=201, response_model=UserResponse)
def register(
    body: RegisterRequest,
    uow: SqlAlchemyUnitOfWork = Depends(get_auth_uow),
    collab_uow: CollabUnitOfWork = Depends(get_collab_uow),
    community_uow: CommunityUoW = Depends(get_community_uow),
    password_hasher: BcryptPasswordHasher = Depends(get_password_hasher),
) -> UserResponse:
    """Register a new user with email, password and a valid invite code.

    When the invite code has ``scope="project"``, the new user is automatically
    enrolled as a project member (via ``RedeemProjectInviteUseCase``).
    When the invite code has ``scope="community"``, the new user is automatically
    added to the community (via ``RedeemCommunityInviteUseCase``).
    """
    use_case = RegisterUserWithInviteUseCase(uow, password_hasher)
    user_id = str(uuid.uuid4())
    result = use_case.execute(
        user_id=user_id,
        email=body.email,
        password=body.password,
        display_name=body.display_name,
        invite_code=body.invite_code,
    )

    # Route by scope — handler owns this decision (SRP: use case stays context-agnostic)
    if result.scope == "project" and result.project_id:
        try:
            RedeemProjectInviteUseCase(collab_uow).execute(
                user_id=result.user_id,
                project_id=result.project_id,
                role_value=result.role or "member",
            )
        except (LookupError, ValueError) as exc:
            logger.warning(
                "RedeemProjectInvite failed for user=%s project=%s: %s",
                result.user_id,
                result.project_id,
                exc,
            )

    if result.scope == "community" and result.community_id:
        try:
            RedeemCommunityInviteUseCase(community_uow).execute(
                user_id=result.user_id,
                community_id=result.community_id,
                role_value=result.role or "member",
            )
        except (LookupError, ValueError) as exc:
            logger.warning(
                "RedeemCommunityInvite failed for user=%s community=%s: %s",
                result.user_id,
                result.community_id,
                exc,
            )

    return UserResponse(
        user_id=result.user_id,
        email=body.email.strip().lower(),
        display_name=body.display_name.strip(),
    )


@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    uow: SqlAlchemyUnitOfWork = Depends(get_auth_uow),
    password_hasher: BcryptPasswordHasher = Depends(get_password_hasher),
    token_service: JwtTokenService = Depends(get_token_service),
) -> TokenResponse:
    """Authenticate with email and password, receive a JWT token."""
    use_case = AuthenticateUseCase(uow, password_hasher, token_service)
    access_token = use_case.execute(email=body.email, password=body.password)
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
def get_me(
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_auth_uow),
) -> UserResponse:
    """Return the currently authenticated user's profile info."""
    with uow:
        user = uow.users.find_by_id(caller_id)
        if user is None:
            raise LookupError(f"User {caller_id} not found")
        return UserResponse(
            user_id=user.user_id,
            email=user.email,
            display_name=user.display_name,
        )


@router.post("/local/set-password", response_model=MessageResponse)
def set_password(
    body: SetPasswordRequest,
    caller_id: str = Depends(require_active_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_auth_uow),
    password_hasher: BcryptPasswordHasher = Depends(get_password_hasher),
) -> MessageResponse:
    """Set password for an authenticated user who doesn't have local credentials."""
    use_case = SetPasswordUseCase(uow, password_hasher)
    use_case.execute(user_id=caller_id, password=body.password)
    return MessageResponse(message="Password set successfully")


@router.patch("/me", response_model=UserResponse)
def update_me(
    body: UpdateProfileRequest,
    caller_id: str = Depends(require_active_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_auth_uow),
) -> UserResponse:
    """Update the authenticated user's email and/or display_name.

    Both fields are optional — omitting a field leaves it unchanged.
    Returns the updated user profile.
    """
    use_case = UpdateProfileUseCase(uow)
    updated = use_case.execute(
        caller_id, email=body.email, display_name=body.display_name
    )
    return UserResponse(
        user_id=updated.user_id,
        email=updated.email,
        display_name=updated.display_name,
    )


@router.post("/invite-codes", status_code=201, response_model=UserInviteCodeResponse)
def create_invite_code(
    body: UserInviteCodeRequest = UserInviteCodeRequest(),
    caller_id: str = Depends(require_active_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_auth_uow),
) -> UserInviteCodeResponse:
    """Create a personal invite code for the authenticated user.

    The code expires in 7 days and is single-use by default.
    Optionally accepts ``scope``, ``project_id``, and ``role`` to generate
    a project-scoped invite that auto-enrols the registrant as a member.
    """
    use_case = CreateUserInviteCodeUseCase(uow)
    invite = use_case.execute(
        user_id=caller_id,
        scope=body.scope,  # type: ignore[arg-type]
        project_id=body.project_id,
        role=body.role,
    )
    return UserInviteCodeResponse(
        code_id=invite.code_id,
        code=invite.code,
        uses_left=invite.uses_left,
        max_uses=invite.max_uses,
        is_active=invite.is_active,
        expires_at=invite.expires_at.isoformat(),  # type: ignore[union-attr]
        created_at=invite.created_at.isoformat(),
        scope=invite.scope,
        project_id=invite.project_id,
        role=invite.role,
    )


@router.get("/referrals", response_model=ReferralsListResponse)
def get_referrals(
    caller_id: str = Depends(require_active_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_auth_uow),
) -> ReferralsListResponse:
    """Return a list of users invited by the currently authenticated user."""
    with uow:
        users = uow.users.find_by_inviter_id(caller_id)
        return ReferralsListResponse(
            total=len(users),
            referrals=[
                ReferralResponse(
                    user_id=u.user_id,
                    display_name=u.display_name,
                    joined_at=u.created_at.isoformat(),
                )
                for u in users
            ],
        )


@router.post("/activate", response_model=TokenResponse)
def activate_account(
    body: ActivateAccountRequest,
    caller_id: str = Depends(get_pending_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_auth_uow),
    token_service: JwtTokenService = Depends(get_token_service),
) -> TokenResponse:
    """Activate a pending account by redeeming a valid invite code.

    Accepts a JWT from a pending user (i.e. registered via OAuth without a code).
    On success returns a new access token with status='active'.
    """
    use_case = ActivateUserWithInviteUseCase(uow, token_service)
    access_token = use_case.execute(user_id=caller_id, invite_code=body.invite_code)
    return TokenResponse(access_token=access_token)


# ---------------------------------------------------------------------------
# Test-only endpoint (E2E helpers)
# ---------------------------------------------------------------------------


class _PendingTokenRequest(BaseModel):
    user_id: str


@router.post("/test/pending-token", include_in_schema=False, response_model=TokenResponse)
def test_pending_token(
    body: _PendingTokenRequest,
    token_service: JwtTokenService = Depends(get_token_service),
) -> TokenResponse:
    """Return a JWT with status='pending' for the given user_id.

    ONLY available when E2E_ALLOW_PENDING_TOKEN=1 is set in the environment.
    Used exclusively by Playwright E2E tests to simulate an OAuth-created
    pending account without needing a real OAuth provider.
    """
    if os.getenv("E2E_ALLOW_PENDING_TOKEN") != "1":
        raise HTTPException(status_code=404, detail="Not found")
    access_token = token_service.create_access_token(body.user_id, status="pending")
    return TokenResponse(access_token=access_token)
