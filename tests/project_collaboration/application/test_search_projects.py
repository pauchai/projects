"""Tests for SearchProjects use case."""

import pytest

from project_collaboration.application.search_projects import SearchProjectsUseCase
from project_collaboration.domain.project_status import ProjectStatus
from project_collaboration.domain.skill_tag import SkillTag
from tests.project_collaboration.fakes.fake_unit_of_work import FakeUnitOfWork
from project_collaboration.domain.role import ProjectRole
from tests.project_collaboration.factories import (
    make_recruiting_project,
    make_project_with_member,
    save_project,
)


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

    def test_search_by_owner_id_returns_only_owned_projects(self) -> None:
        uow = FakeUnitOfWork()
        save_project(uow, make_recruiting_project(project_id="p1", owner_id="alice"))
        save_project(uow, make_recruiting_project(project_id="p2", owner_id="bob"))
        use_case = SearchProjectsUseCase(uow=uow)

        results = use_case.execute(owner_id="alice")

        assert len(results) == 1
        assert results[0].project_id == "p1"

    def test_search_by_owner_id_with_no_status_returns_all_statuses(self) -> None:
        """Owner filter with status=None returns projects in any status."""
        uow = FakeUnitOfWork()
        save_project(uow, make_recruiting_project(project_id="p1", owner_id="alice"))
        active = make_recruiting_project(project_id="p2", owner_id="alice")
        active.activate()
        active.collect_events()
        save_project(uow, active)
        use_case = SearchProjectsUseCase(uow=uow)

        results = use_case.execute(owner_id="alice", status=None)

        assert len(results) == 2
        ids = {r.project_id for r in results}
        assert ids == {"p1", "p2"}

    def test_search_by_member_user_id_returns_projects_with_active_membership(
        self,
    ) -> None:
        uow = FakeUnitOfWork()
        project_with_member, _ = make_project_with_member(
            project_id="p1", owner_id="alice"
        )
        save_project(uow, project_with_member)
        save_project(uow, make_recruiting_project(project_id="p2", owner_id="bob"))
        use_case = SearchProjectsUseCase(uow=uow)

        # u2 is the member added by make_project_with_member
        results = use_case.execute(member_user_id="u2", status=None)

        assert len(results) == 1
        assert results[0].project_id == "p1"

    def test_search_by_member_user_id_excludes_inactive_memberships(self) -> None:
        uow = FakeUnitOfWork()
        project, membership_id = make_project_with_member(
            project_id="p1", owner_id="alice"
        )
        project.remove_member(membership_id=membership_id)
        project.collect_events()
        save_project(uow, project)
        use_case = SearchProjectsUseCase(uow=uow)

        results = use_case.execute(member_user_id="u2", status=None)

        assert results == []

    def test_search_combines_owner_id_with_keyword(self) -> None:
        uow = FakeUnitOfWork()
        save_project(
            uow,
            make_recruiting_project(
                project_id="p1", owner_id="alice", title="ML Platform"
            ),
        )
        save_project(
            uow,
            make_recruiting_project(project_id="p2", owner_id="alice", title="Web App"),
        )
        save_project(
            uow,
            make_recruiting_project(project_id="p3", owner_id="bob", title="ML Tools"),
        )
        use_case = SearchProjectsUseCase(uow=uow)

        results = use_case.execute(owner_id="alice", keyword="ml")

        assert len(results) == 1
        assert results[0].project_id == "p1"
