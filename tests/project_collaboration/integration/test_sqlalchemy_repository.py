"""Integration tests for SqlAlchemyProjectRepository and SqlAlchemyUnitOfWork.

These tests verify the real PostgreSQL persistence layer:
- Round-trip save/load of full Project aggregates
- Persistence of all child entities (memberships, applications)
- Persistence of value objects (SkillTag via association table, applicant_skills via JSON)
- Persistence of previous_status for suspend/resume
- Search with filters (status, keyword, skills)
- UoW commit/rollback semantics
- Nonexistent project returns None

Requires ``docker compose up -d postgres-test`` (port 5433).
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session, sessionmaker

from project_collaboration.domain.application_form import ApplicationStatus
from project_collaboration.domain.project import Project
from project_collaboration.domain.project_status import ProjectStatus
from project_collaboration.domain.role import ProjectRole
from project_collaboration.domain.skill_tag import SkillTag
from project_collaboration.infrastructure.sqlalchemy_repository import (
    SqlAlchemyProjectRepository,
)
from project_collaboration.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_project(**overrides: object) -> Project:
    """Create a Project with defaults (mirrors test factories but avoids FakeUoW import)."""
    defaults: dict = dict(
        project_id="p1",
        title="Test Project",
        description="A test project description.",
        owner_id="owner1",
        required_skills=[SkillTag("python")],
        max_members=None,
    )
    defaults.update(overrides)
    p = Project(**defaults)
    p.collect_events()  # clear creation events
    return p


# ---------------------------------------------------------------------------
# Repository: find_by_id
# ---------------------------------------------------------------------------


class TestFindById:
    """Tests for SqlAlchemyProjectRepository.find_by_id."""

    def test_returns_none_for_nonexistent_project(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyProjectRepository(integration_session)

        result = repo.find_by_id("nonexistent")

        assert result is None

    def test_round_trip_saves_and_loads_project(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyProjectRepository(integration_session)
        project = _make_project()

        repo.save(project)
        loaded = repo.find_by_id("p1")

        assert loaded is not None
        assert loaded.project_id == "p1"
        assert loaded.title == "Test Project"
        assert loaded.description == "A test project description."
        assert loaded.owner_id == "owner1"
        assert loaded.status == ProjectStatus.DRAFT
        assert loaded.max_members is None
        assert loaded.created_at is not None

    def test_persists_required_skills(self, integration_session: Session) -> None:
        repo = SqlAlchemyProjectRepository(integration_session)
        project = _make_project(
            required_skills=[SkillTag("python"), SkillTag("rust"), SkillTag("docker")]
        )

        repo.save(project)
        loaded = repo.find_by_id("p1")

        assert loaded is not None
        skill_values = sorted(s.value for s in loaded.required_skills)
        assert skill_values == ["docker", "python", "rust"]

    def test_persists_owner_membership(self, integration_session: Session) -> None:
        repo = SqlAlchemyProjectRepository(integration_session)
        project = _make_project()

        repo.save(project)
        loaded = repo.find_by_id("p1")

        assert loaded is not None
        assert len(loaded.memberships) == 1
        owner_m = loaded.memberships[0]
        assert owner_m.user_id == "owner1"
        assert owner_m.role == ProjectRole.OWNER
        assert owner_m.is_active is True

    def test_persists_project_status_after_publish(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyProjectRepository(integration_session)
        project = _make_project()
        project.publish()
        project.collect_events()

        repo.save(project)
        loaded = repo.find_by_id("p1")

        assert loaded is not None
        assert loaded.status == ProjectStatus.RECRUITING

    def test_persists_previous_status_after_suspend(
        self, integration_session: Session
    ) -> None:
        """previous_status must survive a DB round-trip for resume."""
        repo = SqlAlchemyProjectRepository(integration_session)
        project = _make_project()
        project.publish()
        project.activate()
        project.suspend()
        project.collect_events()

        repo.save(project)
        loaded = repo.find_by_id("p1")

        assert loaded is not None
        assert loaded.status == ProjectStatus.SUSPENDED
        assert loaded.previous_status == ProjectStatus.ACTIVE

    def test_persists_max_members(self, integration_session: Session) -> None:
        repo = SqlAlchemyProjectRepository(integration_session)
        project = _make_project(max_members=5)

        repo.save(project)
        loaded = repo.find_by_id("p1")

        assert loaded is not None
        assert loaded.max_members == 5


# ---------------------------------------------------------------------------
# Repository: applications
# ---------------------------------------------------------------------------


class TestApplicationPersistence:
    """Tests for persistence of ApplicationForm entities."""

    def test_persists_application(self, integration_session: Session) -> None:
        repo = SqlAlchemyProjectRepository(integration_session)
        project = _make_project()
        project.publish()
        project.apply(
            application_id="a1",
            applicant_id="u2",
            desired_role=ProjectRole.MEMBER,
            motivation="I want to join.",
            applicant_skills=[SkillTag("python"), SkillTag("react")],
        )
        project.collect_events()

        repo.save(project)
        loaded = repo.find_by_id("p1")

        assert loaded is not None
        assert len(loaded.applications) == 1
        app = loaded.applications[0]
        assert app.application_id == "a1"
        assert app.applicant_id == "u2"
        assert app.project_id == "p1"
        assert app.desired_role == ProjectRole.MEMBER
        assert app.motivation == "I want to join."
        assert app.status == ApplicationStatus.PENDING
        assert app.reviewed_by is None
        # applicant_skills stored as JSON, reconstituted as SkillTag objects
        skill_values = sorted(s.value for s in app.applicant_skills)
        assert skill_values == ["python", "react"]

    def test_persists_accepted_application_and_new_membership(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyProjectRepository(integration_session)
        project = _make_project()
        project.publish()
        project.apply(
            application_id="a1",
            applicant_id="u2",
            desired_role=ProjectRole.MEMBER,
            motivation="I want to join.",
            applicant_skills=[SkillTag("python")],
        )
        project.accept_application(application_id="a1", reviewed_by="owner1")
        project.collect_events()

        repo.save(project)
        loaded = repo.find_by_id("p1")

        assert loaded is not None
        # Application should be accepted
        app = [a for a in loaded.applications if a.application_id == "a1"][0]
        assert app.status == ApplicationStatus.ACCEPTED
        assert app.reviewed_by == "owner1"
        # New membership for u2 should exist
        u2_memberships = [m for m in loaded.memberships if m.user_id == "u2"]
        assert len(u2_memberships) == 1
        assert u2_memberships[0].role == ProjectRole.MEMBER
        assert u2_memberships[0].is_active is True

    def test_persists_rejected_application(self, integration_session: Session) -> None:
        repo = SqlAlchemyProjectRepository(integration_session)
        project = _make_project()
        project.publish()
        project.apply(
            application_id="a1",
            applicant_id="u2",
            desired_role=ProjectRole.MEMBER,
            motivation="I want to join.",
            applicant_skills=[SkillTag("python")],
        )
        project.reject_application(application_id="a1", reviewed_by="owner1")
        project.collect_events()

        repo.save(project)
        loaded = repo.find_by_id("p1")

        assert loaded is not None
        app = loaded.applications[0]
        assert app.status == ApplicationStatus.REJECTED
        assert app.reviewed_by == "owner1"


# ---------------------------------------------------------------------------
# Repository: membership changes
# ---------------------------------------------------------------------------


class TestMembershipPersistence:
    """Tests for persistence of membership changes (role change, deactivation)."""

    def test_persists_role_change(self, integration_session: Session) -> None:
        repo = SqlAlchemyProjectRepository(integration_session)
        project = _make_project()
        project.publish()
        project.apply(
            application_id="a1",
            applicant_id="u2",
            desired_role=ProjectRole.MEMBER,
            motivation="I want to join.",
            applicant_skills=[SkillTag("python")],
        )
        project.accept_application(application_id="a1", reviewed_by="owner1")
        u2_m = [m for m in project.memberships if m.user_id == "u2"][0]
        project.change_member_role(u2_m.membership_id, ProjectRole.ADMIN)
        project.collect_events()

        repo.save(project)
        loaded = repo.find_by_id("p1")

        assert loaded is not None
        loaded_u2 = [m for m in loaded.memberships if m.user_id == "u2"][0]
        assert loaded_u2.role == ProjectRole.ADMIN

    def test_persists_member_deactivation(self, integration_session: Session) -> None:
        repo = SqlAlchemyProjectRepository(integration_session)
        project = _make_project()
        project.publish()
        project.apply(
            application_id="a1",
            applicant_id="u2",
            desired_role=ProjectRole.MEMBER,
            motivation="I want to join.",
            applicant_skills=[SkillTag("python")],
        )
        project.accept_application(application_id="a1", reviewed_by="owner1")
        u2_m = [m for m in project.memberships if m.user_id == "u2"][0]
        project.remove_member(u2_m.membership_id)
        project.collect_events()

        repo.save(project)
        loaded = repo.find_by_id("p1")

        assert loaded is not None
        loaded_u2 = [m for m in loaded.memberships if m.user_id == "u2"][0]
        assert loaded_u2.is_active is False


# ---------------------------------------------------------------------------
# Repository: upsert (save twice)
# ---------------------------------------------------------------------------


class TestUpsertBehavior:
    """Verify that save() is idempotent (upsert semantics)."""

    def test_save_twice_updates_existing_project(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyProjectRepository(integration_session)
        project = _make_project()

        repo.save(project)

        # Mutate and save again
        project.publish()
        project.collect_events()
        repo.save(project)

        loaded = repo.find_by_id("p1")
        assert loaded is not None
        assert loaded.status == ProjectStatus.RECRUITING


# ---------------------------------------------------------------------------
# Repository: search
# ---------------------------------------------------------------------------


class TestSearch:
    """Tests for SqlAlchemyProjectRepository.search."""

    def test_search_returns_all_when_no_filters(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyProjectRepository(integration_session)
        repo.save(_make_project(project_id="p1", title="Alpha Project"))
        repo.save(_make_project(project_id="p2", title="Beta Project"))

        results = repo.search()

        assert len(results) == 2
        ids = {r.project_id for r in results}
        assert ids == {"p1", "p2"}

    def test_search_by_status(self, integration_session: Session) -> None:
        repo = SqlAlchemyProjectRepository(integration_session)
        draft = _make_project(project_id="p1")
        recruiting = _make_project(project_id="p2", title="Recruiting Proj")
        recruiting.publish()
        recruiting.collect_events()
        repo.save(draft)
        repo.save(recruiting)

        results = repo.search(status=ProjectStatus.RECRUITING)

        assert len(results) == 1
        assert results[0].project_id == "p2"

    def test_search_by_keyword_in_title(self, integration_session: Session) -> None:
        repo = SqlAlchemyProjectRepository(integration_session)
        repo.save(_make_project(project_id="p1", title="Machine Learning Pipeline"))
        repo.save(_make_project(project_id="p2", title="Web Dashboard"))

        results = repo.search(keyword="machine")

        assert len(results) == 1
        assert results[0].project_id == "p1"

    def test_search_by_keyword_in_description(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyProjectRepository(integration_session)
        repo.save(
            _make_project(
                project_id="p1",
                title="Project A",
                description="Uses advanced neural networks",
            )
        )
        repo.save(
            _make_project(
                project_id="p2",
                title="Project B",
                description="Simple CRUD app",
            )
        )

        results = repo.search(keyword="neural")

        assert len(results) == 1
        assert results[0].project_id == "p1"

    def test_search_by_skills(self, integration_session: Session) -> None:
        repo = SqlAlchemyProjectRepository(integration_session)
        repo.save(
            _make_project(
                project_id="p1",
                required_skills=[SkillTag("python"), SkillTag("docker")],
            )
        )
        repo.save(
            _make_project(
                project_id="p2",
                required_skills=[SkillTag("rust")],
            )
        )

        results = repo.search(skills=[SkillTag("python")])

        assert len(results) == 1
        assert results[0].project_id == "p1"

    def test_search_combined_filters(self, integration_session: Session) -> None:
        repo = SqlAlchemyProjectRepository(integration_session)

        p1 = _make_project(
            project_id="p1",
            title="ML Pipeline",
            required_skills=[SkillTag("python")],
        )
        p1.publish()
        p1.collect_events()

        p2 = _make_project(
            project_id="p2",
            title="ML Dashboard",
            required_skills=[SkillTag("typescript")],
        )
        p2.publish()
        p2.collect_events()

        p3 = _make_project(
            project_id="p3",
            title="ML Notebook",
            required_skills=[SkillTag("python")],
        )
        # p3 stays Draft

        repo.save(p1)
        repo.save(p2)
        repo.save(p3)

        # Recruiting + keyword "ML" + skill "python" -> only p1
        results = repo.search(
            status=ProjectStatus.RECRUITING,
            keyword="ML",
            skills=[SkillTag("python")],
        )

        assert len(results) == 1
        assert results[0].project_id == "p1"

    def test_search_returns_empty_when_no_matches(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyProjectRepository(integration_session)
        repo.save(_make_project(project_id="p1"))

        results = repo.search(keyword="nonexistent")

        assert results == []


# ---------------------------------------------------------------------------
# Repository: reconstituted project has empty _events
# ---------------------------------------------------------------------------


class TestReconstitution:
    """Verify reconstituted projects have clean transient state."""

    def test_reconstituted_project_has_empty_events(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyProjectRepository(integration_session)
        project = _make_project()

        repo.save(project)
        loaded = repo.find_by_id("p1")

        assert loaded is not None
        assert loaded._events == []

    def test_reconstituted_project_previous_status_is_none_for_non_suspended(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyProjectRepository(integration_session)
        project = _make_project()

        repo.save(project)
        loaded = repo.find_by_id("p1")

        assert loaded is not None
        assert loaded.previous_status is None


# ---------------------------------------------------------------------------
# Unit of Work: commit/rollback semantics
# ---------------------------------------------------------------------------


class TestUnitOfWork:
    """Tests for SqlAlchemyUnitOfWork commit and rollback semantics."""

    def test_uow_commit_persists_changes(
        self,
        integration_session_factory: sessionmaker[Session],
    ) -> None:
        uow = SqlAlchemyUnitOfWork(integration_session_factory)
        project = _make_project()

        with uow:
            uow.projects.save(project)
            uow.commit()

        # Read back via a fresh UoW
        with uow:
            loaded = uow.projects.find_by_id("p1")
            assert loaded is not None
            assert loaded.project_id == "p1"

    def test_uow_rollback_discards_changes(
        self,
        integration_session_factory: sessionmaker[Session],
    ) -> None:
        uow = SqlAlchemyUnitOfWork(integration_session_factory)
        project = _make_project()

        with uow:
            uow.projects.save(project)
            uow.rollback()

        # Should not find the project
        with uow:
            loaded = uow.projects.find_by_id("p1")
            assert loaded is None

    def test_uow_exit_without_commit_rolls_back(
        self,
        integration_session_factory: sessionmaker[Session],
    ) -> None:
        uow = SqlAlchemyUnitOfWork(integration_session_factory)
        project = _make_project()

        with uow:
            uow.projects.save(project)
            # no commit, __exit__ should rollback

        with uow:
            loaded = uow.projects.find_by_id("p1")
            assert loaded is None
