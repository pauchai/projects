"""Google OAuth 2.0 HTTP client (driven adapter).

Implements the ``OAuthClient`` protocol defined in ``auth.domain.ports``.
Communicates with Google's OAuth 2.0 endpoints to:
1. Build the authorization URL for the consent screen.
2. Exchange an authorization code for an access token.
3. Fetch user profile data using the access token.

Uses ``httpx.Client`` for synchronous HTTP — the client instance can be
injected (e.g., a mock transport in tests) or created internally.
"""

from __future__ import annotations

from urllib.parse import urlencode

import httpx

from auth.domain.oauth import OAuthError, OAuthUserInfo

# Google OAuth 2.0 endpoints
_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

_DEFAULT_SCOPES = "openid email profile"


class GoogleOAuthClient:
    """Google OAuth 2.0 client — implements OAuthClient port.

    Args:
        client_id: Google OAuth client ID.
        client_secret: Google OAuth client secret.
        redirect_uri: Registered redirect URI for the callback.
        http_client: Optional ``httpx.Client`` instance (for testing).
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._http = http_client or httpx.Client(timeout=10.0)

    # ------------------------------------------------------------------
    # OAuthClient protocol methods
    # ------------------------------------------------------------------

    def build_authorization_url(self, state: str) -> str:
        """Build the Google OAuth consent screen URL."""
        params = {
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
            "response_type": "code",
            "scope": _DEFAULT_SCOPES,
            "access_type": "offline",
            "state": state,
        }
        return f"{_AUTHORIZE_URL}?{urlencode(params)}"

    def exchange_code(self, code: str) -> str:
        """Exchange an authorization code for an access token.

        Raises:
            OAuthError: If the token exchange fails or the response
                does not contain an access token.
        """
        try:
            response = self._http.post(
                _TOKEN_URL,
                data={
                    "code": code,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "redirect_uri": self._redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
        except httpx.HTTPError as exc:
            raise OAuthError(f"Failed token exchange: {exc}") from exc

        if response.status_code != 200:
            raise OAuthError(
                f"Google token exchange failed (HTTP {response.status_code})"
            )

        data = response.json()
        access_token = data.get("access_token")
        if not access_token:
            raise OAuthError("Google token response missing access_token")
        return access_token

    def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Fetch user profile from Google using the access token.

        Raises:
            OAuthError: If the request fails, the email is not verified,
                or required fields are missing.
        """
        try:
            response = self._http.get(
                _USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        except httpx.HTTPError as exc:
            raise OAuthError(f"Failed to fetch user info: {exc}") from exc

        if response.status_code != 200:
            raise OAuthError(
                f"Google user info request failed (HTTP {response.status_code})"
            )

        data = response.json()

        email = data.get("email")
        if not email:
            raise OAuthError("Google user info missing email")

        if not data.get("verified_email", False):
            raise OAuthError("Google email is not verified")

        return OAuthUserInfo(
            provider="google",
            provider_user_id=data["id"],
            email=email,
            display_name=data.get("name", email),
        )
