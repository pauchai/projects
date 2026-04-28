"""Auth routes: REST endpoints for user registration, authentication, and profile."""

import uuid

from fastapi import APIRouter, Depends

from auth.api.dependencies import (
    get_auth_uow,
    get_current_user_id,
    get_password_hasher,
    get_token_service,
)
from auth.api.schemas import (
    LoginRequest,
    MessageResponse,
    ReferralResponse,
    ReferralsListResponse,
    RegisterRequest,
    SetPasswordRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserInviteCodeResponse,
    UserResponse,
)
from auth.application.authenticate import AuthenticateUseCase
from auth.application.create_user_invite_code import CreateUserInviteCodeUseCase
from auth.application.register_user_with_invite import RegisterUserWithInviteUseCase
from auth.application.set_password import SetPasswordUseCase
from auth.application.update_profile import UpdateProfileUseCase
from auth.infrastructure.bcrypt_password_hasher import BcryptPasswordHasher
from auth.infrastructure.jwt_token_service import JwtTokenService
from auth.infrastructure.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/register", status_code=201, response_model=UserResponse)
def register(
    body: RegisterRequest,
    uow: SqlAlchemyUnitOfWork = Depends(get_auth_uow),
    password_hasher: BcryptPasswordHasher = Depends(get_password_hasher),
) -> UserResponse:
    """Register a new user with email, password and a valid invite code."""
    use_case = RegisterUserWithInviteUseCase(uow, password_hasher)
    user_id = str(uuid.uuid4())
    use_case.execute(
        user_id=user_id,
        email=body.email,
        password=body.password,
        display_name=body.display_name,
        invite_code=body.invite_code,
    )
    return UserResponse(
        user_id=user_id,
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
    caller_id: str = Depends(get_current_user_id),
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
    caller_id: str = Depends(get_current_user_id),
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
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_auth_uow),
) -> UserInviteCodeResponse:
    """Create a personal invite code for the authenticated user.

    The code expires in 7 days and is single-use by default.
    """
    use_case = CreateUserInviteCodeUseCase(uow)
    invite = use_case.execute(user_id=caller_id)
    return UserInviteCodeResponse(
        code_id=invite.code_id,
        code=invite.code,
        uses_left=invite.uses_left,
        max_uses=invite.max_uses,
        is_active=invite.is_active,
        expires_at=invite.expires_at.isoformat(),  # type: ignore[union-attr]
        created_at=invite.created_at.isoformat(),
    )


@router.get("/referrals", response_model=ReferralsListResponse)
def get_referrals(
    caller_id: str = Depends(get_current_user_id),
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
