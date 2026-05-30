"""ProjectNeed domain entity — a public opening posted by a project.

Design decisions:
- ProjectNeed is a public announcement that a project is looking for people
  with specific skills for a given role.
- Any active project member can create a need (not only the owner).
- Status lifecycle: OPEN → FILLED (when a member joined via this need)
                    OPEN → CLOSED (manually closed by a member)
                    FILLED → CLOSED (need can also be closed after being filled)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum

from project_collaboration.domain.role import ProjectRole


class NeedStatus(str, Enum):
    OPEN = "open"
    FILLED = "filled"
    CLOSED = "closed"


class ProjectNeed:
    """A public opening posted by a project team.

    Attributes:
        need_id:     Unique identity.
        project_id:  The project this need belongs to.
        role:        The role being offered.
        skills:      List of skill tags the ideal candidate should have.
        description: Free-text description of what the person will work on.
        slots:       Number of people needed (default 1).
        status:      Current lifecycle status.
        created_by:  user_id of the member who posted the need.
        created_at:  UTC timestamp.
    """

    def __init__(
        self,
        need_id: str,
        project_id: str,
        role: ProjectRole,
        description: str,
        created_by: str,
        *,
        skills: list[str] | None = None,
        slots: int = 1,
        status: NeedStatus = NeedStatus.OPEN,
        created_at: datetime | None = None,
    ) -> None:
        if not description.strip():
            raise ValueError("description cannot be empty")
        if slots < 1:
            raise ValueError("slots must be at least 1")
        if role == ProjectRole.OWNER:
            raise ValueError("Cannot post a need for the OWNER role")

        self.need_id = need_id
        self.project_id = project_id
        self.role = role
        self.description = description.strip()
        self.created_by = created_by
        self.skills: list[str] = skills or []
        self.slots = slots
        self.status = status
        self.created_at: datetime = created_at or datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Manually close the need — no more applications accepted."""
        if self.status == NeedStatus.CLOSED:
            raise ValueError("ProjectNeed is already closed")
        self.status = NeedStatus.CLOSED

    def mark_filled(self) -> None:
        """Mark the need as filled — all slots have been taken."""
        if self.status != NeedStatus.OPEN:
            raise ValueError(
                f"Cannot mark as filled when status is '{self.status.value}'"
            )
        self.status = NeedStatus.FILLED
