"""SQLAlchemy Core-based UserRepository (driven adapter).

Uses SQLAlchemy Core (Table + connection.execute) rather than ORM mapping,
so that auth domain classes stay completely free of infrastructure concerns.
Reconstitution bypasses ``__init__`` via ``object.__new__`` + direct attribute
assignment, avoiding validation re-runs on load.
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from auth.domain.user import Credential, User
from auth.infrastructure.orm import credentials_table, users_table


class SqlAlchemyUserRepository:
    """Implements UserRepository Protocol using SQLAlchemy Core queries."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Public interface (matches UserRepository Protocol)
    # ------------------------------------------------------------------

    def find_by_id(self, user_id: str) -> User | None:
        """Load a full User aggregate by ID, or return None."""
        conn = self._session.connection()

        row = conn.execute(
            select(users_table).where(users_table.c.user_id == user_id)
        ).first()
        if row is None:
            return None

        cred_rows = conn.execute(
            select(credentials_table).where(credentials_table.c.user_id == user_id)
        ).fetchall()

        return self._reconstitute_user(row, cred_rows)

    def find_by_email(self, email: str) -> User | None:
        """Load a full User aggregate by email (normalized), or return None."""
        normalized = email.strip().lower()
        conn = self._session.connection()

        row = conn.execute(
            select(users_table).where(users_table.c.email == normalized)
        ).first()
        if row is None:
            return None

        cred_rows = conn.execute(
            select(credentials_table).where(credentials_table.c.user_id == row.user_id)
        ).fetchall()

        return self._reconstitute_user(row, cred_rows)

    def save(self, user: User) -> None:
        """Upsert a User aggregate (user row + all credentials)."""
        conn = self._session.connection()

        # 1. Upsert user row
        stmt = pg_insert(users_table).values(
            user_id=user.user_id,
            email=user.email,
            display_name=user.display_name,
            is_active=user.is_active,
            created_at=user.created_at,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["user_id"],
            set_={
                "email": stmt.excluded.email,
                "display_name": stmt.excluded.display_name,
                "is_active": stmt.excluded.is_active,
            },
        )
        conn.execute(stmt)

        # 2. Upsert credentials
        # Delete credentials that are no longer on the aggregate, then upsert remaining.
        current_cred_ids = [c.credential_id for c in user.credentials]
        if current_cred_ids:
            conn.execute(
                delete(credentials_table).where(
                    credentials_table.c.user_id == user.user_id,
                    credentials_table.c.credential_id.notin_(current_cred_ids),
                )
            )
        else:
            conn.execute(
                delete(credentials_table).where(
                    credentials_table.c.user_id == user.user_id
                )
            )

        for cred in user.credentials:
            c_stmt = pg_insert(credentials_table).values(
                credential_id=cred.credential_id,
                user_id=cred.user_id,
                provider=cred.provider,
                provider_user_id=cred.provider_user_id,
                hashed_secret=cred.hashed_secret,
                created_at=cred.created_at,
            )
            c_stmt = c_stmt.on_conflict_do_update(
                index_elements=["credential_id"],
                set_={
                    "provider_user_id": c_stmt.excluded.provider_user_id,
                    "hashed_secret": c_stmt.excluded.hashed_secret,
                },
            )
            conn.execute(c_stmt)

    # ------------------------------------------------------------------
    # Private reconstitution helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _reconstitute_user(row: object, cred_rows: list) -> User:
        """Rebuild a User aggregate from raw DB rows, bypassing __init__."""
        user = object.__new__(User)
        user.user_id = row.user_id  # type: ignore[attr-defined]
        user.email = row.email  # type: ignore[attr-defined]
        user.display_name = row.display_name  # type: ignore[attr-defined]
        user.is_active = row.is_active  # type: ignore[attr-defined]
        user.created_at = row.created_at  # type: ignore[attr-defined]
        user.credentials = [
            SqlAlchemyUserRepository._reconstitute_credential(cr) for cr in cred_rows
        ]
        return user

    @staticmethod
    def _reconstitute_credential(row: object) -> Credential:
        """Rebuild a Credential entity from a raw DB row."""
        cred = object.__new__(Credential)
        cred.credential_id = row.credential_id  # type: ignore[attr-defined]
        cred.user_id = row.user_id  # type: ignore[attr-defined]
        cred.provider = row.provider  # type: ignore[attr-defined]
        cred.provider_user_id = row.provider_user_id  # type: ignore[attr-defined]
        cred.hashed_secret = row.hashed_secret  # type: ignore[attr-defined]
        cred.created_at = row.created_at  # type: ignore[attr-defined]
        return cred
