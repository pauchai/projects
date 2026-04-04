"""FastAPI dependency injection for the Auth bounded context.

Provides UnitOfWork, PasswordHasher, and TokenService instances to route handlers.
"""

from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from auth.infrastructure.bcrypt_password_hasher import BcryptPasswordHasher
from auth.infrastructure.database import (
    DEFAULT_DATABASE_URL,
    get_engine,
    get_session_factory,
)
from auth.infrastructure.jwt_token_service import JwtTokenService
from auth.infrastructure.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork

# Module-level singletons, initialized lazily.
_session_factory: sessionmaker[Session] | None = None
_password_hasher: BcryptPasswordHasher | None = None
_token_service: JwtTokenService | None = None

# JWT configuration via env vars with sensible defaults.
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", "60"))


def _get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        engine = get_engine(DEFAULT_DATABASE_URL)
        _session_factory = get_session_factory(engine)
    return _session_factory


def get_auth_uow() -> Generator[SqlAlchemyUnitOfWork, None, None]:
    """FastAPI dependency that yields a SqlAlchemyUnitOfWork for auth.

    Use cases manage the UoW lifecycle themselves (``with uow:``),
    so we just need to construct it with the session factory.
    """
    uow = SqlAlchemyUnitOfWork(_get_session_factory())
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


def override_session_factory(factory: sessionmaker[Session]) -> None:
    """Override the module-level session factory (used in tests)."""
    global _session_factory
    _session_factory = factory
