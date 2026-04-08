"""Telegram auth request — tracks the multi-step bot-based authentication flow.

A TelegramAuthRequest is created when a user initiates "Sign in with Telegram"
and is consumed when the user completes the flow by clicking the auth link
sent by the bot. It bridges the gap between the bot (which receives user data)
and the backend (which issues JWT tokens).

Lifecycle:
1. Created with auth_code + state when user clicks "Sign in with Telegram".
2. Bot receives /start <auth_code>, calls bot-callback endpoint.
3. Bot-callback fills in telegram user data + generates authorization_code.
4. User clicks auth link → frontend sends code + state → backend issues JWT.
5. Record is consumed (marked as used or deleted).
"""

from datetime import datetime, timezone


class TelegramAuthRequest:
    """Temporary record coordinating Telegram bot-based auth flow.

    Not a domain aggregate — this is a coordination entity used by the
    TelegramOAuthClient adapter to bridge the bot ↔ backend interaction.
    """

    def __init__(
        self,
        auth_code: str,
        state: str,
    ) -> None:
        if not auth_code.strip():
            raise ValueError("auth_code cannot be empty")
        if not state.strip():
            raise ValueError("state cannot be empty")

        self.auth_code = auth_code
        self.state = state
        self.authorization_code: str | None = None
        self.telegram_user_id: str | None = None
        self.telegram_username: str | None = None
        self.telegram_first_name: str | None = None
        self.is_used: bool = False
        self.created_at: datetime = datetime.now(timezone.utc)

    def fill_telegram_data(
        self,
        telegram_user_id: str,
        telegram_username: str | None,
        telegram_first_name: str,
        authorization_code: str,
    ) -> None:
        """Fill in data received from the Telegram bot after /start command.

        Raises ValueError if already filled or used.
        """
        if self.is_used:
            raise ValueError("Auth request has already been used")
        if self.authorization_code is not None:
            raise ValueError("Telegram data has already been filled")
        if not telegram_user_id.strip():
            raise ValueError("telegram_user_id cannot be empty")
        if not telegram_first_name.strip():
            raise ValueError("telegram_first_name cannot be empty")
        if not authorization_code.strip():
            raise ValueError("authorization_code cannot be empty")

        self.telegram_user_id = telegram_user_id
        self.telegram_username = telegram_username
        self.telegram_first_name = telegram_first_name
        self.authorization_code = authorization_code

    def consume(self) -> None:
        """Mark this request as used. Prevents reuse of the same auth code.

        Raises ValueError if not ready (no telegram data) or already used.
        """
        if self.is_used:
            raise ValueError("Auth request has already been used")
        if self.authorization_code is None:
            raise ValueError("Auth request has not been completed by the bot yet")
        self.is_used = True

    @property
    def is_ready(self) -> bool:
        """Whether the bot has filled in the telegram data and auth code."""
        return self.authorization_code is not None and not self.is_used
