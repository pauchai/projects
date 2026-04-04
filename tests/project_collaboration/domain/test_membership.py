"""Tests for Membership entity."""

import pytest
from datetime import datetime, timezone

from project_collaboration.domain.membership import Membership
from project_collaboration.domain.role import ProjectRole


class TestMembershipCreation:
    """Membership is created with a role and active status."""

    def test_creates_active_membership(self) -> None:
        m = Membership(
            membership_id="m1",
            user_id="u1",
            project_id="p1",
            role=ProjectRole.MEMBER,
        )
        assert m.is_active is True

    def test_stores_identity_fields(self) -> None:
        m = Membership(
            membership_id="m1",
            user_id="u1",
            project_id="p1",
            role=ProjectRole.ADMIN,
        )
        assert m.membership_id == "m1"
        assert m.user_id == "u1"
        assert m.project_id == "p1"

    def test_stores_role(self) -> None:
        m = Membership(
            membership_id="m1",
            user_id="u1",
            project_id="p1",
            role=ProjectRole.MENTOR,
        )
        assert m.role == ProjectRole.MENTOR

    def test_has_joined_at_timestamp(self) -> None:
        before = datetime.now(timezone.utc)
        m = Membership(
            membership_id="m1",
            user_id="u1",
            project_id="p1",
            role=ProjectRole.MEMBER,
        )
        after = datetime.now(timezone.utc)
        assert before <= m.joined_at <= after


class TestMembershipDeactivation:
    """Deactivating a membership marks it as inactive."""

    def test_deactivate_sets_inactive(self) -> None:
        m = Membership(
            membership_id="m1",
            user_id="u1",
            project_id="p1",
            role=ProjectRole.MEMBER,
        )
        m.deactivate()
        assert m.is_active is False

    def test_deactivate_already_inactive_raises(self) -> None:
        m = Membership(
            membership_id="m1",
            user_id="u1",
            project_id="p1",
            role=ProjectRole.MEMBER,
        )
        m.deactivate()
        with pytest.raises(ValueError, match="already inactive"):
            m.deactivate()


class TestMembershipRoleChange:
    """Changing a membership role."""

    def test_change_role_updates_role(self) -> None:
        m = Membership(
            membership_id="m1",
            user_id="u1",
            project_id="p1",
            role=ProjectRole.MEMBER,
        )
        m.change_role(ProjectRole.ADMIN)
        assert m.role == ProjectRole.ADMIN

    def test_change_role_to_owner_raises(self) -> None:
        m = Membership(
            membership_id="m1",
            user_id="u1",
            project_id="p1",
            role=ProjectRole.MEMBER,
        )
        with pytest.raises(ValueError, match="Cannot assign Owner"):
            m.change_role(ProjectRole.OWNER)

    def test_change_role_on_inactive_membership_raises(self) -> None:
        m = Membership(
            membership_id="m1",
            user_id="u1",
            project_id="p1",
            role=ProjectRole.MEMBER,
        )
        m.deactivate()
        with pytest.raises(ValueError, match="inactive membership"):
            m.change_role(ProjectRole.ADMIN)
