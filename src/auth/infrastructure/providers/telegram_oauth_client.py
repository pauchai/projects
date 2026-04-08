"""Telegram OAuth client adapter (driven adapter).

Implements the ``OAuthClient`` protocol defined in ``auth.domain.ports``.
Unlike Google OAuth, Telegram does not use a standard OAuth 2.0 flow.
Instead, user data is collected by the Telegram bot and stored in the
``telegram_auth_requests`` table. This adapter retrieves that data
when the frontend exchanges the authorization code.

Key differences from GoogleOAuthClient:
- ``build_authorization_url`` generates a ``tg://resolve`` deep link.
- ``exchange_code`` looks up the authorization_code in the DB (no HTTP call).
- ``get_user_info`` returns data already stored in the DB by the bot.
- Telegram does not provide email, so a synthetic email is generated.
"""

from __future__ import annotations

from auth.domain.oauth import OAuthError, OAuthUserInfo
from auth.domain.telegram_auth_request import TelegramAuthRequest

# Synthetic email domain for Telegram users who have no real email.
_TELEGRAM_EMAIL_DOMAIN = "telegram.user"


class TelegramOAuthClient:
    """Telegram OAuth-like client — implements OAuthClient port.

    This adapter is stateful per-request: ``exchange_code`` stores the
    found ``TelegramAuthRequest`` so that ``get_user_info`` can access
    the telegram data without a second DB lookup. This matches the
    ``OAuthClient`` protocol contract where ``exchange_code`` is called
    first, followed by ``get_user_info``.

    Args:
        bot_username: The Telegram bot username (without @).
    """

    def __init__(self, bot_username: str) -> None:
        self._bot_username = bot_username
        self._current_request: TelegramAuthRequest | None = None

    def build_authorization_url(self, state: str) -> str:
        """Build a Telegram deep link URL for the bot /start command.

        The auth_code is embedded in the state parameter to be used
        as the /start payload. The actual state is stored server-side.
        """
        # The state parameter here is actually the auth_code for the deep link
        return f"https://t.me/{self._bot_username}?start={state}"

    def exchange_code(self, code: str) -> str:
        """Look up the authorization code in the stored request.

        For Telegram, the 'code' is the authorization_code generated
        by the bot-callback endpoint. This method validates it and
        stores the request for ``get_user_info``.

        Note: The actual DB lookup happens in the route handler, which
        passes the TelegramAuthRequest to this client via ``set_auth_request``.

        Returns:
            A dummy access token (the authorization_code itself) since
            Telegram doesn't use real access tokens.

        Raises:
            OAuthError: If no auth request was set or the code doesn't match.
        """
        if self._current_request is None:
            raise OAuthError("No Telegram auth request found for this code")
        if self._current_request.authorization_code != code:
            raise OAuthError("Authorization code mismatch")
        return code

    def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Return user info from the stored TelegramAuthRequest.

        Generates a synthetic email since Telegram doesn't provide one.

        Raises:
            OAuthError: If no auth request data is available.
        """
        req = self._current_request
        if req is None or req.telegram_user_id is None:
            raise OAuthError("No Telegram user data available")

        # Telegram doesn't provide email — generate a synthetic one
        # based on the Telegram user ID. This ensures uniqueness and
        # allows the existing User model (which requires email) to work.
        synthetic_email = f"{req.telegram_user_id}@{_TELEGRAM_EMAIL_DOMAIN}"

        display_name = req.telegram_first_name or "Telegram User"
        if req.telegram_username:
            display_name = req.telegram_username

        return OAuthUserInfo(
            provider="telegram",
            provider_user_id=req.telegram_user_id,
            email=synthetic_email,
            display_name=display_name,
        )

    def set_auth_request(self, request: TelegramAuthRequest) -> None:
        """Inject the TelegramAuthRequest found by the route handler.

        This avoids passing a DB session into the OAuthClient adapter.
        The route handler looks up the request by authorization_code
        and passes it here before calling the use case.
        """
        self._current_request = request
