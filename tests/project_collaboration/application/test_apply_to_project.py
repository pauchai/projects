"""Tests for ApplyToProject use case."""

import pytest

from project_collaboration.application.apply_to_project import ApplyToProjectUseCase
from project_collaboration.domain.project import Project
from project_collaboration.domain.project_status import ProjectStatus
from project_collaboration.domain.role import ProjectRole
from project_collaboration.domain.skill_tag import SkillTag
from tests.project_collaboration.fakes.fake_unit_of_work import FakeUnitOfWork


def _recruiting_project(uow: FakeUnitOfWork, **overrides) -> Project:
    defaults = dict(
        project_id="p1",
        title="Test Project",
        description="Desc.",
        owner_id="owner1",
        required_skills=[SkillTag("python")],
    )
    defaults.update(overrides)
    p = Project(**defaults)
    p.publish()
    p.collect_events()
    with uow:
        uow.projects.save(p)
        uow.commit()
    return p


class TestApplyToProjectUseCase:
    """ApplyToProject adds a pending application to a recruiting project."""

    def test_creates_pending_application(self) -> None:
        uow = FakeUnitOfWork()
        _recruiting_project(uow)
        use_case = ApplyToProjectUseCase(uow=uow)

        use_case.execute(
            application_id="a1",
            project_id="p1",
            applicant_id="u2",
            desired_role=ProjectRole.MEMBER,
            motivation="I want to join.",
            applicant_skills=[SkillTag("python")],
        )

        with uow:
            project = uow.projects.find_by_id("p1")
        assert project is not None
        assert len(project.applications) == 1

    def test_raises_when_project_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = ApplyToProjectUseCase(uow=uow)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute(
                application_id="a1",
                project_id="p999",
                applicant_id="u2",
                desired_role=ProjectRole.MEMBER,
                motivation="Hi.",
                applicant_skills=[],
            )

    def test_raises_when_not_recruiting(self) -> None:
        uow = FakeUnitOfWork()
        p = Project(
            project_id="p1",
            title="Draft Project",
            description="Desc.",
            owner_id="owner1",
            required_skills=[],
        )
        with uow:
            uow.projects.save(p)  # still in DRAFT
            uow.commit()
        use_case = ApplyToProjectUseCase(uow=uow)

        with pytest.raises(ValueError, match="[Rr]ecruiting"):
            use_case.execute(
                application_id="a1",
                project_id="p1",
                applicant_id="u2",
                desired_role=ProjectRole.MEMBER,
                motivation="Hi.",
                applicant_skills=[],
            )

    def test_raises_when_already_member(self) -> None:
        uow = FakeUnitOfWork()
        _recruiting_project(uow, owner_id="u1")
        use_case = ApplyToProjectUseCase(uow=uow)

        with pytest.raises(ValueError, match="already.*member"):
            use_case.execute(
                application_id="a1",
                project_id="p1",
                applicant_id="u1",  # owner
                desired_role=ProjectRole.MEMBER,
                motivation="Hi.",
                applicant_skills=[],
            )
