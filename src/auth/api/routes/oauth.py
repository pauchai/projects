"""OAuth routes: REST endpoints for Google OAuth authentication and linking."""

import secrets

from fastapi import APIRouter, Depends, HTTPException

from auth.api.dependencies import (
    get_auth_uow,
    get_current_user_id,
    get_google_oauth_client,
    get_token_service,
)
from auth.api.schemas import (
    MessageResponse,
    OAuthAuthorizeResponse,
    OAuthAvailableResponse,
    OAuthCallbackRequest,
    TokenResponse,
)
from auth.application.authenticate_with_oauth import AuthenticateWithOAuthUseCase
from auth.application.link_oauth_provider import LinkOAuthProviderUseCase
from auth.infrastructure.jwt_token_service import JwtTokenService
from auth.infrastructure.providers.google_oauth_client import GoogleOAuthClient
from auth.infrastructure.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/auth/oauth/google", tags=["oauth"])


@router.get("/available", response_model=OAuthAvailableResponse)
def google_oauth_available(
    oauth_client: GoogleOAuthClient | None = Depends(get_google_oauth_client),
) -> OAuthAvailableResponse:
    """Check whether Google OAuth is configured and available."""
    return OAuthAvailableResponse(available=oauth_client is not None)


@router.get("/authorize", response_model=OAuthAuthorizeResponse)
def google_oauth_authorize(
    oauth_client: GoogleOAuthClient | None = Depends(get_google_oauth_client),
) -> OAuthAuthorizeResponse:
    """Generate a Google OAuth authorization URL with a random state parameter."""
    if oauth_client is None:
        raise HTTPException(status_code=501, detail="Google OAuth is not configured")

    state = secrets.token_urlsafe(32)
    authorization_url = oauth_client.build_authorization_url(state)
    return OAuthAuthorizeResponse(authorization_url=authorization_url, state=state)


@router.post("/callback", response_model=TokenResponse)
def google_oauth_callback(
    body: OAuthCallbackRequest,
    oauth_client: GoogleOAuthClient | None = Depends(get_google_oauth_client),
    uow: SqlAlchemyUnitOfWork = Depends(get_auth_uow),
    token_service: JwtTokenService = Depends(get_token_service),
) -> TokenResponse:
    """Exchange a Google authorization code for a JWT access token.

    This endpoint is called by the frontend after the user completes
    the Google consent screen. It:
    1. Exchanges the code for a Google access token.
    2. Fetches the user's Google profile.
    3. Creates or links the user account.
    4. Returns a JWT access token.
    """
    if oauth_client is None:
        raise HTTPException(status_code=501, detail="Google OAuth is not configured")

    use_case = AuthenticateWithOAuthUseCase(
        uow=uow,
        oauth_client=oauth_client,
        token_service=token_service,
    )
    access_token = use_case.execute(code=body.code)
    return TokenResponse(access_token=access_token)


@router.post("/link", response_model=MessageResponse)
def google_oauth_link(
    body: OAuthCallbackRequest,
    caller_id: str = Depends(get_current_user_id),
    oauth_client: GoogleOAuthClient | None = Depends(get_google_oauth_client),
    uow: SqlAlchemyUnitOfWork = Depends(get_auth_uow),
) -> MessageResponse:
    """Link a Google account to the authenticated user.

    Uses the same authorization code flow as login, but instead of
    creating/logging in a user, it attaches the Google credential to
    the currently authenticated user.

    Raises:
        409: If the Google account is already linked to another user.
        422: If the user already has a Google credential.
    """
    if oauth_client is None:
        raise HTTPException(status_code=501, detail="Google OAuth is not configured")

    use_case = LinkOAuthProviderUseCase(uow=uow, oauth_client=oauth_client)
    use_case.execute(user_id=caller_id, code=body.code)
    return MessageResponse(message="Google account linked successfully")
