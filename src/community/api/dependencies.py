from collections.abc import Generator
from typing import Optional

from fastapi import Depends, Header
from sqlalchemy.orm import Session, sessionmaker

from auth.api.dependencies import get_token_service
from auth.domain.ports import TokenService
from community.infrastructure.database import get_engine, get_session_factory
from community.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyCommunityUnitOfWork,
)
from project_collaboration.api.dependencies import AuthenticationError
from shared_kernel.events import EventBus

_session_factory: sessionmaker[Session] | None = None
_event_bus: EventBus | None = None


def _get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = get_session_factory(engine)
    return _session_factory


def get_uow() -> Generator[SqlAlchemyCommunityUnitOfWork, None, None]:
    uow = SqlAlchemyCommunityUnitOfWork(_get_session_factory(), event_bus=_event_bus)
    yield uow


def get_current_user_id(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    token_service: TokenService = Depends(get_token_service),
) -> str:
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


def override_session_factory(factory: sessionmaker[Session]) -> None:
    global _session_factory
    _session_factory = factory


def set_event_bus(bus: EventBus | None) -> None:
    global _event_bus
    _event_bus = bus
