from enum import Enum


class CommunityStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"

    def can_transition_to(self, target: "CommunityStatus") -> bool:
        if self == target:
            return False
        return target in _ALLOWED_TRANSITIONS.get(self, set())


_ALLOWED_TRANSITIONS: dict[CommunityStatus, set[CommunityStatus]] = {
    CommunityStatus.ACTIVE: {CommunityStatus.SUSPENDED, CommunityStatus.ARCHIVED},
    CommunityStatus.SUSPENDED: {CommunityStatus.ACTIVE, CommunityStatus.ARCHIVED},
}
