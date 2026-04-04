"""Tests for PublishProject use case."""

import pytest

from project_collaboration.application.publish_project import PublishProjectUseCase
from project_collaboration.domain.project import Project
from project_collaboration.domain.project_status import ProjectStatus
from project_collaboration.domain.skill_tag import SkillTag
from tests.project_collaboration.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.project_collaboration.factories import make_project, save_project


class TestPublishProjectUseCase:
    """PublishProject transitions a draft project to recruiting."""

    def test_publishes_draft_project(self) -> None:
        uow = FakeUnitOfWork()
        save_project(uow, make_project(owner_id="u1"))
        use_case = PublishProjectUseCase(uow=uow)

        use_case.execute(project_id="p1", caller_id="u1")

        with uow:
            project = uow.projects.find_by_id("p1")
        assert project is not None
        assert project.status == ProjectStatus.RECRUITING

    def test_raises_when_project_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = PublishProjectUseCase(uow=uow)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute(project_id="p999", caller_id="u1")

    def test_raises_when_not_in_draft(self) -> None:
        uow = FakeUnitOfWork()
        p = make_project(owner_id="u1")
        p.publish()  # already recruiting
        p.collect_events()
        save_project(uow, p)
        use_case = PublishProjectUseCase(uow=uow)

        with pytest.raises(ValueError, match="transition"):
            use_case.execute(project_id="p1", caller_id="u1")

    def test_raises_when_caller_is_not_owner(self) -> None:
        uow = FakeUnitOfWork()
        save_project(uow, make_project(owner_id="u1"))
        use_case = PublishProjectUseCase(uow=uow)

        with pytest.raises(PermissionError, match="[Oo]wner"):
            use_case.execute(project_id="p1", caller_id="intruder")
