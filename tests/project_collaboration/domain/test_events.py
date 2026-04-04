"""Tests for domain event dataclasses."""

import pytest
from dataclasses import FrozenInstanceError

from project_collaboration.domain.events import (
    DomainEvent,
    ProjectCreated,
    ProjectPublished,
    ProjectActivated,
    ProjectSuspended,
    ProjectResumed,
    ProjectCompleted,
    ProjectCancelled,
    ApplicationSubmitted,
    ApplicationAccepted,
    ApplicationRejected,
    MemberJoined,
    MemberRoleChanged,
    MemberRemoved,
)
from project_collaboration.domain.role import ProjectRole


class TestDomainEventBase:
    """All events inherit from DomainEvent and are frozen."""

    def test_project_created_is_domain_event(self) -> None:
        event = ProjectCreated(project_id="p1", owner_id="u1", title="My Project")
        assert isinstance(event, DomainEvent)

    def test_events_are_frozen(self) -> None:
        event = ProjectCreated(project_id="p1", owner_id="u1", title="My Project")
        with pytest.raises(FrozenInstanceError):
            event.project_id = "p2"  # type: ignore[misc]


class TestProjectEvents:
    """Project lifecycle events carry the correct payloads."""

    def test_project_created_fields(self) -> None:
        event = ProjectCreated(project_id="p1", owner_id="u1", title="Alpha")
        assert event.project_id == "p1"
        assert event.owner_id == "u1"
        assert event.title == "Alpha"

    def test_project_published_fields(self) -> None:
        event = ProjectPublished(project_id="p1")
        assert event.project_id == "p1"

    def test_project_activated_fields(self) -> None:
        event = ProjectActivated(project_id="p1")
        assert event.project_id == "p1"

    def test_project_suspended_fields(self) -> None:
        event = ProjectSuspended(project_id="p1")
        assert event.project_id == "p1"

    def test_project_resumed_fields(self) -> None:
        event = ProjectResumed(project_id="p1")
        assert event.project_id == "p1"

    def test_project_completed_fields(self) -> None:
        event = ProjectCompleted(project_id="p1")
        assert event.project_id == "p1"

    def test_project_cancelled_fields(self) -> None:
        event = ProjectCancelled(project_id="p1")
        assert event.project_id == "p1"


class TestApplicationEvents:
    """Application events carry application, project, and applicant IDs."""

    def test_application_submitted_fields(self) -> None:
        event = ApplicationSubmitted(
            application_id="a1", project_id="p1", applicant_id="u1"
        )
        assert event.application_id == "a1"
        assert event.project_id == "p1"
        assert event.applicant_id == "u1"

    def test_application_accepted_fields(self) -> None:
        event = ApplicationAccepted(
            application_id="a1", project_id="p1", applicant_id="u1"
        )
        assert event.application_id == "a1"
        assert event.project_id == "p1"
        assert event.applicant_id == "u1"

    def test_application_rejected_fields(self) -> None:
        event = ApplicationRejected(
            application_id="a1", project_id="p1", applicant_id="u1"
        )
        assert event.application_id == "a1"
        assert event.project_id == "p1"
        assert event.applicant_id == "u1"


class TestMemberEvents:
    """Member events carry membership, project, and user details."""

    def test_member_joined_fields(self) -> None:
        event = MemberJoined(
            membership_id="m1", project_id="p1", user_id="u1", role=ProjectRole.MEMBER
        )
        assert event.membership_id == "m1"
        assert event.project_id == "p1"
        assert event.user_id == "u1"
        assert event.role == ProjectRole.MEMBER

    def test_member_role_changed_fields(self) -> None:
        event = MemberRoleChanged(
            membership_id="m1", project_id="p1", new_role=ProjectRole.ADMIN
        )
        assert event.membership_id == "m1"
        assert event.project_id == "p1"
        assert event.new_role == ProjectRole.ADMIN

    def test_member_removed_fields(self) -> None:
        event = MemberRemoved(membership_id="m1", project_id="p1", user_id="u1")
        assert event.membership_id == "m1"
        assert event.project_id == "p1"
        assert event.user_id == "u1"
