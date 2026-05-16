"""Tests for RedeemProjectInviteUseCase."""

from __future__ import annotations

import pytest

from project_collaboration.application.redeem_project_invite import RedeemProjectInviteUseCase
from project_collaboration.domain.membership import Membership
from project_collaboration.domain.role import ProjectRole
from tests.project_collaboration.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.project_collaboration.factories import (
    make_recruiting_project,
    save_project,
)


class TestRedeemProjectInviteUseCase:
    """RedeemProjectInviteUseCase creates a Membership from a project-scoped invite."""

    def test_execute_adds_membership_to_project(self) -> None:
        # Arrange
        uow = FakeUnitOfWork()
        save_project(uow, make_recruiting_project())
        use_case = RedeemProjectInviteUseCase(uow)

        # Act
        membership_id = use_case.execute(
            user_id="new-user",
            project_id="p1",
            role_value="member",
        )

        # Assert
        with uow:
            project = uow.projects.find_by_id("p1")
        assert project is not None
        member = next((m for m in project.memberships if m.user_id == "new-user"), None)
        assert member is not None
        assert member.membership_id == membership_id
        assert member.role == ProjectRole.MEMBER
        assert member.is_active is True

    def test_execute_returns_membership_id_string(self) -> None:
        # Arrange
        uow = FakeUnitOfWork()
        save_project(uow, make_recruiting_project())
        use_case = RedeemProjectInviteUseCase(uow)

        # Act
        membership_id = use_case.execute(
            user_id="new-user",
            project_id="p1",
            role_value="mentor",
        )

        # Assert
        assert isinstance(membership_id, str)
        assert len(membership_id) > 0

    def test_execute_commits_unit_of_work(self) -> None:
        # Arrange
        uow = FakeUnitOfWork()
        save_project(uow, make_recruiting_project())
        use_case = RedeemProjectInviteUseCase(uow)

        # Act
        use_case.execute(user_id="new-user", project_id="p1", role_value="member")

        # Assert
        assert uow.committed is True

    def test_execute_raises_lookup_error_when_project_not_found(self) -> None:
        # Arrange
        uow = FakeUnitOfWork()
        use_case = RedeemProjectInviteUseCase(uow)

        # Act & Assert
        with pytest.raises(LookupError, match="p999"):
            use_case.execute(user_id="new-user", project_id="p999", role_value="member")

    def test_execute_raises_value_error_when_user_already_active_member(self) -> None:
        # Arrange
        uow = FakeUnitOfWork()
        project = make_recruiting_project()
        project.memberships.append(
            Membership(
                membership_id="existing-m",
                user_id="existing-user",
                project_id="p1",
                role=ProjectRole.MEMBER,
            )
        )
        save_project(uow, project)
        use_case = RedeemProjectInviteUseCase(uow)

        # Act & Assert
        with pytest.raises(ValueError, match="already an active member"):
            use_case.execute(
                user_id="existing-user",
                project_id="p1",
                role_value="member",
            )

    def test_execute_falls_back_to_member_role_for_invalid_role_value(self) -> None:
        # Arrange
        uow = FakeUnitOfWork()
        save_project(uow, make_recruiting_project())
        use_case = RedeemProjectInviteUseCase(uow)

        # Act
        use_case.execute(
            user_id="new-user",
            project_id="p1",
            role_value="nonexistent_role",
        )

        # Assert — invalid role falls back to MEMBER, no exception raised
        with uow:
            project = uow.projects.find_by_id("p1")
        assert project is not None
        member = next((m for m in project.memberships if m.user_id == "new-user"), None)
        assert member is not None
        assert member.role == ProjectRole.MEMBER
