"""SQLAlchemy ORM-based UserRepository (driven adapter).

Uses SQLAlchemy ORM with Imperative Mapping (configured in ``orm.py``).
Domain classes are loaded/saved as mapped objects; the ORM handles
``__new__`` + attribute population on load, bypassing ``__init__``.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from auth.domain.user import User
from auth.infrastructure.orm import users_table


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

    def save(self, user: User) -> None:
        """Persist a User aggregate (user + credentials handled by ORM cascade)."""
        self._session.merge(user)
