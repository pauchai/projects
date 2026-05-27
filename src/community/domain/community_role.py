from enum import Enum


class CommunityRole(Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MODERATOR = "moderator"
    MEMBER = "member"

    def can_manage_members(self) -> bool:
        return self in {CommunityRole.OWNER, CommunityRole.ADMIN}

    def can_manage_settings(self) -> bool:
        return self in {CommunityRole.OWNER, CommunityRole.ADMIN}

    def can_manage_projects(self) -> bool:
        return self in {CommunityRole.OWNER, CommunityRole.ADMIN, CommunityRole.MODERATOR}
