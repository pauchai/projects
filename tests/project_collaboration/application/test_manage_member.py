"""Tests for ManageMember use cases (change role and remove)."""

import pytest

from project_collaboration.application.manage_member import (
    ChangeMemberRoleUseCase,
    RemoveMemberUseCase,
)
from project_collaboration.domain.project import Project
from project_collaboration.domain.role import ProjectRole
from project_collaboration.domain.skill_tag import SkillTag
from tests.project_collaboration.fakes.fake_unit_of_work import FakeUnitOfWork


def _project_with_member(uow: FakeUnitOfWork) -> tuple[Project, str]:
    """Create a recruiting project with an accepted member. Returns (project, membership_id)."""
    p = Project(
        project_id="p1",
        title="Test Project",
        description="Desc.",
        owner_id="owner1",
        required_skills=[SkillTag("python")],
    )
    p.publish()
    p.apply(
        application_id="a1",
        applicant_id="u2",
        desired_role=ProjectRole.MEMBER,
        motivation="Hi.",
        applicant_skills=[],
    )
    p.accept_application(application_id="a1", reviewed_by="owner1")
    p.collect_events()
    with uow:
        uow.projects.save(p)
        uow.commit()

    member = [m for m in p.memberships if m.user_id == "u2"][0]
    return p, member.membership_id


# =============================================================================
# ChangeMemberRoleUseCase
# =============================================================================


class TestChangeMemberRoleUseCase:
    """ChangeMemberRole updates a member's role within the project."""

    def test_changes_role(self) -> None:
        uow = FakeUnitOfWork()
        _, membership_id = _project_with_member(uow)
        use_case = ChangeMemberRoleUseCase(uow=uow)

        use_case.execute(
            project_id="p1",
            membership_id=membership_id,
            new_role=ProjectRole.ADMIN,
            caller_id="owner1",
        )

        with uow:
            project = uow.projects.find_by_id("p1")
        assert project is not None
        member = [m for m in project.memberships if m.membership_id == membership_id][0]
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
        project, _ = _project_with_member(uow)
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
        _, membership_id = _project_with_member(uow)
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
        _, membership_id = _project_with_member(uow)
        use_case = RemoveMemberUseCase(uow=uow)

        use_case.execute(
            project_id="p1", membership_id=membership_id, caller_id="owner1"
        )

        with uow:
            project = uow.projects.find_by_id("p1")
        assert project is not None
        member = [m for m in project.memberships if m.membership_id == membership_id][0]
        assert member.is_active is False

    def test_raises_when_project_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = RemoveMemberUseCase(uow=uow)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute(project_id="p999", membership_id="m1", caller_id="owner1")

    def test_raises_when_removing_owner(self) -> None:
        uow = FakeUnitOfWork()
        project, _ = _project_with_member(uow)
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
        _, membership_id = _project_with_member(uow)
        use_case = RemoveMemberUseCase(uow=uow)

        with pytest.raises(PermissionError, match="management rights"):
            use_case.execute(
                project_id="p1",
                membership_id=membership_id,
                caller_id="u2",  # u2 is a regular Member
            )
