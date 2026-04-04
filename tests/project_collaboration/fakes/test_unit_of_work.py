"""Tests for FakeUnitOfWork — verifies UoW Protocol and Fake behavior."""

import pytest

from project_collaboration.domain.ports import UnitOfWork
from project_collaboration.domain.project import Project
from project_collaboration.domain.project_status import ProjectStatus
from project_collaboration.domain.skill_tag import SkillTag
from tests.project_collaboration.fakes.fake_unit_of_work import FakeUnitOfWork


class TestFakeUnitOfWork:
    """FakeUnitOfWork provides in-memory repos and tracks commit/rollback."""

    def test_provides_project_repository(self) -> None:
        uow = FakeUnitOfWork()
        with uow:
            assert uow.projects is not None

    def test_commit_marks_committed(self) -> None:
        uow = FakeUnitOfWork()
        with uow:
            uow.commit()
        assert uow.committed is True

    def test_not_committed_by_default(self) -> None:
        uow = FakeUnitOfWork()
        with uow:
            pass
        assert uow.committed is False

    def test_save_and_find_through_uow(self) -> None:
        uow = FakeUnitOfWork()
        with uow:
            project = Project(
                project_id="p1",
                title="Test Project",
                description="Desc.",
                owner_id="u1",
                required_skills=[SkillTag("python")],
            )
            uow.projects.save(project)
            uow.commit()

        # Data persists after commit
        with uow:
            found = uow.projects.find_by_id("p1")
            assert found is not None
            assert found.project_id == "p1"

    def test_rollback_discards_changes(self) -> None:
        uow = FakeUnitOfWork()

        # Pre-populate with a project
        with uow:
            project = Project(
                project_id="p1",
                title="Original",
                description="Desc.",
                owner_id="u1",
                required_skills=[],
            )
            uow.projects.save(project)
            uow.commit()

        # Make a change but rollback
        with uow:
            project2 = Project(
                project_id="p2",
                title="New Project",
                description="Desc.",
                owner_id="u2",
                required_skills=[],
            )
            uow.projects.save(project2)
            uow.rollback()

        # p2 should not be visible after rollback
        with uow:
            assert uow.projects.find_by_id("p1") is not None
            assert uow.projects.find_by_id("p2") is None

    def test_exit_without_commit_rolls_back(self) -> None:
        uow = FakeUnitOfWork()

        # Pre-populate
        with uow:
            project = Project(
                project_id="p1",
                title="Original",
                description="Desc.",
                owner_id="u1",
                required_skills=[],
            )
            uow.projects.save(project)
            uow.commit()

        # Enter, add something, exit without commit (implicit rollback)
        with uow:
            project2 = Project(
                project_id="p2",
                title="Uncommitted",
                description="Desc.",
                owner_id="u2",
                required_skills=[],
            )
            uow.projects.save(project2)
            # no commit — __exit__ should rollback

        with uow:
            assert uow.projects.find_by_id("p1") is not None
            assert uow.projects.find_by_id("p2") is None

    def test_rollback_reverts_mutations_to_existing_project(self) -> None:
        """Regression: snapshot must deep-copy so rollback reverts in-place mutations."""
        uow = FakeUnitOfWork()

        # Pre-populate with a Draft project
        with uow:
            project = Project(
                project_id="p1",
                title="Original",
                description="Desc.",
                owner_id="u1",
                required_skills=[],
            )
            uow.projects.save(project)
            uow.commit()

        # Enter UoW, mutate the project in-place, then exit without commit
        with uow:
            found = uow.projects.find_by_id("p1")
            assert found is not None
            found.publish()  # Draft -> Recruiting (in-place mutation)
            uow.projects.save(found)
            # no commit — should rollback

        # After rollback, the project should still be in Draft
        with uow:
            restored = uow.projects.find_by_id("p1")
            assert restored is not None
            assert restored.status == ProjectStatus.DRAFT

    def test_satisfies_unit_of_work_protocol(self) -> None:
        """FakeUnitOfWork is structurally compatible with UnitOfWork Protocol."""
        # The type annotation verifies structural compatibility at type-check time.
        uow: UnitOfWork = FakeUnitOfWork()
        # At runtime, verify the interface exists via duck typing.
        with uow:
            assert hasattr(uow, "projects")
            assert callable(getattr(uow, "commit"))
            assert callable(getattr(uow, "rollback"))
