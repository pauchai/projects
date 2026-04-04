"""Tests for application-layer helper functions."""

import pytest

from project_collaboration.application._helpers import (
    get_project_or_raise,
    require_management_rights,
)
from project_collaboration.domain.role import ProjectRole
from tests.project_collaboration.factories import make_project, make_recruiting_project
from tests.project_collaboration.fakes.fake_unit_of_work import FakeUnitOfWork


class TestGetProjectOrRaise:
    def test_returns_project_when_found(self) -> None:
        uow = FakeUnitOfWork()
        project = make_project()
        uow.projects.save(project)

        result = get_project_or_raise(uow, project.project_id)

        assert result.project_id == project.project_id

    def test_raises_lookup_error_when_not_found(self) -> None:
        uow = FakeUnitOfWork()

        with pytest.raises(LookupError, match="not found"):
            get_project_or_raise(uow, "nonexistent")


class TestRequireManagementRights:
    def test_passes_for_owner(self) -> None:
        project = make_recruiting_project(owner_id="owner1")

        # Should not raise
        require_management_rights(project, "owner1")

    def test_passes_for_admin(self) -> None:
        project = make_recruiting_project(owner_id="owner1")
        project.apply(
            application_id="a1",
            applicant_id="admin1",
            desired_role=ProjectRole.ADMIN,
            motivation="I want to help.",
            applicant_skills=[],
        )
        project.accept_application(application_id="a1", reviewed_by="owner1")

        require_management_rights(project, "admin1")

    def test_raises_permission_error_for_regular_member(self) -> None:
        project = make_recruiting_project(owner_id="owner1")
        project.apply(
            application_id="a1",
            applicant_id="member1",
            desired_role=ProjectRole.MEMBER,
            motivation="I want to join.",
            applicant_skills=[],
        )
        project.accept_application(application_id="a1", reviewed_by="owner1")

        with pytest.raises(PermissionError, match="management rights"):
            require_management_rights(project, "member1")

    def test_raises_permission_error_for_non_member(self) -> None:
        project = make_recruiting_project(owner_id="owner1")

        with pytest.raises(PermissionError, match="management rights"):
            require_management_rights(project, "stranger")
