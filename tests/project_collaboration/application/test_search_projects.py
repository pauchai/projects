"""Tests for SearchProjects use case."""

import pytest

from project_collaboration.application.search_projects import SearchProjectsUseCase
from project_collaboration.domain.project import Project
from project_collaboration.domain.project_status import ProjectStatus
from project_collaboration.domain.skill_tag import SkillTag
from tests.project_collaboration.fakes.fake_unit_of_work import FakeUnitOfWork


def _recruiting_project(
    uow: FakeUnitOfWork,
    project_id: str = "p1",
    title: str = "Test Project",
    description: str = "A test project description.",
    owner_id: str = "owner1",
    skills: list[SkillTag] | None = None,
) -> Project:
    """Create a recruiting project in the UoW."""
    p = Project(
        project_id=project_id,
        title=title,
        description=description,
        owner_id=owner_id,
        required_skills=skills or [SkillTag("python")],
    )
    p.publish()
    p.collect_events()
    with uow:
        uow.projects.save(p)
        uow.commit()
    return p


class TestSearchProjectsUseCase:
    """SearchProjects returns projects matching skills, keyword, and status filters."""

    def test_search_by_skills_returns_matching_projects(self) -> None:
        uow = FakeUnitOfWork()
        _recruiting_project(uow, project_id="p1", skills=[SkillTag("python")])
        _recruiting_project(uow, project_id="p2", skills=[SkillTag("rust")])
        use_case = SearchProjectsUseCase(uow=uow)

        results = use_case.execute(skills=[SkillTag("python")])

        assert len(results) == 1
        assert results[0].project_id == "p1"

    def test_defaults_to_recruiting_status(self) -> None:
        """When no status is passed, only Recruiting projects are returned."""
        uow = FakeUnitOfWork()
        # Create a Recruiting project
        _recruiting_project(uow, project_id="p1")
        # Create an Active project (Recruiting -> Active transition)
        active = _recruiting_project(uow, project_id="p2")
        active.activate()
        active.collect_events()
        with uow:
            uow.projects.save(active)
            uow.commit()

        use_case = SearchProjectsUseCase(uow=uow)
        results = use_case.execute()

        assert len(results) == 1
        assert results[0].project_id == "p1"

    def test_search_by_keyword_matches_title(self) -> None:
        uow = FakeUnitOfWork()
        _recruiting_project(uow, project_id="p1", title="Machine Learning Platform")
        _recruiting_project(uow, project_id="p2", title="Web Backend")
        use_case = SearchProjectsUseCase(uow=uow)

        results = use_case.execute(keyword="machine")

        assert len(results) == 1
        assert results[0].project_id == "p1"

    def test_search_by_keyword_matches_description(self) -> None:
        uow = FakeUnitOfWork()
        _recruiting_project(
            uow,
            project_id="p1",
            title="Generic Title",
            description="Build a recommendation engine with collaborative filtering.",
        )
        _recruiting_project(
            uow,
            project_id="p2",
            title="Another Title",
            description="Simple CRUD application.",
        )
        use_case = SearchProjectsUseCase(uow=uow)

        results = use_case.execute(keyword="recommendation")

        assert len(results) == 1
        assert results[0].project_id == "p1"

    def test_search_returns_empty_when_no_match(self) -> None:
        uow = FakeUnitOfWork()
        _recruiting_project(uow, project_id="p1", skills=[SkillTag("python")])
        use_case = SearchProjectsUseCase(uow=uow)

        results = use_case.execute(skills=[SkillTag("haskell")])

        assert results == []

    def test_search_with_no_filters_returns_all_recruiting(self) -> None:
        uow = FakeUnitOfWork()
        _recruiting_project(uow, project_id="p1", skills=[SkillTag("python")])
        _recruiting_project(uow, project_id="p2", skills=[SkillTag("rust")])
        use_case = SearchProjectsUseCase(uow=uow)

        results = use_case.execute()

        assert len(results) == 2
        ids = {r.project_id for r in results}
        assert ids == {"p1", "p2"}

    def test_search_with_explicit_status_override(self) -> None:
        """Passing an explicit status overrides the Recruiting default."""
        uow = FakeUnitOfWork()
        _recruiting_project(uow, project_id="p1")
        active = _recruiting_project(uow, project_id="p2")
        active.activate()
        active.collect_events()
        with uow:
            uow.projects.save(active)
            uow.commit()

        use_case = SearchProjectsUseCase(uow=uow)
        results = use_case.execute(status=ProjectStatus.ACTIVE)

        assert len(results) == 1
        assert results[0].project_id == "p2"

    def test_search_combines_skill_and_keyword_filters(self) -> None:
        uow = FakeUnitOfWork()
        _recruiting_project(
            uow,
            project_id="p1",
            title="ML Pipeline",
            skills=[SkillTag("python")],
        )
        _recruiting_project(
            uow,
            project_id="p2",
            title="ML Dashboard",
            skills=[SkillTag("typescript")],
        )
        _recruiting_project(
            uow,
            project_id="p3",
            title="Data API",
            skills=[SkillTag("python")],
        )
        use_case = SearchProjectsUseCase(uow=uow)

        results = use_case.execute(skills=[SkillTag("python")], keyword="ml")

        assert len(results) == 1
        assert results[0].project_id == "p1"
