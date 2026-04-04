"""Project role with privilege hierarchy."""

from enum import Enum


class ProjectRole(Enum):
    """Role of a participant within a project, ordered by privilege."""

    OWNER = "owner"
    ADMIN = "admin"
    MENTOR = "mentor"
    MEMBER = "member"
    OBSERVER = "observer"

    def has_management_rights(self) -> bool:
        """Return True if this role can manage members and review applications."""
        return self in {ProjectRole.OWNER, ProjectRole.ADMIN}
