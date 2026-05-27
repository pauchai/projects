"""Pydantic schemas for Auth API request/response serialization."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    """POST /auth/register"""

    email: str = Field(min_length=1)
    password: str = Field(min_length=1)
    display_name: str = Field(min_length=1, max_length=100)


class LoginRequest(BaseModel):
    """POST /auth/login"""

    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


class SetPasswordRequest(BaseModel):
    """POST /auth/local/set-password"""

    password: str = Field(min_length=1)


class UpdateProfileRequest(BaseModel):
    """PATCH /auth/me — update email and/or display_name.

    Both fields are optional. Omitting a field leaves it unchanged.
    """

    email: str | None = None
    display_name: str | None = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class TokenResponse(BaseModel):
    """Response containing an access token."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Serialized user info returned on registration."""

    user_id: str
    email: str
    display_name: str


class OAuthCallbackRequest(BaseModel):
    """POST /auth/oauth/google/callback"""

    code: str = Field(min_length=1)
    state: str = Field(min_length=1)


class OAuthAuthorizeResponse(BaseModel):
    """Response with the OAuth authorization URL."""

    authorization_url: str
    state: str


class OAuthAvailableResponse(BaseModel):
    """Response indicating whether an OAuth provider is configured."""

    available: bool


class TelegramAuthorizeResponse(BaseModel):
    """Response with the Telegram deep link URL and state."""

    telegram_url: str
    state: str


class TelegramBotCallbackRequest(BaseModel):
    """POST /auth/oauth/telegram/bot-callback — sent by the Telegram bot."""

    auth_code: str = Field(min_length=1)
    telegram_user_id: str = Field(min_length=1)
    telegram_username: str | None = None
    telegram_first_name: str = Field(min_length=1)


class TelegramBotCallbackResponse(BaseModel):
    """Response to the bot after successful bot-callback."""

    authorization_code: str
    state: str


class MessageResponse(BaseModel):
    """Generic success/info response."""

    message: str


# ---------------------------------------------------------------------------
# Credentials management
# ---------------------------------------------------------------------------


class CredentialSchema(BaseModel):
    """A single credential summary for UI display."""

    credential_id: str
    provider: str
    provider_display_name: str
    provider_user_id: str
    is_removable: bool


class CredentialsListResponse(BaseModel):
    """GET /auth/credentials — all credentials for the authenticated user."""

    user_email: str
    user_display_name: str
    credentials: list[CredentialSchema]
    total_count: int
    has_local_credential: bool
    created_at: str = ""
    scope: str = ""
    project_id: str | None = None
    role: str | None = None
