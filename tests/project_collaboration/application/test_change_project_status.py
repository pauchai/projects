"""Tests for ChangeProjectStatus use cases (activate, suspend, resume, complete, cancel)."""

import pytest

from project_collaboration.application.change_project_status import (
    ActivateProjectUseCase,
    SuspendProjectUseCase,
    ResumeProjectUseCase,
    CompleteProjectUseCase,
    CancelProjectUseCase,
)
from project_collaboration.domain.project_status import ProjectStatus
from tests.project_collaboration.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.project_collaboration.factories import (
    make_project,
    make_recruiting_project,
    make_active_project,
    save_project,
)


# =============================================================================
# ActivateProjectUseCase
# =============================================================================


class TestActivateProjectUseCase:
    def test_activates_recruiting_project(self) -> None:
        uow = FakeUnitOfWork()
        save_project(uow, make_recruiting_project())
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
        save_project(uow, make_project())
        use_case = ActivateProjectUseCase(uow=uow)

        with pytest.raises(ValueError, match="transition"):
            use_case.execute(project_id="p1", caller_id="owner1")

    def test_raises_when_caller_is_not_owner(self) -> None:
        uow = FakeUnitOfWork()
        save_project(uow, make_recruiting_project())
        use_case = ActivateProjectUseCase(uow=uow)

        with pytest.raises(PermissionError, match="[Oo]wner"):
            use_case.execute(project_id="p1", caller_id="intruder")


# =============================================================================
# SuspendProjectUseCase
# =============================================================================


class TestSuspendProjectUseCase:
    def test_suspends_recruiting_project(self) -> None:
        uow = FakeUnitOfWork()
        save_project(uow, make_recruiting_project())
        use_case = SuspendProjectUseCase(uow=uow)

        use_case.execute(project_id="p1", caller_id="owner1")

        project = uow.projects.find_by_id("p1")
        assert project is not None
        assert project.status == ProjectStatus.SUSPENDED

    def test_suspends_active_project(self) -> None:
        uow = FakeUnitOfWork()
        save_project(uow, make_active_project())
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
        save_project(uow, make_recruiting_project())
        use_case = SuspendProjectUseCase(uow=uow)

        with pytest.raises(PermissionError, match="[Oo]wner"):
            use_case.execute(project_id="p1", caller_id="intruder")


# =============================================================================
# ResumeProjectUseCase
# =============================================================================


class TestResumeProjectUseCase:
    def test_resumes_to_recruiting(self) -> None:
        uow = FakeUnitOfWork()
        p = make_recruiting_project()
        p.suspend()
        p.collect_events()
        save_project(uow, p)
        use_case = ResumeProjectUseCase(uow=uow)

        use_case.execute(project_id="p1", caller_id="owner1")

        project = uow.projects.find_by_id("p1")
        assert project is not None
        assert project.status == ProjectStatus.RECRUITING

    def test_resumes_to_active(self) -> None:
        uow = FakeUnitOfWork()
        p = make_active_project()
        p.suspend()
        p.collect_events()
        save_project(uow, p)
        use_case = ResumeProjectUseCase(uow=uow)

        use_case.execute(project_id="p1", caller_id="owner1")

        project = uow.projects.find_by_id("p1")
        assert project is not None
        assert project.status == ProjectStatus.ACTIVE

    def test_raises_when_not_suspended(self) -> None:
        uow = FakeUnitOfWork()
        save_project(uow, make_recruiting_project())
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
        p = make_recruiting_project()
        p.suspend()
        p.collect_events()
        save_project(uow, p)
        use_case = ResumeProjectUseCase(uow=uow)

        with pytest.raises(PermissionError, match="[Oo]wner"):
            use_case.execute(project_id="p1", caller_id="intruder")


# =============================================================================
# CompleteProjectUseCase
# =============================================================================


class TestCompleteProjectUseCase:
    def test_completes_active_project(self) -> None:
        uow = FakeUnitOfWork()
        save_project(uow, make_active_project())
        use_case = CompleteProjectUseCase(uow=uow)

        use_case.execute(project_id="p1", caller_id="owner1")

        project = uow.projects.find_by_id("p1")
        assert project is not None
        assert project.status == ProjectStatus.COMPLETED

    def test_raises_when_not_active(self) -> None:
        uow = FakeUnitOfWork()
        save_project(uow, make_recruiting_project())
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
        save_project(uow, make_active_project())
        use_case = CompleteProjectUseCase(uow=uow)

        with pytest.raises(PermissionError, match="[Oo]wner"):
            use_case.execute(project_id="p1", caller_id="intruder")


# =============================================================================
# CancelProjectUseCase
# =============================================================================


class TestCancelProjectUseCase:
    def test_cancels_recruiting_project(self) -> None:
        uow = FakeUnitOfWork()
        save_project(uow, make_recruiting_project())
        use_case = CancelProjectUseCase(uow=uow)

        use_case.execute(project_id="p1", caller_id="owner1")

        project = uow.projects.find_by_id("p1")
        assert project is not None
        assert project.status == ProjectStatus.CANCELLED

    def test_cancels_active_project(self) -> None:
        uow = FakeUnitOfWork()
        save_project(uow, make_active_project())
        use_case = CancelProjectUseCase(uow=uow)

        use_case.execute(project_id="p1", caller_id="owner1")

        project = uow.projects.find_by_id("p1")
        assert project is not None
        assert project.status == ProjectStatus.CANCELLED

    def test_raises_when_in_draft(self) -> None:
        uow = FakeUnitOfWork()
        save_project(uow, make_project())
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
        save_project(uow, make_recruiting_project())
        use_case = CancelProjectUseCase(uow=uow)

        with pytest.raises(PermissionError, match="[Oo]wner"):
            use_case.execute(project_id="p1", caller_id="intruder")
