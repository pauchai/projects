"""SQLAlchemy repository for InviteCode (driven adapter)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from auth.domain.invite_code import InviteCode
from auth.infrastructure.orm import invite_codes_table


class SqlAlchemyInviteCodeRepository:
    """Implements InviteCodeRepository Protocol using SQLAlchemy ORM."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_code(self, code: str) -> InviteCode | None:
        """Find an invite code by its normalized uppercase code string."""
        normalized = code.strip().upper()
        stmt = select(InviteCode).where(invite_codes_table.c.code == normalized)
        return self._session.scalars(stmt).first()

    def save(self, invite_code: InviteCode) -> None:
        """Persist a single InviteCode."""
        self._session.merge(invite_code)

    def save_all(self, invite_codes: list[InviteCode]) -> None:
        """Persist a batch of InviteCodes."""
        for invite_code in invite_codes:
            self._session.merge(invite_code)
