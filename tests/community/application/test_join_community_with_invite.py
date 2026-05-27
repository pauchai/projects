import pytest

from community.application.join_community_with_invite import (
    JoinCommunityWithInviteUseCase,
)
from community.domain.community_role import CommunityRole
from tests.community.fakes.fake_unit_of_work import (
    FakeUnitOfWork,
    make_community,
    make_invite_code,
)


class TestJoinCommunityWithInviteUseCase:
    def test_joins_community_with_valid_code(self) -> None:
        uow = FakeUnitOfWork()
        community = make_community(owner_id="owner-1")
        uow.communities.save(community)
        invite = make_invite_code(
            code="JOINME1", community_id=community.community_id, issued_by="owner-1"
        )
        uow.invite_codes.save(invite)
        use_case = JoinCommunityWithInviteUseCase(uow)

        membership_id = use_case.execute(user_id="new-user-1", invite_code="JOINME1")

        assert membership_id is not None
        community = uow.communities.find_by_id(community.community_id)
        assert community is not None
        member = community._find_active_membership("new-user-1")
        assert member is not None
        assert member.role == CommunityRole.MEMBER

    def test_redeems_code_after_join(self) -> None:
        uow = FakeUnitOfWork()
        community = make_community(owner_id="owner-1")
        uow.communities.save(community)
        invite = make_invite_code(
            code="USEONCE", community_id=community.community_id, issued_by="owner-1",
            max_uses=1,
        )
        uow.invite_codes.save(invite)
        use_case = JoinCommunityWithInviteUseCase(uow)

        use_case.execute(user_id="new-user-1", invite_code="USEONCE")

        saved = uow.invite_codes.find_by_code("USEONCE")
        assert saved is not None
        assert saved.uses_left == 0
        assert saved.is_valid() is False

    def test_raises_on_invalid_code(self) -> None:
        uow = FakeUnitOfWork()
        use_case = JoinCommunityWithInviteUseCase(uow)

        with pytest.raises(ValueError, match="invalid or has expired"):
            use_case.execute(user_id="user-1", invite_code="NONEXISTENT")

    def test_raises_on_expired_code(self) -> None:
        from datetime import datetime, timedelta, timezone

        uow = FakeUnitOfWork()
        community = make_community(owner_id="owner-1")
        uow.communities.save(community)
        invite = make_invite_code(
            code="EXPIRED1", community_id=community.community_id, issued_by="owner-1",
        )
        invite.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        uow.invite_codes.save(invite)
        use_case = JoinCommunityWithInviteUseCase(uow)

        with pytest.raises(ValueError, match="invalid or has expired"):
            use_case.execute(user_id="new-user-1", invite_code="EXPIRED1")

    def test_raises_on_used_up_code(self) -> None:
        uow = FakeUnitOfWork()
        community = make_community(owner_id="owner-1")
        uow.communities.save(community)
        invite = make_invite_code(
            code="USEDUP1", community_id=community.community_id, issued_by="owner-1",
            max_uses=1,
        )
        invite.redeem()
        uow.invite_codes.save(invite)
        use_case = JoinCommunityWithInviteUseCase(uow)

        with pytest.raises(ValueError, match="invalid or has expired"):
            use_case.execute(user_id="new-user-1", invite_code="USEDUP1")

    def test_raises_if_already_member(self) -> None:
        uow = FakeUnitOfWork()
        community = make_community(owner_id="owner-1")
        community.add_member(
            membership_id="existing-m1",
            user_id="existing-user",
            role=CommunityRole.MEMBER,
        )
        uow.communities.save(community)
        invite = make_invite_code(
            code="ALREADY1", community_id=community.community_id, issued_by="owner-1"
        )
        uow.invite_codes.save(invite)
        use_case = JoinCommunityWithInviteUseCase(uow)

        with pytest.raises(ValueError, match="already an active member"):
            use_case.execute(user_id="existing-user", invite_code="ALREADY1")

    def test_assigns_role_from_code(self) -> None:
        uow = FakeUnitOfWork()
        community = make_community(owner_id="owner-1")
        uow.communities.save(community)
        invite = make_invite_code(
            code="MOD1", community_id=community.community_id,
            issued_by="owner-1", role="moderator",
        )
        uow.invite_codes.save(invite)
        use_case = JoinCommunityWithInviteUseCase(uow)

        use_case.execute(user_id="new-mod", invite_code="MOD1")

        community = uow.communities.find_by_id(community.community_id)
        assert community is not None
        member = community._find_active_membership("new-mod")
        assert member is not None
        assert member.role == CommunityRole.MODERATOR

    def test_commits_successfully(self) -> None:
        uow = FakeUnitOfWork()
        community = make_community(owner_id="owner-1")
        uow.communities.save(community)
        invite = make_invite_code(
            code="COMMIT1", community_id=community.community_id, issued_by="owner-1"
        )
        uow.invite_codes.save(invite)
        use_case = JoinCommunityWithInviteUseCase(uow)

        use_case.execute(user_id="user-1", invite_code="COMMIT1")

        assert uow.committed is True

    def test_fallback_role_when_code_role_is_invalid(self) -> None:
        uow = FakeUnitOfWork()
        community = make_community(owner_id="owner-1")
        uow.communities.save(community)
        invite = make_invite_code(
            code="BADROLE", community_id=community.community_id,
            issued_by="owner-1", role="superadmin",
        )
        uow.invite_codes.save(invite)
        use_case = JoinCommunityWithInviteUseCase(uow)

        membership_id = use_case.execute(user_id="user-1", invite_code="BADROLE")

        community = uow.communities.find_by_id(community.community_id)
        assert community is not None
        member = community._find_active_membership("user-1")
        assert member is not None
        assert member.role == CommunityRole.MEMBER
