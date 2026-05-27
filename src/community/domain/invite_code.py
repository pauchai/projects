from __future__ import annotations

from datetime import datetime, timezone


class CommunityInviteCode:
    def __init__(
        self,
        code_id: str,
        code: str,
        community_id: str,
        issued_by: str,
        *,
        max_uses: int = 1,
        expires_at: datetime | None = None,
        role: str = "member",
    ) -> None:
        if not code.strip():
            raise ValueError("Code cannot be empty")
        if max_uses < 1:
            raise ValueError("max_uses must be at least 1")
        if not community_id:
            raise ValueError("community_id is required")

        self.code_id = code_id
        self.code = code.strip().upper()
        self.community_id = community_id
        self.issued_by = issued_by
        self.max_uses = max_uses
        self.uses_left = max_uses
        self.is_active: bool = True
        self.created_at: datetime = datetime.now(timezone.utc)
        self.expires_at: datetime | None = expires_at
        self.role: str = role

    def is_valid(self, now: datetime | None = None) -> bool:
        if not self.is_active:
            return False
        if self.uses_left <= 0:
            return False
        if self.expires_at is not None:
            _now = now or datetime.now(timezone.utc)
            if _now > self.expires_at:
                return False
        return True

    def redeem(self) -> None:
        if not self.is_active:
            raise ValueError("Invite code is no longer active")
        if self.uses_left <= 0:
            raise ValueError("Invite code has already been fully used")
        if self.expires_at is not None:
            if datetime.now(timezone.utc) > self.expires_at:
                raise ValueError("Invite code has expired")
        self.uses_left -= 1

    def deactivate(self) -> None:
        if not self.is_active:
            raise ValueError("Invite code is already inactive")
        self.is_active = False
