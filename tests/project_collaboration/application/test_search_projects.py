"""Tests for SearchProjects use case."""

import pytest

from project_collaboration.application.search_projects import SearchProjectsUseCase
from project_collaboration.domain.project_status import ProjectStatus
from project_collaboration.domain.skill_tag import SkillTag
from tests.project_collaboration.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.project_collaboration.factories import make_recruiting_project, save_project


class TestSearchProjectsUseCase:
    """SearchProjects returns projects matching skills, keyword, and status filters."""

    def test_search_by_skills_returns_matching_projects(self) -> None:
        uow = FakeUnitOfWork()
        save_project(
            uow,
            make_recruiting_project(
                project_id="p1", required_skills=[SkillTag("python")]
            ),
        )
        save_project(
            uow,
            make_recruiting_project(
                project_id="p2", required_skills=[SkillTag("rust")]
            ),
        )
        use_case = SearchProjectsUseCase(uow=uow)

        results = use_case.execute(skills=[SkillTag("python")])

        assert len(results) == 1
        assert results[0].project_id == "p1"

    def test_defaults_to_recruiting_status(self) -> None:
        """When no status is passed, only Recruiting projects are returned."""
        uow = FakeUnitOfWork()
        save_project(uow, make_recruiting_project(project_id="p1"))
        active = make_recruiting_project(project_id="p2")
        active.activate()
        active.collect_events()
        save_project(uow, active)

        use_case = SearchProjectsUseCase(uow=uow)
        results = use_case.execute()

        assert len(results) == 1
        assert results[0].project_id == "p1"

    def test_search_by_keyword_matches_title(self) -> None:
        uow = FakeUnitOfWork()
        save_project(
            uow,
            make_recruiting_project(project_id="p1", title="Machine Learning Platform"),
        )
        save_project(uow, make_recruiting_project(project_id="p2", title="Web Backend"))
        use_case = SearchProjectsUseCase(uow=uow)

        results = use_case.execute(keyword="machine")

        assert len(results) == 1
        assert results[0].project_id == "p1"

    def test_search_by_keyword_matches_description(self) -> None:
        uow = FakeUnitOfWork()
        save_project(
            uow,
            make_recruiting_project(
                project_id="p1",
                title="Generic Title",
                description="Build a recommendation engine with collaborative filtering.",
            ),
        )
        save_project(
            uow,
            make_recruiting_project(
                project_id="p2",
                title="Another Title",
                description="Simple CRUD application.",
            ),
        )
        use_case = SearchProjectsUseCase(uow=uow)

        results = use_case.execute(keyword="recommendation")

        assert len(results) == 1
        assert results[0].project_id == "p1"

    def test_search_returns_empty_when_no_match(self) -> None:
        uow = FakeUnitOfWork()
        save_project(
            uow,
            make_recruiting_project(
                project_id="p1", required_skills=[SkillTag("python")]
            ),
        )
        use_case = SearchProjectsUseCase(uow=uow)

        results = use_case.execute(skills=[SkillTag("haskell")])

        assert results == []

    def test_search_with_no_filters_returns_all_recruiting(self) -> None:
        uow = FakeUnitOfWork()
        save_project(
            uow,
            make_recruiting_project(
                project_id="p1", required_skills=[SkillTag("python")]
            ),
        )
        save_project(
            uow,
            make_recruiting_project(
                project_id="p2", required_skills=[SkillTag("rust")]
            ),
        )
        use_case = SearchProjectsUseCase(uow=uow)

        results = use_case.execute()

        assert len(results) == 2
        ids = {r.project_id for r in results}
        assert ids == {"p1", "p2"}

    def test_search_with_explicit_status_override(self) -> None:
        """Passing an explicit status overrides the Recruiting default."""
        uow = FakeUnitOfWork()
        save_project(uow, make_recruiting_project(project_id="p1"))
        active = make_recruiting_project(project_id="p2")
        active.activate()
        active.collect_events()
        save_project(uow, active)

        use_case = SearchProjectsUseCase(uow=uow)
        results = use_case.execute(status=ProjectStatus.ACTIVE)

        assert len(results) == 1
        assert results[0].project_id == "p2"

    def test_search_combines_skill_and_keyword_filters(self) -> None:
        uow = FakeUnitOfWork()
        save_project(
            uow,
            make_recruiting_project(
                project_id="p1",
                title="ML Pipeline",
                required_skills=[SkillTag("python")],
            ),
        )
        save_project(
            uow,
            make_recruiting_project(
                project_id="p2",
                title="ML Dashboard",
                required_skills=[SkillTag("typescript")],
            ),
        )
        save_project(
            uow,
            make_recruiting_project(
                project_id="p3",
                title="Data API",
                required_skills=[SkillTag("python")],
            ),
        )
        use_case = SearchProjectsUseCase(uow=uow)

        results = use_case.execute(skills=[SkillTag("python")], keyword="ml")

        assert len(results) == 1
        assert results[0].project_id == "p1"
