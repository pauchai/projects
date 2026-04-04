"""Tests for PublishProject use case."""

import pytest

from project_collaboration.application.publish_project import PublishProjectUseCase
from project_collaboration.domain.project import Project
from project_collaboration.domain.project_status import ProjectStatus
from project_collaboration.domain.skill_tag import SkillTag
from tests.project_collaboration.fakes.fake_unit_of_work import FakeUnitOfWork


def _saved_draft_project(uow: FakeUnitOfWork) -> Project:
    p = Project(
        project_id="p1",
        title="Test Project",
        description="Desc.",
        owner_id="u1",
        required_skills=[SkillTag("python")],
    )
    p.collect_events()  # clear creation events
    with uow:
        uow.projects.save(p)
        uow.commit()
    return p


class TestPublishProjectUseCase:
    """PublishProject transitions a draft project to recruiting."""

    def test_publishes_draft_project(self) -> None:
        uow = FakeUnitOfWork()
        _saved_draft_project(uow)
        use_case = PublishProjectUseCase(uow=uow)

        use_case.execute(project_id="p1")

        with uow:
            project = uow.projects.find_by_id("p1")
        assert project is not None
        assert project.status == ProjectStatus.RECRUITING

    def test_raises_when_project_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = PublishProjectUseCase(uow=uow)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute(project_id="p999")

    def test_raises_when_not_in_draft(self) -> None:
        uow = FakeUnitOfWork()
        p = _saved_draft_project(uow)
        p.publish()  # already recruiting
        with uow:
            uow.projects.save(p)
            uow.commit()
        use_case = PublishProjectUseCase(uow=uow)

        with pytest.raises(ValueError, match="transition"):
            use_case.execute(project_id="p1")
