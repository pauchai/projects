import copy
import uuid
from datetime import datetime, timezone

from community.domain.community import Community
from community.domain.community_role import CommunityRole
from community.domain.community_status import CommunityStatus
from community.domain.invite_code import CommunityInviteCode


class FakeCommunityRepository:
    def __init__(self) -> None:
        self._storage: dict[str, Community] = {}

    def find_by_id(self, community_id: str) -> Community | None:
        return self._storage.get(community_id)

    def save(self, community: Community) -> None:
        self._storage[community.community_id] = community

    def search(
        self,
        owner_id: str | None = None,
        member_user_id: str | None = None,
        status: CommunityStatus | None = None,
        keyword: str | None = None,
    ) -> list[Community]:
        results = list(self._storage.values())
        if owner_id is not None:
            results = [c for c in results if c.owner_id == owner_id]
        if member_user_id is not None:
            results = [
                c
                for c in results
                if any(m.user_id == member_user_id and m.is_active for m in c.memberships)
            ]
        if status is not None:
            results = [c for c in results if c.status == status]
        if keyword is not None:
            pattern = keyword.lower()
            results = [
                c
                for c in results
                if pattern in c.name.lower() or pattern in c.description.lower()
            ]
        return results

    def snapshot(self) -> dict[str, Community]:
        return copy.deepcopy(self._storage)

    def restore(self, snapshot: dict[str, Community]) -> None:
        self._storage = snapshot


class FakeCommunityInviteCodeRepository:
    def __init__(self) -> None:
        self._storage: dict[str, CommunityInviteCode] = {}

    def find_by_code(self, code: str) -> CommunityInviteCode | None:
        for c in self._storage.values():
            if c.code == code.strip().upper():
                return c
        return None

    def find_by_id(self, code_id: str) -> CommunityInviteCode | None:
        return self._storage.get(code_id)

    def find_by_community(self, community_id: str) -> list[CommunityInviteCode]:
        return [c for c in self._storage.values() if c.community_id == community_id]

    def save(self, invite_code: CommunityInviteCode) -> None:
        self._storage[invite_code.code_id] = invite_code

    def delete(self, code_id: str) -> None:
        self._storage.pop(code_id, None)

    def snapshot(self) -> dict[str, CommunityInviteCode]:
        return copy.deepcopy(self._storage)

    def restore(self, snapshot: dict[str, CommunityInviteCode]) -> None:
        self._storage = snapshot


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.communities = FakeCommunityRepository()
        self.invite_codes = FakeCommunityInviteCodeRepository()
        self.committed = False
        self._community_snapshot: dict[str, Community] | None = None
        self._invite_snapshot: dict[str, CommunityInviteCode] | None = None

    def __enter__(self) -> "FakeUnitOfWork":
        self.committed = False
        self._community_snapshot = self.communities.snapshot()
        self._invite_snapshot = self.invite_codes.snapshot()
        return self

    def __exit__(self, *args: object) -> None:
        if not self.committed:
            self.rollback()

    def commit(self) -> None:
        self.committed = True
        self._community_snapshot = None
        self._invite_snapshot = None

    def rollback(self) -> None:
        if self._community_snapshot is not None:
            self.communities.restore(self._community_snapshot)
            self._community_snapshot = None
        if self._invite_snapshot is not None:
            self.invite_codes.restore(self._invite_snapshot)
            self._invite_snapshot = None


def make_community(
    community_id: str | None = None,
    name: str = "Test Community",
    owner_id: str = "owner-1",
) -> Community:
    return Community(
        community_id=community_id or str(uuid.uuid4()),
        name=name,
        description="A test community",
        owner_id=owner_id,
    )


def make_invite_code(
    code: str = "TESTCODE1",
    community_id: str | None = None,
    issued_by: str = "owner-1",
    max_uses: int = 1,
    role: str = "member",
) -> CommunityInviteCode:
    return CommunityInviteCode(
        code_id=str(uuid.uuid4()),
        code=code,
        community_id=community_id or str(uuid.uuid4()),
        issued_by=issued_by,
        max_uses=max_uses,
        role=role,
    )
