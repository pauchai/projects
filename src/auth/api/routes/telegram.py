"""Telegram OAuth routes: REST endpoints for Telegram bot-based authentication.

Flow:
1. GET /authorize — generates auth_code + state, stores in DB, returns Telegram deep link.
2. POST /bot-callback — bot sends telegram user data + auth_code (internal API).
3. POST /callback — frontend exchanges authorization_code + state for JWT.
4. POST /link — links Telegram account to the authenticated user.
"""

import secrets

from fastapi import APIRouter, Depends, HTTPException

from auth.api.dependencies import (
    get_auth_uow,
    get_current_user_id,
    get_telegram_oauth_client,
    get_token_service,
)
from auth.api.schemas import (
    MessageResponse,
    OAuthAvailableResponse,
    OAuthCallbackRequest,
    TelegramAuthorizeResponse,
    TelegramBotCallbackRequest,
    TelegramBotCallbackResponse,
    TokenResponse,
)
from auth.application.authenticate_with_oauth import AuthenticateWithOAuthUseCase
from auth.application.link_oauth_provider import LinkOAuthProviderUseCase
from auth.domain.telegram_auth_request import TelegramAuthRequest
from auth.infrastructure.jwt_token_service import JwtTokenService
from auth.infrastructure.providers.telegram_oauth_client import TelegramOAuthClient
from auth.infrastructure.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/auth/oauth/telegram", tags=["telegram-oauth"])


@router.get("/available", response_model=OAuthAvailableResponse)
def telegram_oauth_available(
    oauth_client: TelegramOAuthClient | None = Depends(get_telegram_oauth_client),
) -> OAuthAvailableResponse:
    """Check whether Telegram OAuth is configured and available."""
    return OAuthAvailableResponse(available=oauth_client is not None)


@router.get("/authorize", response_model=TelegramAuthorizeResponse)
def telegram_oauth_authorize(
    oauth_client: TelegramOAuthClient | None = Depends(get_telegram_oauth_client),
    uow: SqlAlchemyUnitOfWork = Depends(get_auth_uow),
) -> TelegramAuthorizeResponse:
    """Generate a Telegram deep link for bot-based auth.

    Creates a TelegramAuthRequest with a unique auth_code and state,
    stores it in the DB, and returns the Telegram deep link URL.
    """
    if oauth_client is None:
        raise HTTPException(status_code=501, detail="Telegram OAuth is not configured")

    auth_code = secrets.token_urlsafe(32)
    state = secrets.token_urlsafe(32)

    auth_request = TelegramAuthRequest(auth_code=auth_code, state=state)

    with uow:
        uow.telegram_auth_requests.save(auth_request)
        uow.commit()

    telegram_url = oauth_client.build_authorization_url(auth_code)

    return TelegramAuthorizeResponse(telegram_url=telegram_url, state=state)


@router.post("/bot-callback", response_model=TelegramBotCallbackResponse)
def telegram_bot_callback(
    body: TelegramBotCallbackRequest,
    oauth_client: TelegramOAuthClient | None = Depends(get_telegram_oauth_client),
    uow: SqlAlchemyUnitOfWork = Depends(get_auth_uow),
) -> TelegramBotCallbackResponse:
    """Internal endpoint called by the Telegram bot after /start command.

    Receives telegram user data and fills it into the auth request.
    Returns the authorization_code + state for the bot to send to the user.
    """
    if oauth_client is None:
        raise HTTPException(status_code=501, detail="Telegram OAuth is not configured")

    with uow:
        auth_request = uow.telegram_auth_requests.find_by_auth_code(body.auth_code)
        if auth_request is None:
            raise HTTPException(status_code=404, detail="Auth request not found")

        if auth_request.is_used:
            raise HTTPException(
                status_code=400, detail="Auth request has already been used"
            )

        authorization_code = secrets.token_urlsafe(32)

        auth_request.fill_telegram_data(
            telegram_user_id=body.telegram_user_id,
            telegram_username=body.telegram_username,
            telegram_first_name=body.telegram_first_name,
            authorization_code=authorization_code,
        )

        uow.telegram_auth_requests.save(auth_request)
        uow.commit()

        return TelegramBotCallbackResponse(
            authorization_code=authorization_code,
            state=auth_request.state,
        )


@router.post("/callback", response_model=TokenResponse)
def telegram_oauth_callback(
    body: OAuthCallbackRequest,
    oauth_client: TelegramOAuthClient | None = Depends(get_telegram_oauth_client),
    uow: SqlAlchemyUnitOfWork = Depends(get_auth_uow),
    token_service: JwtTokenService = Depends(get_token_service),
) -> TokenResponse:
    """Exchange a Telegram authorization code for a JWT access token.

    Called by the frontend after the user clicks the auth link sent by the bot.
    1. Looks up the TelegramAuthRequest by authorization_code.
    2. Validates the state parameter.
    3. Passes the request to TelegramOAuthClient.
    4. Runs AuthenticateWithOAuthUseCase to create/link user + return JWT.
    """
    if oauth_client is None:
        raise HTTPException(status_code=501, detail="Telegram OAuth is not configured")

    # Look up the auth request by the authorization code
    with uow:
        auth_request = uow.telegram_auth_requests.find_by_authorization_code(body.code)
        if auth_request is None:
            raise HTTPException(status_code=400, detail="Invalid authorization code")

        if auth_request.state != body.state:
            raise HTTPException(status_code=400, detail="State mismatch")

        if auth_request.is_used:
            raise HTTPException(
                status_code=400, detail="Authorization code has already been used"
            )

        # Mark as used to prevent replay
        auth_request.consume()
        uow.telegram_auth_requests.save(auth_request)
        uow.commit()

    # Inject the auth request data into the OAuth client.
    # Note: consume() sets is_used=True, but the client only needs
    # telegram user data and authorization_code — not the is_ready flag.
    oauth_client.set_auth_request(auth_request)

    # Reuse the standard OAuth use case
    use_case = AuthenticateWithOAuthUseCase(
        uow=uow,
        oauth_client=oauth_client,
        token_service=token_service,
    )
    access_token = use_case.execute(code=body.code)
    return TokenResponse(access_token=access_token)


@router.post("/link", response_model=MessageResponse)
def telegram_oauth_link(
    body: OAuthCallbackRequest,
    caller_id: str = Depends(get_current_user_id),
    oauth_client: TelegramOAuthClient | None = Depends(get_telegram_oauth_client),
    uow: SqlAlchemyUnitOfWork = Depends(get_auth_uow),
) -> MessageResponse:
    """Link a Telegram account to the authenticated user.

    Same flow as /callback, but instead of login/register it attaches
    the Telegram credential to the currently authenticated user.

    Raises:
        409: If the Telegram account is already linked to another user.
        422: If the user already has a Telegram credential.
    """
    if oauth_client is None:
        raise HTTPException(status_code=501, detail="Telegram OAuth is not configured")

    # Look up and validate the auth request (same as /callback)
    with uow:
        auth_request = uow.telegram_auth_requests.find_by_authorization_code(body.code)
        if auth_request is None:
            raise HTTPException(status_code=400, detail="Invalid authorization code")

        if auth_request.state != body.state:
            raise HTTPException(status_code=400, detail="State mismatch")

        if auth_request.is_used:
            raise HTTPException(
                status_code=400, detail="Authorization code has already been used"
            )

        auth_request.consume()
        uow.telegram_auth_requests.save(auth_request)
        uow.commit()

    # Inject the auth request data into the OAuth client.
    oauth_client.set_auth_request(auth_request)

    use_case = LinkOAuthProviderUseCase(uow=uow, oauth_client=oauth_client)
    use_case.execute(user_id=caller_id, code=body.code)
    return MessageResponse(message="Telegram account linked successfully")
