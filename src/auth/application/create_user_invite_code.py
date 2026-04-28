"""CreateUserInviteCode use case — regular user generates a personal invite code."""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone

from auth.domain.invite_code import InviteCode
from auth.domain.ports import UnitOfWork

_DEFAULT_MAX_USES = 1
_DEFAULT_EXPIRES_DAYS = 7


def _generate_code(length: int = 8) -> str:
    """Generate a random uppercase alphanumeric code (no ambiguous chars)."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # omit 0/O/1/I
    return "".join(random.choices(alphabet, k=length))


class CreateUserInviteCodeUseCase:
    """Any authenticated user generates a personal invite code.

    The created code:
    - has ``issued_by`` and ``inviter_id`` both set to the requesting user_id
      so that when someone registers with it, the referral graph is populated.
    - expires in ``expires_days`` days (default 7).
    - is single-use by default (``max_uses=1``).
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        user_id: str,
        *,
        max_uses: int = _DEFAULT_MAX_USES,
        expires_days: int = _DEFAULT_EXPIRES_DAYS,
    ) -> InviteCode:
        """Generate one invite code owned by *user_id*.

        Args:
            user_id: ID of the authenticated user creating the code.
            max_uses: Uses per code (default 1).
            expires_days: Days until expiry (default 7).

        Returns:
            The persisted InviteCode.

        Raises:
            ValueError: if user_id is empty, max_uses < 1, or expires_days < 1.
        """
        if not user_id or not user_id.strip():
            raise ValueError("user_id cannot be empty")
        if max_uses < 1:
            raise ValueError("max_uses must be at least 1")
        if expires_days < 1:
            raise ValueError("expires_days must be at least 1")

        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)

        with self._uow as uow:
            invite = InviteCode(
                code_id=str(uuid.uuid4()),
                code=_generate_code(),
                issued_by=user_id,
                inviter_id=user_id,
                max_uses=max_uses,
                expires_at=expires_at,
            )
            uow.invite_codes.save(invite)
            uow.commit()

        return invite
