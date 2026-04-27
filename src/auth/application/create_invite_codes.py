"""CreateInviteCodes use case — admin generates a batch of invite codes."""

from __future__ import annotations

import random
import string
import uuid

from auth.domain.invite_code import InviteCode
from auth.domain.ports import UnitOfWork


def _generate_code(length: int = 8) -> str:
    """Generate a random uppercase alphanumeric code (no ambiguous chars)."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # omit 0/O/1/I
    return "".join(random.choices(alphabet, k=length))


class CreateInviteCodesUseCase:
    """Admin use case: generate *count* invite codes.

    Each code is single-use by default (max_uses=1).  Codes are stored
    atomically.  The generated InviteCode objects are returned so the
    caller can display / distribute them.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        admin_user_id: str,
        count: int,
        *,
        max_uses: int = 1,
    ) -> list[InviteCode]:
        """Generate *count* invite codes issued by *admin_user_id*.

        Args:
            admin_user_id: ID of the admin generating the codes.
            count: Number of codes to generate (1–500).
            max_uses: Uses per code (default 1 = single-use).

        Returns:
            List of persisted InviteCode objects.

        Raises:
            ValueError: if count or max_uses are out of range.
        """
        if count < 1 or count > 500:
            raise ValueError("count must be between 1 and 500")
        if max_uses < 1:
            raise ValueError("max_uses must be at least 1")

        with self._uow as uow:
            codes: list[InviteCode] = []
            for _ in range(count):
                invite = InviteCode(
                    code_id=str(uuid.uuid4()),
                    code=_generate_code(),
                    issued_by=admin_user_id,
                    max_uses=max_uses,
                )
                codes.append(invite)
            uow.invite_codes.save_all(codes)
            uow.commit()

        return codes
