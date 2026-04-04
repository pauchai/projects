"""Tests for ProjectRole enum and privilege hierarchy."""

import pytest


class TestProjectRoleValues:
    """ProjectRole enum should have exactly 5 values."""

    def test_has_owner_role(self) -> None:
        from project_collaboration.domain.role import ProjectRole

        assert ProjectRole.OWNER.value == "owner"

    def test_has_admin_role(self) -> None:
        from project_collaboration.domain.role import ProjectRole

        assert ProjectRole.ADMIN.value == "admin"

    def test_has_mentor_role(self) -> None:
        from project_collaboration.domain.role import ProjectRole

        assert ProjectRole.MENTOR.value == "mentor"

    def test_has_member_role(self) -> None:
        from project_collaboration.domain.role import ProjectRole

        assert ProjectRole.MEMBER.value == "member"

    def test_has_observer_role(self) -> None:
        from project_collaboration.domain.role import ProjectRole

        assert ProjectRole.OBSERVER.value == "observer"

    def test_has_exactly_five_values(self) -> None:
        from project_collaboration.domain.role import ProjectRole

        assert len(ProjectRole) == 5


class TestProjectRoleManagementRights:
    """Only Owner and Admin can manage members and review applications."""

    def test_owner_has_management_rights(self) -> None:
        from project_collaboration.domain.role import ProjectRole

        assert ProjectRole.OWNER.has_management_rights() is True

    def test_admin_has_management_rights(self) -> None:
        from project_collaboration.domain.role import ProjectRole

        assert ProjectRole.ADMIN.has_management_rights() is True

    def test_mentor_has_no_management_rights(self) -> None:
        from project_collaboration.domain.role import ProjectRole

        assert ProjectRole.MENTOR.has_management_rights() is False

    def test_member_has_no_management_rights(self) -> None:
        from project_collaboration.domain.role import ProjectRole

        assert ProjectRole.MEMBER.has_management_rights() is False

    def test_observer_has_no_management_rights(self) -> None:
        from project_collaboration.domain.role import ProjectRole

        assert ProjectRole.OBSERVER.has_management_rights() is False
