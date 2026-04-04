"""Auth routes: REST endpoints for user registration and authentication."""

import uuid

from fastapi import APIRouter, Depends

from auth.api.dependencies import get_auth_uow, get_password_hasher, get_token_service
from auth.api.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from auth.application.authenticate import AuthenticateUseCase
from auth.application.register_user import RegisterUserUseCase
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
    """Register a new user with email and password."""
    use_case = RegisterUserUseCase(uow, password_hasher)
    user_id = str(uuid.uuid4())
    use_case.execute(
        user_id=user_id,
        email=body.email,
        password=body.password,
        display_name=body.display_name,
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
