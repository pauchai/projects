"""SQLAlchemy ORM-based UserRepository (driven adapter).

Uses SQLAlchemy ORM with Imperative Mapping (configured in ``orm.py``).
Domain classes are loaded/saved as mapped objects; the ORM handles
``__new__`` + attribute population on load, bypassing ``__init__``.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from auth.domain.user import Credential, User
from auth.infrastructure.orm import credentials_table, users_table


class SqlAlchemyUserRepository:
    """Implements UserRepository Protocol using SQLAlchemy ORM."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Public interface (matches UserRepository Protocol)
    # ------------------------------------------------------------------

    def find_by_id(self, user_id: str) -> User | None:
        """Load a full User aggregate by ID, or return None."""
        return self._session.get(
            User,
            user_id,
            options=[
                selectinload(User.credentials),  # type: ignore[attr-defined]
            ],
        )

    def find_by_email(self, email: str) -> User | None:
        """Load a full User aggregate by email (normalized), or return None."""
        normalized = email.strip().lower()
        stmt = (
            select(User)
            .where(users_table.c.email == normalized)
            .options(
                selectinload(User.credentials),  # type: ignore[attr-defined]
            )
        )
        return self._session.scalars(stmt).first()

    def find_by_oauth_provider_user_id(
        self, provider: str, provider_user_id: str
    ) -> User | None:
        """Find the user who owns a credential with the given provider + external ID."""
        stmt = (
            select(User)
            .join(Credential, users_table.c.user_id == credentials_table.c.user_id)
            .where(
                credentials_table.c.provider == provider,
                credentials_table.c.provider_user_id == provider_user_id,
            )
            .options(
                selectinload(User.credentials),  # type: ignore[attr-defined]
            )
        )
        return self._session.scalars(stmt).first()

    def save(self, user: User) -> None:
        """Persist a User aggregate (user + credentials handled by ORM cascade)."""
        self._session.merge(user)
