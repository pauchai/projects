"""FastAPI dependency injection for the Auth bounded context.

Provides UnitOfWork, PasswordHasher, TokenService, TelegramAuthRequestRepository,
and auth guard instances to route handlers.
"""

from __future__ import annotations

import os
from collections.abc import Generator
from typing import Optional

from fastapi import Depends, Header
from sqlalchemy.orm import Session, sessionmaker

from auth.infrastructure.bcrypt_password_hasher import BcryptPasswordHasher
from auth.infrastructure.database import (
    DEFAULT_DATABASE_URL,
    get_engine,
    get_session_factory,
)
from auth.infrastructure.jwt_token_service import JwtTokenService
from auth.infrastructure.providers.google_oauth_client import GoogleOAuthClient
from auth.infrastructure.providers.telegram_oauth_client import TelegramOAuthClient
from auth.infrastructure.redis_client import get_redis_client
from auth.infrastructure.redis_telegram_auth_request_repository import (
    RedisTelegramAuthRequestRepository,
)
from auth.infrastructure.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork
from shared_kernel.events import EventBus

# Module-level singletons, initialized lazily.
_session_factory: sessionmaker[Session] | None = None
_password_hasher: BcryptPasswordHasher | None = None
_token_service: JwtTokenService | None = None
_event_bus: EventBus | None = None
_google_oauth_client: GoogleOAuthClient | None = None
_telegram_oauth_client: TelegramOAuthClient | None = None
_telegram_auth_repo: RedisTelegramAuthRequestRepository | None = None

# JWT configuration via env vars with sensible defaults.
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", "60"))

# Google OAuth configuration via env vars (all optional — graceful degradation).
OAUTH_GOOGLE_CLIENT_ID = os.environ.get("OAUTH_GOOGLE_CLIENT_ID", "")
OAUTH_GOOGLE_CLIENT_SECRET = os.environ.get("OAUTH_GOOGLE_CLIENT_SECRET", "")
OAUTH_GOOGLE_REDIRECT_URI = os.environ.get("OAUTH_GOOGLE_REDIRECT_URI", "")

# Telegram OAuth configuration via env vars (all optional — graceful degradation).
OAUTH_TELEGRAM_BOT_TOKEN = os.environ.get("OAUTH_TELEGRAM_BOT_TOKEN", "")
OAUTH_TELEGRAM_BOT_USERNAME = os.environ.get("OAUTH_TELEGRAM_BOT_USERNAME", "")


class AuthenticationError(Exception):
    """Raised when JWT authentication fails (missing, malformed, or invalid token)."""


def _get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = get_session_factory(engine)
    return _session_factory


def get_auth_uow() -> Generator[SqlAlchemyUnitOfWork, None, None]:
    """FastAPI dependency that yields a SqlAlchemyUnitOfWork for auth.

    Use cases manage the UoW lifecycle themselves (``with uow:``),
    so we just need to construct it with the session factory and event bus.
    """
    uow = SqlAlchemyUnitOfWork(_get_session_factory(), event_bus=_event_bus)
    yield uow


def get_password_hasher() -> BcryptPasswordHasher:
    """FastAPI dependency: returns a singleton BcryptPasswordHasher."""
    global _password_hasher
    if _password_hasher is None:
        _password_hasher = BcryptPasswordHasher()
    return _password_hasher


def get_token_service() -> JwtTokenService:
    """FastAPI dependency: returns a singleton JwtTokenService."""
    global _token_service
    if _token_service is None:
        _token_service = JwtTokenService(
            secret=JWT_SECRET,
            algorithm=JWT_ALGORITHM,
            expire_minutes=JWT_EXPIRE_MINUTES,
        )
    return _token_service


def _extract_user_id(
    authorization: str | None,
    token_service: JwtTokenService,
) -> str:
    """Pure logic: extract user_id from a JWT Bearer token.

    Args:
        authorization: The value of the Authorization header.
        token_service: A TokenService instance for decoding the token.

    Returns:
        The user_id extracted from the token.

    Raises:
        AuthenticationError: If the header is missing, malformed, or the token
            is invalid/expired.
    """
    if authorization is None:
        raise AuthenticationError("Missing Authorization header")

    parts = authorization.split(" ", maxsplit=1)
    if len(parts) != 2 or parts[0] != "Bearer":
        raise AuthenticationError("Authorization header must use Bearer scheme")

    token = parts[1].strip()
    if not token:
        raise AuthenticationError("Missing token in Authorization header")

    try:
        return token_service.decode_token(token)
    except ValueError as exc:
        raise AuthenticationError(f"Invalid token: {exc}") from exc


def get_current_user_id(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    token_service: JwtTokenService = Depends(get_token_service),
) -> str:
    """FastAPI dependency: extracts user_id from JWT Bearer token.

    Uses the Authorization header and the TokenService.
    Raises AuthenticationError on failure (mapped to 401 by the exception handler).
    """
    return _extract_user_id(authorization, token_service)


def override_session_factory(factory: sessionmaker[Session]) -> None:
    """Override the module-level session factory (used in tests)."""
    global _session_factory
    _session_factory = factory


def set_event_bus(bus: EventBus | None) -> None:
    """Set the module-level event bus.

    Called once at application startup to wire up domain event handlers.
    Pass ``None`` to disable event publishing.
    """
    global _event_bus
    _event_bus = bus


def get_google_oauth_client() -> GoogleOAuthClient | None:
    """FastAPI dependency: returns a GoogleOAuthClient if configured, else None.

    Google OAuth is optional (graceful degradation). If the env vars
    ``OAUTH_GOOGLE_CLIENT_ID``, ``OAUTH_GOOGLE_CLIENT_SECRET``, and
    ``OAUTH_GOOGLE_REDIRECT_URI`` are not all set, returns ``None`` and
    the OAuth endpoints will respond with appropriate error/unavailable
    responses.
    """
    global _google_oauth_client
    if not all(
        [OAUTH_GOOGLE_CLIENT_ID, OAUTH_GOOGLE_CLIENT_SECRET, OAUTH_GOOGLE_REDIRECT_URI]
    ):
        return None
    if _google_oauth_client is None:
        _google_oauth_client = GoogleOAuthClient(
            client_id=OAUTH_GOOGLE_CLIENT_ID,
            client_secret=OAUTH_GOOGLE_CLIENT_SECRET,
            redirect_uri=OAUTH_GOOGLE_REDIRECT_URI,
        )
    return _google_oauth_client


def get_telegram_oauth_client() -> TelegramOAuthClient | None:
    """FastAPI dependency: returns a TelegramOAuthClient if configured, else None.

    Telegram OAuth is optional (graceful degradation). If the env vars
    ``OAUTH_TELEGRAM_BOT_TOKEN`` and ``OAUTH_TELEGRAM_BOT_USERNAME`` are
    not both set, returns ``None``.
    """
    global _telegram_oauth_client
    if not all([OAUTH_TELEGRAM_BOT_TOKEN, OAUTH_TELEGRAM_BOT_USERNAME]):
        return None
    if _telegram_oauth_client is None:
        _telegram_oauth_client = TelegramOAuthClient(
            bot_username=OAUTH_TELEGRAM_BOT_USERNAME,
        )
    return _telegram_oauth_client


def get_telegram_auth_repo() -> RedisTelegramAuthRequestRepository:
    """FastAPI dependency: returns a singleton RedisTelegramAuthRequestRepository.

    Uses Redis for storing temporary Telegram auth requests with automatic
    TTL-based expiration (5 minutes).  This replaces the old SQLAlchemy-based
    repository that caused unbounded record accumulation in PostgreSQL.
    """
    global _telegram_auth_repo
    if _telegram_auth_repo is None:
        redis_client = get_redis_client()
        _telegram_auth_repo = RedisTelegramAuthRequestRepository(redis_client)
    return _telegram_auth_repo
