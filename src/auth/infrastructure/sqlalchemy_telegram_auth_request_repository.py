"""SQLAlchemy ORM-based TelegramAuthRequestRepository (driven adapter).

Uses SQLAlchemy ORM with Imperative Mapping (configured in ``orm.py``).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from auth.domain.telegram_auth_request import TelegramAuthRequest
from auth.infrastructure.orm import telegram_auth_requests_table


class SqlAlchemyTelegramAuthRequestRepository:
    """Implements TelegramAuthRequestRepository Protocol using SQLAlchemy ORM."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_auth_code(self, auth_code: str) -> TelegramAuthRequest | None:
        """Find an auth request by its auth_code (primary key)."""
        return self._session.get(TelegramAuthRequest, auth_code)

    def find_by_authorization_code(
        self, authorization_code: str
    ) -> TelegramAuthRequest | None:
        """Find an auth request by the authorization_code generated after bot callback."""
        stmt = select(TelegramAuthRequest).where(
            telegram_auth_requests_table.c.authorization_code == authorization_code
        )
        return self._session.scalars(stmt).first()

    def save(self, request: TelegramAuthRequest) -> None:
        """Persist a TelegramAuthRequest."""
        self._session.merge(request)
