from community.domain.community import Community
from community.domain.community_role import CommunityRole
from community.domain.ports import CommunityUnitOfWork


def get_community_or_raise(uow: CommunityUnitOfWork, community_id: str) -> Community:
    community = uow.communities.find_by_id(community_id)
    if community is None:
        raise LookupError(f"Community {community_id} not found")
    return community


def require_community_role(
    community: Community, caller_id: str, *required_roles: CommunityRole
) -> None:
    membership = community._find_active_membership(caller_id)
    if membership is None:
        raise PermissionError("Caller is not a member of this community")
    if membership.role not in required_roles:
        raise PermissionError(
            f"Caller needs one of {[r.value for r in required_roles]} roles"
        )
