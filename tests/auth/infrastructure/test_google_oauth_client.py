"""Unit tests for GoogleOAuthClient — TDD with httpx mock transport."""

from __future__ import annotations

import json
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from auth.domain.oauth import OAuthError, OAuthUserInfo
from auth.infrastructure.providers.google_oauth_client import GoogleOAuthClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CLIENT_ID = "test-client-id.apps.googleusercontent.com"
CLIENT_SECRET = "test-client-secret"
REDIRECT_URI = "http://localhost:8000/auth/oauth/google/callback"


def _make_client(
    token_response: httpx.Response | None = None,
    userinfo_response: httpx.Response | None = None,
) -> GoogleOAuthClient:
    """Create a GoogleOAuthClient with a mocked HTTP transport."""

    def _handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "oauth2.googleapis.com/token" in url:
            if token_response is not None:
                return token_response
            return httpx.Response(
                200,
                json={"access_token": "mock-access-token", "token_type": "Bearer"},
            )
        if "googleapis.com/oauth2/v2/userinfo" in url:
            if userinfo_response is not None:
                return userinfo_response
            return httpx.Response(
                200,
                json={
                    "id": "google-sub-123",
                    "email": "alice@gmail.com",
                    "name": "Alice Smith",
                    "verified_email": True,
                },
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(_handler)
    http_client = httpx.Client(transport=transport)
    return GoogleOAuthClient(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        http_client=http_client,
    )


# ---------------------------------------------------------------------------
# Tests: build_authorization_url
# ---------------------------------------------------------------------------


class TestBuildAuthorizationUrl:
    """Tests for Google OAuth authorization URL construction."""

    def test_url_points_to_google_accounts(self) -> None:
        client = _make_client()

        url = client.build_authorization_url(state="abc123")

        parsed = urlparse(url)
        assert parsed.scheme == "https"
        assert parsed.hostname == "accounts.google.com"

    def test_url_contains_client_id(self) -> None:
        client = _make_client()

        url = client.build_authorization_url(state="abc123")

        params = parse_qs(urlparse(url).query)
        assert params["client_id"] == [CLIENT_ID]

    def test_url_contains_redirect_uri(self) -> None:
        client = _make_client()

        url = client.build_authorization_url(state="abc123")

        params = parse_qs(urlparse(url).query)
        assert params["redirect_uri"] == [REDIRECT_URI]

    def test_url_contains_state(self) -> None:
        client = _make_client()

        url = client.build_authorization_url(state="my-state-value")

        params = parse_qs(urlparse(url).query)
        assert params["state"] == ["my-state-value"]

    def test_url_requests_code_response_type(self) -> None:
        client = _make_client()

        url = client.build_authorization_url(state="abc123")

        params = parse_qs(urlparse(url).query)
        assert params["response_type"] == ["code"]

    def test_url_requests_openid_email_profile_scopes(self) -> None:
        client = _make_client()

        url = client.build_authorization_url(state="abc123")

        params = parse_qs(urlparse(url).query)
        scopes = params["scope"][0].split()
        assert "openid" in scopes
        assert "email" in scopes
        assert "profile" in scopes

    def test_url_includes_access_type_offline(self) -> None:
        client = _make_client()

        url = client.build_authorization_url(state="abc123")

        params = parse_qs(urlparse(url).query)
        assert params["access_type"] == ["offline"]


# ---------------------------------------------------------------------------
# Tests: exchange_code
# ---------------------------------------------------------------------------


class TestExchangeCode:
    """Tests for authorization code -> access token exchange."""

    def test_returns_access_token_on_success(self) -> None:
        client = _make_client()

        token = client.exchange_code("valid-auth-code")

        assert token == "mock-access-token"

    def test_raises_oauth_error_on_http_error(self) -> None:
        client = _make_client(
            token_response=httpx.Response(400, json={"error": "invalid_grant"})
        )

        with pytest.raises(OAuthError, match="token exchange"):
            client.exchange_code("bad-code")

    def test_raises_oauth_error_on_missing_access_token(self) -> None:
        client = _make_client(
            token_response=httpx.Response(200, json={"token_type": "Bearer"})
        )

        with pytest.raises(OAuthError, match="access_token"):
            client.exchange_code("some-code")


# ---------------------------------------------------------------------------
# Tests: get_user_info
# ---------------------------------------------------------------------------


class TestGetUserInfo:
    """Tests for fetching user profile from Google."""

    def test_returns_oauth_user_info(self) -> None:
        client = _make_client()

        info = client.get_user_info("mock-access-token")

        assert isinstance(info, OAuthUserInfo)
        assert info.provider == "google"
        assert info.provider_user_id == "google-sub-123"
        assert info.email == "alice@gmail.com"
        assert info.display_name == "Alice Smith"

    def test_raises_oauth_error_on_http_error(self) -> None:
        client = _make_client(
            userinfo_response=httpx.Response(401, json={"error": "invalid_token"})
        )

        with pytest.raises(OAuthError, match="user info"):
            client.get_user_info("bad-token")

    def test_raises_oauth_error_on_unverified_email(self) -> None:
        client = _make_client(
            userinfo_response=httpx.Response(
                200,
                json={
                    "id": "google-sub-456",
                    "email": "bob@gmail.com",
                    "name": "Bob",
                    "verified_email": False,
                },
            )
        )

        with pytest.raises(OAuthError, match="verified"):
            client.get_user_info("some-token")

    def test_raises_oauth_error_on_missing_email(self) -> None:
        client = _make_client(
            userinfo_response=httpx.Response(
                200,
                json={
                    "id": "google-sub-789",
                    "name": "No Email User",
                    "verified_email": True,
                },
            )
        )

        with pytest.raises(OAuthError, match="email"):
            client.get_user_info("some-token")
