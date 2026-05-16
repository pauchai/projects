"""Tests for CreateProjectNeedUseCase."""

from __future__ import annotations

import pytest

from project_collaboration.application.create_project_need import (
    CreateProjectNeedCommand,
    CreateProjectNeedUseCase,
)
from project_collaboration.domain.project_need import NeedStatus
from project_collaboration.domain.role import ProjectRole
from tests.project_collaboration.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.project_collaboration.factories import (
    make_project_with_active_member,
    make_recruiting_project,
    save_project,
)


def _make_command(**overrides: object) -> CreateProjectNeedCommand:
    defaults: dict = dict(
        project_id="p1",
        caller_id="u2",
        role=ProjectRole.MEMBER,
        description="Looking for a contributor.",
        skills=["python"],
        slots=1,
    )
    defaults.update(overrides)
    return CreateProjectNeedCommand(**defaults)  # type: ignore[arg-type]


class TestCreateProjectNeedUseCase:
    """CreateProjectNeedUseCase lets an active member post an open position."""

    def test_execute_saves_need_and_returns_need_id(self) -> None:
        # Arrange
        uow = FakeUnitOfWork()
        save_project(uow, make_project_with_active_member(user_id="u2"))
        use_case = CreateProjectNeedUseCase(uow)

        # Act
        need_id = use_case.execute(_make_command())

        # Assert
        need = uow.needs.find_by_id(need_id)
        assert need is not None
        assert need.project_id == "p1"
        assert need.status == NeedStatus.OPEN

    def test_execute_returns_string_need_id(self) -> None:
        # Arrange
        uow = FakeUnitOfWork()
        save_project(uow, make_project_with_active_member(user_id="u2"))
        use_case = CreateProjectNeedUseCase(uow)

        # Act
        need_id = use_case.execute(_make_command())

        # Assert
        assert isinstance(need_id, str)
        assert len(need_id) > 0

    def test_execute_persists_skills_and_slots(self) -> None:
        # Arrange
        uow = FakeUnitOfWork()
        save_project(uow, make_project_with_active_member(user_id="u2"))
        use_case = CreateProjectNeedUseCase(uow)
        cmd = _make_command(skills=["python", "react"], slots=3)

        # Act
        need_id = use_case.execute(cmd)

        # Assert
        need = uow.needs.find_by_id(need_id)
        assert need is not None
        assert need.skills == ["python", "react"]
        assert need.slots == 3

    def test_execute_commits_unit_of_work(self) -> None:
        # Arrange
        uow = FakeUnitOfWork()
        save_project(uow, make_project_with_active_member(user_id="u2"))
        use_case = CreateProjectNeedUseCase(uow)

        # Act
        use_case.execute(_make_command())

        # Assert
        assert uow.committed is True

    def test_execute_raises_lookup_error_when_project_not_found(self) -> None:
        # Arrange
        uow = FakeUnitOfWork()
        use_case = CreateProjectNeedUseCase(uow)

        # Act & Assert
        with pytest.raises(LookupError, match="p1"):
            use_case.execute(_make_command(project_id="p1"))

    def test_execute_raises_permission_error_when_caller_not_member(self) -> None:
        # Arrange
        uow = FakeUnitOfWork()
        save_project(uow, make_recruiting_project())  # no extra members
        use_case = CreateProjectNeedUseCase(uow)

        # Act & Assert — "u2" is not a member (only owner1 is)
        with pytest.raises(PermissionError, match="active project members"):
            use_case.execute(_make_command(caller_id="u2"))

    def test_execute_raises_permission_error_when_caller_membership_inactive(self) -> None:
        # Arrange
        uow = FakeUnitOfWork()
        project = make_project_with_active_member(user_id="u2")
        # Deactivate u2's membership
        member = next(m for m in project.memberships if m.user_id == "u2")
        member.deactivate()
        save_project(uow, project)
        use_case = CreateProjectNeedUseCase(uow)

        # Act & Assert
        with pytest.raises(PermissionError, match="active project members"):
            use_case.execute(_make_command(caller_id="u2"))

    def test_execute_raises_value_error_when_description_is_empty(self) -> None:
        # Arrange
        uow = FakeUnitOfWork()
        save_project(uow, make_project_with_active_member(user_id="u2"))
        use_case = CreateProjectNeedUseCase(uow)

        # Act & Assert — domain invariant: empty description forbidden
        with pytest.raises(ValueError, match="description"):
            use_case.execute(_make_command(description="   "))

    def test_execute_raises_value_error_when_slots_less_than_one(self) -> None:
        # Arrange
        uow = FakeUnitOfWork()
        save_project(uow, make_project_with_active_member(user_id="u2"))
        use_case = CreateProjectNeedUseCase(uow)

        # Act & Assert — domain invariant: slots >= 1
        with pytest.raises(ValueError, match="slots"):
            use_case.execute(_make_command(slots=0))

    def test_execute_raises_value_error_when_role_is_owner(self) -> None:
        # Arrange
        uow = FakeUnitOfWork()
        save_project(uow, make_project_with_active_member(user_id="u2"))
        use_case = CreateProjectNeedUseCase(uow)

        # Act & Assert — domain invariant: cannot post a need for OWNER role
        with pytest.raises(ValueError, match="OWNER"):
            use_case.execute(_make_command(role=ProjectRole.OWNER))
