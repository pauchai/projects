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
    """Response indicating whether Google OAuth is configured."""

    available: bool


class MessageResponse(BaseModel):
    """Generic success/info response."""

    message: str
