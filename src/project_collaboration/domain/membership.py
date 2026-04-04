"""Membership entity — relationship between a user and a project."""

from datetime import datetime, timezone

from project_collaboration.domain.role import ProjectRole


class Membership:
    """A user's participation in a project with a specific role."""

    def __init__(
        self,
        membership_id: str,
        user_id: str,
        project_id: str,
        role: ProjectRole,
    ) -> None:
        self.membership_id = membership_id
        self.user_id = user_id
        self.project_id = project_id
        self.role = role
        self.is_active: bool = True
        self.joined_at: datetime = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        """Mark membership as inactive. Raises if already inactive."""
        if not self.is_active:
            raise ValueError("Membership is already inactive")
        self.is_active = False

    def change_role(self, new_role: ProjectRole) -> None:
        """Change the member's role. Cannot assign Owner or change on inactive membership."""
        if not self.is_active:
            raise ValueError("Cannot change role on inactive membership")
        if new_role == ProjectRole.OWNER:
            raise ValueError("Cannot assign Owner role via change_role")
        self.role = new_role
