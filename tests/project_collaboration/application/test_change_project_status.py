"""Tests for ChangeProjectStatus use cases (activate, suspend, resume, complete, cancel)."""

import pytest

from project_collaboration.application.change_project_status import (
    ActivateProjectUseCase,
    SuspendProjectUseCase,
    ResumeProjectUseCase,
    CompleteProjectUseCase,
    CancelProjectUseCase,
)
from project_collaboration.domain.project import Project
from project_collaboration.domain.project_status import ProjectStatus
from project_collaboration.domain.skill_tag import SkillTag
from tests.project_collaboration.fakes.fake_unit_of_work import FakeUnitOfWork


def _draft_project(uow: FakeUnitOfWork) -> Project:
    p = Project(
        project_id="p1",
        title="Test Project",
        description="Desc.",
        owner_id="owner1",
        required_skills=[SkillTag("python")],
    )
    p.collect_events()
    with uow:
        uow.projects.save(p)
        uow.commit()
    return p


def _recruiting_project(uow: FakeUnitOfWork) -> Project:
    p = _draft_project(uow)
    p.publish()
    p.collect_events()
    with uow:
        uow.projects.save(p)
        uow.commit()
    return p


def _active_project(uow: FakeUnitOfWork) -> Project:
    p = _recruiting_project(uow)
    p.activate()
    p.collect_events()
    with uow:
        uow.projects.save(p)
        uow.commit()
    return p


# =============================================================================
# ActivateProjectUseCase
# =============================================================================


class TestActivateProjectUseCase:
    def test_activates_recruiting_project(self) -> None:
        uow = FakeUnitOfWork()
        _recruiting_project(uow)
        use_case = ActivateProjectUseCase(uow=uow)

        use_case.execute(project_id="p1", caller_id="owner1")

        project = uow.projects.find_by_id("p1")
        assert project is not None
        assert project.status == ProjectStatus.ACTIVE

    def test_raises_when_project_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = ActivateProjectUseCase(uow=uow)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute(project_id="p999", caller_id="owner1")

    def test_raises_when_not_recruiting(self) -> None:
        uow = FakeUnitOfWork()
        _draft_project(uow)
        use_case = ActivateProjectUseCase(uow=uow)

        with pytest.raises(ValueError, match="transition"):
            use_case.execute(project_id="p1", caller_id="owner1")

    def test_raises_when_caller_is_not_owner(self) -> None:
        uow = FakeUnitOfWork()
        _recruiting_project(uow)
        use_case = ActivateProjectUseCase(uow=uow)

        with pytest.raises(PermissionError, match="[Oo]wner"):
            use_case.execute(project_id="p1", caller_id="intruder")


# =============================================================================
# SuspendProjectUseCase
# =============================================================================


class TestSuspendProjectUseCase:
    def test_suspends_recruiting_project(self) -> None:
        uow = FakeUnitOfWork()
        _recruiting_project(uow)
        use_case = SuspendProjectUseCase(uow=uow)

        use_case.execute(project_id="p1", caller_id="owner1")

        project = uow.projects.find_by_id("p1")
        assert project is not None
        assert project.status == ProjectStatus.SUSPENDED

    def test_suspends_active_project(self) -> None:
        uow = FakeUnitOfWork()
        _active_project(uow)
        use_case = SuspendProjectUseCase(uow=uow)

        use_case.execute(project_id="p1", caller_id="owner1")

        project = uow.projects.find_by_id("p1")
        assert project is not None
        assert project.status == ProjectStatus.SUSPENDED

    def test_raises_when_project_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = SuspendProjectUseCase(uow=uow)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute(project_id="p999", caller_id="owner1")

    def test_raises_when_caller_is_not_owner(self) -> None:
        uow = FakeUnitOfWork()
        _recruiting_project(uow)
        use_case = SuspendProjectUseCase(uow=uow)

        with pytest.raises(PermissionError, match="[Oo]wner"):
            use_case.execute(project_id="p1", caller_id="intruder")


# =============================================================================
# ResumeProjectUseCase
# =============================================================================


class TestResumeProjectUseCase:
    def test_resumes_to_recruiting(self) -> None:
        uow = FakeUnitOfWork()
        p = _recruiting_project(uow)
        p.suspend()
        with uow:
            uow.projects.save(p)
            uow.commit()
        use_case = ResumeProjectUseCase(uow=uow)

        use_case.execute(project_id="p1", caller_id="owner1")

        project = uow.projects.find_by_id("p1")
        assert project is not None
        assert project.status == ProjectStatus.RECRUITING

    def test_resumes_to_active(self) -> None:
        uow = FakeUnitOfWork()
        p = _active_project(uow)
        p.suspend()
        with uow:
            uow.projects.save(p)
            uow.commit()
        use_case = ResumeProjectUseCase(uow=uow)

        use_case.execute(project_id="p1", caller_id="owner1")

        project = uow.projects.find_by_id("p1")
        assert project is not None
        assert project.status == ProjectStatus.ACTIVE

    def test_raises_when_not_suspended(self) -> None:
        uow = FakeUnitOfWork()
        _recruiting_project(uow)
        use_case = ResumeProjectUseCase(uow=uow)

        with pytest.raises(ValueError, match="[Ss]uspended"):
            use_case.execute(project_id="p1", caller_id="owner1")

    def test_raises_when_project_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = ResumeProjectUseCase(uow=uow)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute(project_id="p999", caller_id="owner1")

    def test_raises_when_caller_is_not_owner(self) -> None:
        uow = FakeUnitOfWork()
        p = _recruiting_project(uow)
        p.suspend()
        with uow:
            uow.projects.save(p)
            uow.commit()
        use_case = ResumeProjectUseCase(uow=uow)

        with pytest.raises(PermissionError, match="[Oo]wner"):
            use_case.execute(project_id="p1", caller_id="intruder")


# =============================================================================
# CompleteProjectUseCase
# =============================================================================


class TestCompleteProjectUseCase:
    def test_completes_active_project(self) -> None:
        uow = FakeUnitOfWork()
        _active_project(uow)
        use_case = CompleteProjectUseCase(uow=uow)

        use_case.execute(project_id="p1", caller_id="owner1")

        project = uow.projects.find_by_id("p1")
        assert project is not None
        assert project.status == ProjectStatus.COMPLETED

    def test_raises_when_not_active(self) -> None:
        uow = FakeUnitOfWork()
        _recruiting_project(uow)
        use_case = CompleteProjectUseCase(uow=uow)

        with pytest.raises(ValueError, match="transition"):
            use_case.execute(project_id="p1", caller_id="owner1")

    def test_raises_when_project_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CompleteProjectUseCase(uow=uow)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute(project_id="p999", caller_id="owner1")

    def test_raises_when_caller_is_not_owner(self) -> None:
        uow = FakeUnitOfWork()
        _active_project(uow)
        use_case = CompleteProjectUseCase(uow=uow)

        with pytest.raises(PermissionError, match="[Oo]wner"):
            use_case.execute(project_id="p1", caller_id="intruder")


# =============================================================================
# CancelProjectUseCase
# =============================================================================


class TestCancelProjectUseCase:
    def test_cancels_recruiting_project(self) -> None:
        uow = FakeUnitOfWork()
        _recruiting_project(uow)
        use_case = CancelProjectUseCase(uow=uow)

        use_case.execute(project_id="p1", caller_id="owner1")

        project = uow.projects.find_by_id("p1")
        assert project is not None
        assert project.status == ProjectStatus.CANCELLED

    def test_cancels_active_project(self) -> None:
        uow = FakeUnitOfWork()
        _active_project(uow)
        use_case = CancelProjectUseCase(uow=uow)

        use_case.execute(project_id="p1", caller_id="owner1")

        project = uow.projects.find_by_id("p1")
        assert project is not None
        assert project.status == ProjectStatus.CANCELLED

    def test_raises_when_in_draft(self) -> None:
        uow = FakeUnitOfWork()
        _draft_project(uow)
        use_case = CancelProjectUseCase(uow=uow)

        with pytest.raises(ValueError, match="transition"):
            use_case.execute(project_id="p1", caller_id="owner1")

    def test_raises_when_project_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CancelProjectUseCase(uow=uow)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute(project_id="p999", caller_id="owner1")

    def test_raises_when_caller_is_not_owner(self) -> None:
        uow = FakeUnitOfWork()
        _recruiting_project(uow)
        use_case = CancelProjectUseCase(uow=uow)

        with pytest.raises(PermissionError, match="[Oo]wner"):
            use_case.execute(project_id="p1", caller_id="intruder")
