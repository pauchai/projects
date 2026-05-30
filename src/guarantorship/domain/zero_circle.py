"""ZeroCircle aggregate — a mutual-guarantee DAO circle for users without guarantors.

When no guarantors with deposits are available, participants can form a
ZeroCircle: a group that collectively commits to future mutual guarantorship.
The circle will eventually be anchored to a DAO contract on-chain.

Business rules:
- One user can be an active member of at most one ZeroCircle.
- The initiator is automatically added as the first member.
- A user cannot join if already a member of any open circle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum


class ZeroCircleStatus(str, Enum):
    OPEN = "open"               # accepting new members
    DAO_PENDING = "dao_pending" # circle formed, awaiting DAO contract
    CLOSED = "closed"           # disbanded


@dataclass(frozen=True)
class ZeroCircleMember:
    circle_id: str
    user_id: str
    joined_at: datetime


class ZeroCircle:
    """A mutual-guarantee circle of users without existing guarantors.

    Attributes:
        circle_id:     Unique identifier.
        name:          Human-readable name for the circle.
        initiated_by:  User ID of the creator.
        status:        Current lifecycle status.
        deposit_stub:  Placeholder deposit amount (no real money yet).
        created_at:    Creation timestamp.
        members:       Current list of ZeroCircleMember value objects.
    """

    def __init__(
        self,
        circle_id: str,
        name: str,
        initiated_by: str,
        *,
        status: ZeroCircleStatus = ZeroCircleStatus.OPEN,
        deposit_stub: Decimal | None = None,
        created_at: datetime | None = None,
        members: list[ZeroCircleMember] | None = None,
    ) -> None:
        if not name.strip():
            raise ValueError("Circle name cannot be empty")
        self.circle_id = circle_id
        self.name = name.strip()
        self.initiated_by = initiated_by
        self.status = status
        self.deposit_stub = deposit_stub
        self.created_at = created_at or datetime.now(timezone.utc)
        self.members: list[ZeroCircleMember] = members or []

        # Auto-add initiator as first member if not already present
        if not any(m.user_id == initiated_by for m in self.members):
            self.members.append(
                ZeroCircleMember(
                    circle_id=circle_id,
                    user_id=initiated_by,
                    joined_at=self.created_at,
                )
            )

    def add_member(self, user_id: str) -> None:
        """Add a user to the circle.

        Raises:
            ValueError: If circle is not open or user is already a member.
        """
        if self.status != ZeroCircleStatus.OPEN:
            raise ValueError("Cannot join a circle that is not open")
        if any(m.user_id == user_id for m in self.members):
            raise ValueError("User is already a member of this circle")
        self.members.append(
            ZeroCircleMember(
                circle_id=self.circle_id,
                user_id=user_id,
                joined_at=datetime.now(timezone.utc),
            )
        )

    def member_ids(self) -> list[str]:
        """Return list of member user IDs."""
        return [m.user_id for m in self.members]
