"""Tests for ManageMember use cases (change role and remove)."""

import pytest

from project_collaboration.application.manage_member import (
    ChangeMemberRoleUseCase,
    RemoveMemberUseCase,
)
from project_collaboration.domain.role import ProjectRole
from tests.project_collaboration.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.project_collaboration.factories import make_project_with_member, save_project


# =============================================================================
# ChangeMemberRoleUseCase
# =============================================================================


class TestChangeMemberRoleUseCase:
    """ChangeMemberRole updates a member's role within the project."""

    def test_changes_role(self) -> None:
        uow = FakeUnitOfWork()
        project, membership_id = make_project_with_member()
        save_project(uow, project)
        use_case = ChangeMemberRoleUseCase(uow=uow)

        use_case.execute(
            project_id="p1",
            membership_id=membership_id,
            new_role=ProjectRole.ADMIN,
            caller_id="owner1",
        )

        with uow:
            found = uow.projects.find_by_id("p1")
        assert found is not None
        member = [m for m in found.memberships if m.membership_id == membership_id][0]
        assert member.role == ProjectRole.ADMIN

    def test_raises_when_project_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = ChangeMemberRoleUseCase(uow=uow)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute(
                project_id="p999",
                membership_id="m1",
                new_role=ProjectRole.ADMIN,
                caller_id="owner1",
            )

    def test_raises_when_changing_owner_role(self) -> None:
        uow = FakeUnitOfWork()
        project, _ = make_project_with_member()
        save_project(uow, project)
        owner_membership = [
            m for m in project.memberships if m.role == ProjectRole.OWNER
        ][0]
        use_case = ChangeMemberRoleUseCase(uow=uow)

        with pytest.raises(ValueError, match="[Oo]wner"):
            use_case.execute(
                project_id="p1",
                membership_id=owner_membership.membership_id,
                new_role=ProjectRole.ADMIN,
                caller_id="owner1",
            )

    def test_raises_when_caller_lacks_management_rights(self) -> None:
        uow = FakeUnitOfWork()
        project, membership_id = make_project_with_member()
        save_project(uow, project)
        use_case = ChangeMemberRoleUseCase(uow=uow)

        with pytest.raises(PermissionError, match="management rights"):
            use_case.execute(
                project_id="p1",
                membership_id=membership_id,
                new_role=ProjectRole.ADMIN,
                caller_id="u2",  # u2 is a regular Member, not Owner/Admin
            )


# =============================================================================
# RemoveMemberUseCase
# =============================================================================


class TestRemoveMemberUseCase:
    """RemoveMember deactivates a member's membership."""

    def test_removes_member(self) -> None:
        uow = FakeUnitOfWork()
        project, membership_id = make_project_with_member()
        save_project(uow, project)
        use_case = RemoveMemberUseCase(uow=uow)

        use_case.execute(
            project_id="p1", membership_id=membership_id, caller_id="owner1"
        )

        with uow:
            found = uow.projects.find_by_id("p1")
        assert found is not None
        member = [m for m in found.memberships if m.membership_id == membership_id][0]
        assert member.is_active is False

    def test_raises_when_project_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = RemoveMemberUseCase(uow=uow)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute(project_id="p999", membership_id="m1", caller_id="owner1")

    def test_raises_when_removing_owner(self) -> None:
        uow = FakeUnitOfWork()
        project, _ = make_project_with_member()
        save_project(uow, project)
        owner_membership = [
            m for m in project.memberships if m.role == ProjectRole.OWNER
        ][0]
        use_case = RemoveMemberUseCase(uow=uow)

        with pytest.raises(ValueError, match="[Oo]wner"):
            use_case.execute(
                project_id="p1",
                membership_id=owner_membership.membership_id,
                caller_id="owner1",
            )

    def test_raises_when_caller_lacks_management_rights(self) -> None:
        uow = FakeUnitOfWork()
        project, membership_id = make_project_with_member()
        save_project(uow, project)
        use_case = RemoveMemberUseCase(uow=uow)

        with pytest.raises(PermissionError, match="management rights"):
            use_case.execute(
                project_id="p1",
                membership_id=membership_id,
                caller_id="u2",  # u2 is a regular Member
            )
