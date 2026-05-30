import pytest

from community.application.create_community_invite_code import (
    CreateCommunityInviteCodeUseCase,
)
from community.domain.community_role import CommunityRole
from tests.community.fakes.fake_unit_of_work import (
    FakeUnitOfWork,
    make_community,
)


class TestCreateCommunityInviteCodeUseCase:
    def test_owner_can_create_code(self) -> None:
        uow = FakeUnitOfWork()
        community = make_community(owner_id="owner-1")
        uow.communities.save(community)
        use_case = CreateCommunityInviteCodeUseCase(uow)

        code = use_case.execute(
            community_id=community.community_id,
            caller_id="owner-1",
            max_uses=5,
            expires_in_days=14,
            role="moderator",
        )

        assert code.community_id == community.community_id
        assert code.issued_by == "owner-1"
        assert code.max_uses == 5
        assert code.role == "moderator"
        assert code.is_active is True
        assert code.uses_left == 5
        assert code.code_id is not None
        assert len(code.code) == 8

    def test_admin_can_create_code(self) -> None:
        uow = FakeUnitOfWork()
        community = make_community(owner_id="owner-1")
        community.add_member(
            membership_id="m1", user_id="admin-1", role=CommunityRole.ADMIN
        )
        uow.communities.save(community)
        use_case = CreateCommunityInviteCodeUseCase(uow)

        code = use_case.execute(
            community_id=community.community_id,
            caller_id="admin-1",
        )
        assert code is not None

    def test_raises_when_community_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateCommunityInviteCodeUseCase(uow)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute(
                community_id="nonexistent",
                caller_id="user-1",
            )

    def test_raises_permission_error_for_non_owner_admin(self) -> None:
        uow = FakeUnitOfWork()
        community = make_community(owner_id="owner-1")
        community.add_member(
            membership_id="m1", user_id="member-1", role=CommunityRole.MEMBER
        )
        uow.communities.save(community)
        use_case = CreateCommunityInviteCodeUseCase(uow)

        with pytest.raises(PermissionError, match="Only owner or admin"):
            use_case.execute(
                community_id=community.community_id,
                caller_id="member-1",
            )

    def test_raises_permission_error_for_non_member(self) -> None:
        uow = FakeUnitOfWork()
        community = make_community(owner_id="owner-1")
        uow.communities.save(community)
        use_case = CreateCommunityInviteCodeUseCase(uow)

        with pytest.raises(PermissionError, match="Only owner or admin"):
            use_case.execute(
                community_id=community.community_id,
                caller_id="stranger",
            )

    def test_saves_and_commits(self) -> None:
        uow = FakeUnitOfWork()
        community = make_community(owner_id="owner-1")
        uow.communities.save(community)
        use_case = CreateCommunityInviteCodeUseCase(uow)

        use_case.execute(
            community_id=community.community_id,
            caller_id="owner-1",
        )

        assert uow.committed is True
        codes = uow.invite_codes.find_by_community(community.community_id)
        assert len(codes) == 1

    def test_defaults(self) -> None:
        uow = FakeUnitOfWork()
        community = make_community(owner_id="owner-1")
        uow.communities.save(community)
        use_case = CreateCommunityInviteCodeUseCase(uow)

        code = use_case.execute(
            community_id=community.community_id,
            caller_id="owner-1",
        )

        assert code.max_uses == 1
        assert code.role == "member"
        assert code.uses_left == 1
