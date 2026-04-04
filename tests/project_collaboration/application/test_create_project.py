"""Tests for CreateProject use case."""

import pytest

from project_collaboration.application.create_project import CreateProjectUseCase
from project_collaboration.domain.project_status import ProjectStatus
from project_collaboration.domain.role import ProjectRole
from project_collaboration.domain.skill_tag import SkillTag
from project_collaboration.domain.events import ProjectCreated
from tests.project_collaboration.fakes.fake_unit_of_work import FakeUnitOfWork


class TestCreateProjectUseCase:
    """CreateProject creates a draft project with owner membership."""

    def test_creates_project_in_draft(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateProjectUseCase(uow=uow)

        project = use_case.execute(
            project_id="p1",
            title="Alpha Project",
            description="A great project.",
            owner_id="u1",
            required_skills=[SkillTag("python")],
        )

        assert project.status == ProjectStatus.DRAFT
        assert project.project_id == "p1"
        assert project.owner_id == "u1"

    def test_saves_project_to_repository(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateProjectUseCase(uow=uow)

        use_case.execute(
            project_id="p1",
            title="Alpha Project",
            description="A great project.",
            owner_id="u1",
            required_skills=[],
        )

        with uow:
            assert uow.projects.find_by_id("p1") is not None

    def test_commits_transaction(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateProjectUseCase(uow=uow)

        use_case.execute(
            project_id="p1",
            title="Alpha Project",
            description="Desc.",
            owner_id="u1",
            required_skills=[],
        )

        assert uow.committed is True

    def test_owner_membership_exists(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateProjectUseCase(uow=uow)

        project = use_case.execute(
            project_id="p1",
            title="Alpha Project",
            description="Desc.",
            owner_id="u1",
            required_skills=[],
        )

        assert len(project.memberships) == 1
        assert project.memberships[0].role == ProjectRole.OWNER
        assert project.memberships[0].user_id == "u1"

    def test_emits_project_created_event(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateProjectUseCase(uow=uow)

        project = use_case.execute(
            project_id="p1",
            title="Alpha",
            description="Desc.",
            owner_id="u1",
            required_skills=[],
        )

        events = project.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], ProjectCreated)

    def test_with_max_members(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateProjectUseCase(uow=uow)

        project = use_case.execute(
            project_id="p1",
            title="Alpha",
            description="Desc.",
            owner_id="u1",
            required_skills=[],
            max_members=5,
        )

        assert project.max_members == 5

    def test_invalid_title_raises(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateProjectUseCase(uow=uow)

        with pytest.raises(ValueError, match="3.*200"):
            use_case.execute(
                project_id="p1",
                title="ab",
                description="Desc.",
                owner_id="u1",
                required_skills=[],
            )
