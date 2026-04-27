"""InviteCode domain entity for the invite-only registration system.

Design decisions:
- InviteCode is an entity (has identity, mutable state).
- ``issued_by`` references the admin user_id that created the code.
- ``inviter_id`` optionally references the regular user who "owns" this code
  (i.e., who referred the new user). For admin-issued seed codes it is None.
- Single-use: max_uses defaults to 1 to couple well with onboarding flow.
- ``redeem()`` enforces all business rules: expiry, exhaustion, activation.
"""

from __future__ import annotations

from datetime import datetime, timezone


class InviteCode:
    """An invite code that grants access to closed registration.

    Lifecycle:
        issued (uses_left > 0, not expired) → redeemed (uses_left == 0)
    """

    def __init__(
        self,
        code_id: str,
        code: str,
        issued_by: str,
        *,
        max_uses: int = 1,
        inviter_id: str | None = None,
        expires_at: datetime | None = None,
    ) -> None:
        if not code.strip():
            raise ValueError("Code cannot be empty")
        if max_uses < 1:
            raise ValueError("max_uses must be at least 1")

        self.code_id = code_id
        self.code = code.strip().upper()
        self.issued_by = issued_by
        self.inviter_id = inviter_id
        self.max_uses = max_uses
        self.uses_left = max_uses
        self.is_active: bool = True
        self.created_at: datetime = datetime.now(timezone.utc)
        self.expires_at: datetime | None = expires_at

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def is_valid(self, now: datetime | None = None) -> bool:
        """Return True if the code can still be used."""
        if not self.is_active:
            return False
        if self.uses_left <= 0:
            return False
        if self.expires_at is not None:
            _now = now or datetime.now(timezone.utc)
            if _now > self.expires_at:
                return False
        return True

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def redeem(self, now: datetime | None = None) -> None:
        """Mark one use of the code.

        Raises:
            ValueError: if the code is inactive, exhausted, or expired.
        """
        if not self.is_active:
            raise ValueError("Invite code is no longer active")
        if self.uses_left <= 0:
            raise ValueError("Invite code has already been fully used")
        if self.expires_at is not None:
            _now = now or datetime.now(timezone.utc)
            if _now > self.expires_at:
                raise ValueError("Invite code has expired")

        self.uses_left -= 1

    def deactivate(self) -> None:
        """Admin deactivation — prevents any further use."""
        if not self.is_active:
            raise ValueError("Invite code is already inactive")
        self.is_active = False
