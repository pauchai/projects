"""Tests for UpdateProject use case."""

import pytest

from project_collaboration.application.create_project import CreateProjectUseCase
from project_collaboration.application.update_project import UpdateProjectUseCase
from project_collaboration.domain.events import ProjectUpdated
from project_collaboration.domain.role import ProjectRole
from project_collaboration.domain.skill_tag import SkillTag
from tests.project_collaboration.fakes.fake_unit_of_work import FakeUnitOfWork
from shared_kernel.events import DomainEvent


class _SpyEventBus:
    """Spy event bus that records all published events."""

    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    def publish(self, events: list[DomainEvent]) -> None:
        self.published.extend(events)


class TestUpdateProjectUseCase:
    """UpdateProject updates a project's details."""

    def test_updates_project_title(self) -> None:
        uow = FakeUnitOfWork()
        CreateProjectUseCase(uow=uow).execute(
            project_id="p1",
            title="Original",
            description="Desc",
            owner_id="owner1",
            required_skills=[],
        )
        use_case = UpdateProjectUseCase(uow=uow)

        project = use_case.execute(
            project_id="p1",
            caller_id="owner1",
            title="New Title",
            description="New description",
            required_skills=[SkillTag("rust")],
            max_members=10,
        )

        assert project.title == "New Title"
        assert project.description == "New description"
        assert project.required_skills == [SkillTag("rust")]
        assert project.max_members == 10

    def test_saves_updated_project_to_repository(self) -> None:
        uow = FakeUnitOfWork()
        CreateProjectUseCase(uow=uow).execute(
            project_id="p1",
            title="Original",
            description="Desc",
            owner_id="owner1",
            required_skills=[],
        )
        use_case = UpdateProjectUseCase(uow=uow)

        project = use_case.execute(
            project_id="p1",
            caller_id="owner1",
            title="Updated",
            description="Desc",
            required_skills=[],
            max_members=None,
        )

        with uow:
            loaded = uow.projects.find_by_id("p1")
            assert loaded is not None
            assert loaded.title == "Updated"

    def test_commits_transaction(self) -> None:
        uow = FakeUnitOfWork()
        CreateProjectUseCase(uow=uow).execute(
            project_id="p1",
            title="Original",
            description="Desc",
            owner_id="owner1",
            required_skills=[],
        )
        use_case = UpdateProjectUseCase(uow=uow)

        use_case.execute(
            project_id="p1",
            caller_id="owner1",
            title="Title",
            description="Desc",
            required_skills=[],
            max_members=None,
        )

        assert uow.committed is True

    def test_raises_when_project_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = UpdateProjectUseCase(uow=uow)

        with pytest.raises(LookupError, match="Project p1 not found"):
            use_case.execute(
                project_id="p1",
                caller_id="owner1",
                title="Title",
                description="Desc",
                required_skills=[],
                max_members=None,
            )

    def test_raises_when_caller_is_not_owner(self) -> None:
        uow = FakeUnitOfWork()
        CreateProjectUseCase(uow=uow).execute(
            project_id="p1",
            title="Original",
            description="Desc",
            owner_id="owner1",
            required_skills=[],
        )
        use_case = UpdateProjectUseCase(uow=uow)

        with pytest.raises(PermissionError, match="Only the project owner"):
            use_case.execute(
                project_id="p1",
                caller_id="not_owner",
                title="Title",
                description="Desc",
                required_skills=[],
                max_members=None,
            )

    def test_emits_project_updated_event(self) -> None:
        spy_bus = _SpyEventBus()
        uow = FakeUnitOfWork(event_bus=spy_bus)
        CreateProjectUseCase(uow=uow).execute(
            project_id="p1",
            title="Original",
            description="Desc",
            owner_id="owner1",
            required_skills=[],
        )
        use_case = UpdateProjectUseCase(uow=uow)

        use_case.execute(
            project_id="p1",
            caller_id="owner1",
            title="New Title",
            description="Desc",
            required_skills=[],
            max_members=None,
        )

        events = [e for e in spy_bus.published if isinstance(e, ProjectUpdated)]
        assert len(events) == 1
        event = events[0]
        assert event.project_id == "p1"
        assert "title" in event.updated_fields
