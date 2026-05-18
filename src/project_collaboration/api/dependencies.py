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
    get_engine,
    get_session_factory,
)
from project_collaboration.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from shared_kernel.events import EventBus

# Module-level singletons, initialized lazily.
_session_factory: sessionmaker[Session] | None = None
_event_bus: EventBus | None = None


class AuthenticationError(Exception):
    """Raised when JWT authentication fails (missing, malformed, or invalid token)."""


def _get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = get_session_factory(engine)
    return _session_factory


def get_uow() -> Generator[SqlAlchemyUnitOfWork, None, None]:
    """FastAPI dependency that yields a SqlAlchemyUnitOfWork.

    Use cases manage the UoW lifecycle themselves (``with uow:``),
    so we just need to construct it with the session factory and event bus.
    """
    uow = SqlAlchemyUnitOfWork(_get_session_factory(), event_bus=_event_bus)
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


import os

SERVICE_TOKEN = os.environ.get("MCP_SERVICE_TOKEN", "")


def get_service_user_id(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_user_id: str = Header(..., alias="X-User-ID"),
) -> str:
    """FastAPI dependency: validates service token and returns impersonated user_id.

    The caller must supply:
    - Authorization: Bearer <MCP_SERVICE_TOKEN>
    - X-User-ID: <target_user_id>

    Returns the target user_id from X-User-ID.

    Raises AuthenticationError if the service token is missing or wrong.
    """
    if not SERVICE_TOKEN:
        raise AuthenticationError("MCP service not configured (MCP_SERVICE_TOKEN not set)")

    if authorization is None:
        raise AuthenticationError("Missing Authorization header")

    parts = authorization.split(" ", maxsplit=1)
    if len(parts) != 2 or parts[0] != "Bearer":
        raise AuthenticationError("Authorization header must use Bearer scheme")

    token = parts[1].strip()
    if token != SERVICE_TOKEN:
        raise AuthenticationError("Invalid service token")

    if not x_user_id:
        raise AuthenticationError("Missing X-User-ID header")

    return x_user_id


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


def set_event_bus(bus: EventBus | None) -> None:
    """Set the module-level event bus.

    Called once at application startup to wire up domain event handlers.
    Pass ``None`` to disable event publishing.
    """
    global _event_bus
    _event_bus = bus
