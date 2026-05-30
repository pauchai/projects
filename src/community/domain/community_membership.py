from datetime import datetime, timezone

from community.domain.community_role import CommunityRole


class CommunityMembership:
    def __init__(
        self,
        membership_id: str,
        community_id: str,
        user_id: str,
        role: CommunityRole,
        weight: float = 0.0,
    ) -> None:
        self.membership_id = membership_id
        self.community_id = community_id
        self.user_id = user_id
        self.role = role
        self.weight = weight
        self.is_active: bool = True
        self.joined_at: datetime = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        if not self.is_active:
            raise ValueError("Membership is already inactive")
        self.is_active = False

    def change_role(self, new_role: CommunityRole) -> None:
        if not self.is_active:
            raise ValueError("Cannot change role on inactive membership")
        if new_role == CommunityRole.OWNER:
            raise ValueError("Cannot assign Owner role via change_role")
        self.role = new_role
