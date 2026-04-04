"""FastAPI dependency injection: provides UnitOfWork and auth dependencies.

Provides:
- ``get_uow``: yields a SqlAlchemyUnitOfWork for project collaboration.
- ``get_current_user_id``: extracts user_id from JWT Bearer token.
- ``AuthenticationError``: raised when authentication fails (mapped to 401).
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Optional

from fastapi import Depends, Header
from sqlalchemy.orm import Session, sessionmaker

from auth.api.dependencies import get_token_service
from auth.domain.ports import TokenService
from project_collaboration.infrastructure.database import (
    DEFAULT_DATABASE_URL,
    get_engine,
    get_session_factory,
)
from project_collaboration.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork,
)

# Module-level singletons, initialized lazily.
_session_factory: sessionmaker[Session] | None = None


class AuthenticationError(Exception):
    """Raised when JWT authentication fails (missing, malformed, or invalid token)."""


def _get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        engine = get_engine(DEFAULT_DATABASE_URL)
        _session_factory = get_session_factory(engine)
    return _session_factory


def get_uow() -> Generator[SqlAlchemyUnitOfWork, None, None]:
    """FastAPI dependency that yields a SqlAlchemyUnitOfWork.

    Use cases manage the UoW lifecycle themselves (``with uow:``),
    so we just need to construct it with the session factory.
    """
    uow = SqlAlchemyUnitOfWork(_get_session_factory())
    yield uow


def _extract_user_id(
    authorization: str | None,
    token_service: TokenService,
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
    token_service: TokenService = Depends(get_token_service),
) -> str:
    """FastAPI dependency: extracts user_id from JWT Bearer token.

    Uses the Authorization header and the shared TokenService from auth context.
    Raises AuthenticationError on failure (mapped to 401 by the exception handler).
    """
    return _extract_user_id(authorization, token_service)


def override_session_factory(factory: sessionmaker[Session]) -> None:
    """Override the module-level session factory (used in tests)."""
    global _session_factory
    _session_factory = factory
