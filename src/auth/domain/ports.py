"""Driven ports (Protocols) for the Auth bounded context.

These interfaces are defined by the domain layer and implemented by infrastructure.
Domain never depends on infrastructure — only on these abstractions (DIP).
"""

from typing import Protocol

from auth.domain.oauth import OAuthUserInfo
from auth.domain.telegram_auth_request import TelegramAuthRequest
from auth.domain.user import User


class PasswordHasher(Protocol):
    """Port for password hashing and verification."""

    def hash(self, plain_password: str) -> str: ...

    def verify(self, plain_password: str, hashed_password: str) -> bool: ...


class TokenService(Protocol):
    """Port for creating and decoding authentication tokens (e.g., JWT)."""

    def create_access_token(self, user_id: str) -> str: ...

    def decode_token(self, token: str) -> str:
        """Decode a token and return the user_id. Raises ValueError if invalid."""
        ...


class OAuthClient(Protocol):
    """Port for communicating with an OAuth provider.

    The domain defines *what* data it needs; infrastructure implements
    *how* to get it from a specific provider (Google, GitHub, etc.).

    The flow:
    1. ``build_authorization_url`` — generate the URL to redirect the user to.
    2. ``exchange_code`` — exchange the authorization code for an access token.
    3. ``get_user_info`` — fetch user profile data using the access token.
    """

    def build_authorization_url(self, state: str) -> str:
        """Return the provider's authorization URL with the given state parameter."""
        ...

    def exchange_code(self, code: str) -> str:
        """Exchange an authorization code for an access token.

        Raises ``OAuthError`` on failure (network, invalid code, etc.).
        """
        ...

    def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Fetch user profile from the provider using the access token.

        Raises ``OAuthError`` on failure.
        """
        ...


class UserRepository(Protocol):
    """Port for persisting and querying Users in the Auth context."""

    def find_by_id(self, user_id: str) -> User | None: ...

    def find_by_email(self, email: str) -> User | None: ...

    def save(self, user: User) -> None: ...


class TelegramAuthRequestRepository(Protocol):
    """Port for persisting and querying TelegramAuthRequests."""

    def find_by_auth_code(self, auth_code: str) -> TelegramAuthRequest | None: ...

    def find_by_authorization_code(
        self, authorization_code: str
    ) -> TelegramAuthRequest | None: ...

    def save(self, request: TelegramAuthRequest) -> None: ...


class UnitOfWork(Protocol):
    """Driven port: coordinates atomic persistence for the Auth context.

    Application Services manage the UoW lifecycle (enter, commit/rollback, exit).
    The domain layer defines this contract; infrastructure provides the real
    implementation. Tests use a FakeUnitOfWork.

    Usage::

        with uow:
            user = uow.users.find_by_email("alice@example.com")
            user.add_credential(credential)
            uow.users.save(user)
            uow.commit()
    """

    users: UserRepository
    telegram_auth_requests: TelegramAuthRequestRepository

    def __enter__(self) -> "UnitOfWork": ...
    def __exit__(self, *args: object) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
