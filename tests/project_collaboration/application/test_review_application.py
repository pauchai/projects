"""Tests for ReviewApplication use cases (accept and reject)."""

import pytest

from project_collaboration.application.review_application import (
    AcceptApplicationUseCase,
    RejectApplicationUseCase,
)
from project_collaboration.domain.application_form import ApplicationStatus
from project_collaboration.domain.role import ProjectRole
from tests.project_collaboration.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.project_collaboration.factories import (
    make_project_with_application,
    save_project,
)


# =============================================================================
# AcceptApplicationUseCase
# =============================================================================


class TestAcceptApplicationUseCase:
    """AcceptApplication approves a pending application and creates membership."""

    def test_accepts_application(self) -> None:
        uow = FakeUnitOfWork()
        save_project(uow, make_project_with_application())
        use_case = AcceptApplicationUseCase(uow=uow)

        use_case.execute(
            project_id="p1",
            application_id="a1",
            caller_id="owner1",
        )

        with uow:
            project = uow.projects.find_by_id("p1")
        assert project is not None
        app = project.applications[0]
        assert app.status == ApplicationStatus.ACCEPTED

    def test_creates_membership_for_applicant(self) -> None:
        uow = FakeUnitOfWork()
        save_project(uow, make_project_with_application())
        use_case = AcceptApplicationUseCase(uow=uow)

        use_case.execute(
            project_id="p1",
            application_id="a1",
            caller_id="owner1",
        )

        with uow:
            project = uow.projects.find_by_id("p1")
        assert project is not None
        active = [m for m in project.memberships if m.is_active]
        assert len(active) == 2  # owner + new member
        new_member = [m for m in active if m.user_id == "u2"][0]
        assert new_member.role == ProjectRole.MEMBER

    def test_raises_when_project_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = AcceptApplicationUseCase(uow=uow)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute(
                project_id="p999",
                application_id="a1",
                caller_id="owner1",
            )

    def test_raises_when_at_max_members(self) -> None:
        uow = FakeUnitOfWork()
        save_project(uow, make_project_with_application(max_members=1))
        use_case = AcceptApplicationUseCase(uow=uow)

        with pytest.raises(ValueError, match="max.*member"):
            use_case.execute(
                project_id="p1",
                application_id="a1",
                caller_id="owner1",
            )

    def test_raises_when_reviewer_lacks_management_rights(self) -> None:
        uow = FakeUnitOfWork()
        save_project(uow, make_project_with_application())
        use_case = AcceptApplicationUseCase(uow=uow)

        with pytest.raises(PermissionError, match="management rights"):
            use_case.execute(
                project_id="p1",
                application_id="a1",
                caller_id="intruder",
            )


# =============================================================================
# RejectApplicationUseCase
# =============================================================================


class TestRejectApplicationUseCase:
    """RejectApplication declines a pending application."""

    def test_rejects_application(self) -> None:
        uow = FakeUnitOfWork()
        save_project(uow, make_project_with_application())
        use_case = RejectApplicationUseCase(uow=uow)

        use_case.execute(
            project_id="p1",
            application_id="a1",
            caller_id="owner1",
        )

        with uow:
            project = uow.projects.find_by_id("p1")
        assert project is not None
        app = project.applications[0]
        assert app.status == ApplicationStatus.REJECTED

    def test_raises_when_project_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = RejectApplicationUseCase(uow=uow)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute(
                project_id="p999",
                application_id="a1",
                caller_id="owner1",
            )

    def test_raises_when_application_not_found(self) -> None:
        uow = FakeUnitOfWork()
        save_project(uow, make_project_with_application())
        use_case = RejectApplicationUseCase(uow=uow)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute(
                project_id="p1",
                application_id="a999",
                caller_id="owner1",
            )

    def test_raises_when_reviewer_lacks_management_rights(self) -> None:
        uow = FakeUnitOfWork()
        save_project(uow, make_project_with_application())
        use_case = RejectApplicationUseCase(uow=uow)

        with pytest.raises(PermissionError, match="management rights"):
            use_case.execute(
                project_id="p1",
                application_id="a1",
                caller_id="intruder",
            )
