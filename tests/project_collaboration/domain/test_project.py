"""Tests for Project aggregate root."""

import pytest
from datetime import datetime, timezone

from project_collaboration.domain.project import Project
from project_collaboration.domain.project_status import ProjectStatus
from project_collaboration.domain.role import ProjectRole
from project_collaboration.domain.skill_tag import SkillTag
from project_collaboration.domain.events import (
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
from project_collaboration.domain.application_form import ApplicationStatus


# --- Helpers ---


def _make_project(**overrides) -> Project:
    """Create a Project with sensible defaults, overridable."""
    defaults = dict(
        project_id="p1",
        title="Test Project",
        description="A test project description.",
        owner_id="owner1",
        required_skills=[SkillTag("python")],
        max_members=None,
    )
    defaults.update(overrides)
    return Project(**defaults)


def _recruiting_project(**overrides) -> Project:
    """Create a project already in Recruiting status."""
    p = _make_project(**overrides)
    p.publish()
    p.collect_events()  # clear events from setup
    return p


def _active_project(**overrides) -> Project:
    """Create a project already in Active status."""
    p = _recruiting_project(**overrides)
    p.activate()
    p.collect_events()
    return p


# =============================================================================
# Creation
# =============================================================================


class TestProjectCreation:
    """A new Project starts in Draft with an Owner membership."""

    def test_starts_in_draft_status(self) -> None:
        p = _make_project()
        assert p.status == ProjectStatus.DRAFT

    def test_stores_identity_and_attributes(self) -> None:
        skills = [SkillTag("python"), SkillTag("design")]
        p = _make_project(
            project_id="p99",
            title="Alpha",
            description="Desc",
            owner_id="u5",
            required_skills=skills,
            max_members=10,
        )
        assert p.project_id == "p99"
        assert p.title == "Alpha"
        assert p.description == "Desc"
        assert p.owner_id == "u5"
        assert p.required_skills == skills
        assert p.max_members == 10

    def test_has_created_at_timestamp(self) -> None:
        before = datetime.now(timezone.utc)
        p = _make_project()
        after = datetime.now(timezone.utc)
        assert before <= p.created_at <= after

    def test_owner_membership_is_created(self) -> None:
        p = _make_project(owner_id="u1")
        assert len(p.memberships) == 1
        m = p.memberships[0]
        assert m.user_id == "u1"
        assert m.role == ProjectRole.OWNER
        assert m.is_active is True

    def test_emits_project_created_event(self) -> None:
        p = _make_project(project_id="p1", owner_id="u1", title="Alpha")
        events = p.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], ProjectCreated)
        assert events[0].project_id == "p1"
        assert events[0].owner_id == "u1"
        assert events[0].title == "Alpha"

    def test_title_too_short_raises(self) -> None:
        with pytest.raises(ValueError, match="3.*200"):
            _make_project(title="ab")

    def test_title_too_long_raises(self) -> None:
        with pytest.raises(ValueError, match="3.*200"):
            _make_project(title="x" * 201)

    def test_description_too_long_raises(self) -> None:
        with pytest.raises(ValueError, match="5000"):
            _make_project(description="x" * 5001)

    def test_applications_list_is_empty(self) -> None:
        p = _make_project()
        assert p.applications == []


# =============================================================================
# Status Transitions (via aggregate methods)
# =============================================================================


class TestProjectPublish:
    """Publishing transitions Draft -> Recruiting."""

    def test_publish_changes_status_to_recruiting(self) -> None:
        p = _make_project()
        p.publish()
        assert p.status == ProjectStatus.RECRUITING

    def test_publish_emits_project_published(self) -> None:
        p = _make_project(project_id="p1")
        p.collect_events()  # discard creation event
        p.publish()
        events = p.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], ProjectPublished)
        assert events[0].project_id == "p1"

    def test_publish_from_recruiting_raises(self) -> None:
        p = _recruiting_project()
        with pytest.raises(ValueError, match="transition"):
            p.publish()


class TestProjectActivate:
    """Activating transitions Recruiting -> Active."""

    def test_activate_changes_status_to_active(self) -> None:
        p = _recruiting_project()
        p.activate()
        assert p.status == ProjectStatus.ACTIVE

    def test_activate_emits_event(self) -> None:
        p = _recruiting_project(project_id="p1")
        p.activate()
        events = p.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], ProjectActivated)

    def test_activate_from_draft_raises(self) -> None:
        p = _make_project()
        p.collect_events()
        with pytest.raises(ValueError, match="transition"):
            p.activate()


class TestProjectSuspend:
    """Suspending remembers the previous status for resume."""

    def test_suspend_from_recruiting(self) -> None:
        p = _recruiting_project()
        p.suspend()
        assert p.status == ProjectStatus.SUSPENDED

    def test_suspend_from_active(self) -> None:
        p = _active_project()
        p.suspend()
        assert p.status == ProjectStatus.SUSPENDED

    def test_suspend_emits_event(self) -> None:
        p = _recruiting_project(project_id="p1")
        p.suspend()
        events = p.collect_events()
        assert any(isinstance(e, ProjectSuspended) for e in events)

    def test_suspend_from_draft_raises(self) -> None:
        p = _make_project()
        p.collect_events()
        with pytest.raises(ValueError, match="transition"):
            p.suspend()


class TestProjectResume:
    """Resuming restores the status before suspension."""

    def test_resume_from_suspended_recruiting(self) -> None:
        p = _recruiting_project()
        p.suspend()
        p.resume()
        assert p.status == ProjectStatus.RECRUITING

    def test_resume_from_suspended_active(self) -> None:
        p = _active_project()
        p.suspend()
        p.resume()
        assert p.status == ProjectStatus.ACTIVE

    def test_resume_emits_event(self) -> None:
        p = _recruiting_project(project_id="p1")
        p.suspend()
        p.collect_events()
        p.resume()
        events = p.collect_events()
        assert any(isinstance(e, ProjectResumed) for e in events)

    def test_resume_from_non_suspended_raises(self) -> None:
        p = _recruiting_project()
        with pytest.raises(ValueError, match="[Ss]uspended"):
            p.resume()


class TestProjectComplete:
    """Completing transitions Active -> Completed (terminal)."""

    def test_complete_changes_status(self) -> None:
        p = _active_project()
        p.complete()
        assert p.status == ProjectStatus.COMPLETED

    def test_complete_emits_event(self) -> None:
        p = _active_project(project_id="p1")
        p.complete()
        events = p.collect_events()
        assert any(isinstance(e, ProjectCompleted) for e in events)

    def test_complete_from_recruiting_raises(self) -> None:
        p = _recruiting_project()
        with pytest.raises(ValueError, match="transition"):
            p.complete()


class TestProjectCancel:
    """Cancelling transitions to Cancelled (terminal)."""

    def test_cancel_from_recruiting(self) -> None:
        p = _recruiting_project()
        p.cancel()
        assert p.status == ProjectStatus.CANCELLED

    def test_cancel_from_active(self) -> None:
        p = _active_project()
        p.cancel()
        assert p.status == ProjectStatus.CANCELLED

    def test_cancel_emits_event(self) -> None:
        p = _active_project(project_id="p1")
        p.cancel()
        events = p.collect_events()
        assert any(isinstance(e, ProjectCancelled) for e in events)

    def test_cancel_from_draft_raises(self) -> None:
        p = _make_project()
        p.collect_events()
        with pytest.raises(ValueError, match="transition"):
            p.cancel()


# =============================================================================
# Applications
# =============================================================================


class TestProjectApply:
    """Submitting an application to a recruiting project."""

    def test_apply_creates_pending_application(self) -> None:
        p = _recruiting_project()
        p.apply(
            application_id="a1",
            applicant_id="u2",
            desired_role=ProjectRole.MEMBER,
            motivation="I want to help.",
            applicant_skills=[SkillTag("python")],
        )
        assert len(p.applications) == 1
        assert p.applications[0].status == ApplicationStatus.PENDING

    def test_apply_emits_application_submitted(self) -> None:
        p = _recruiting_project(project_id="p1")
        p.apply(
            application_id="a1",
            applicant_id="u2",
            desired_role=ProjectRole.MEMBER,
            motivation="Hello.",
            applicant_skills=[],
        )
        events = p.collect_events()
        assert any(isinstance(e, ApplicationSubmitted) for e in events)

    def test_apply_when_not_recruiting_raises(self) -> None:
        p = _make_project()
        p.collect_events()
        with pytest.raises(ValueError, match="[Rr]ecruiting"):
            p.apply(
                application_id="a1",
                applicant_id="u2",
                desired_role=ProjectRole.MEMBER,
                motivation="Hello.",
                applicant_skills=[],
            )

    def test_apply_when_already_member_raises(self) -> None:
        p = _recruiting_project(owner_id="u1")
        with pytest.raises(ValueError, match="already.*member"):
            p.apply(
                application_id="a1",
                applicant_id="u1",  # owner is already a member
                desired_role=ProjectRole.MEMBER,
                motivation="Hello.",
                applicant_skills=[],
            )

    def test_apply_with_pending_application_raises(self) -> None:
        p = _recruiting_project()
        p.apply(
            application_id="a1",
            applicant_id="u2",
            desired_role=ProjectRole.MEMBER,
            motivation="Hello.",
            applicant_skills=[],
        )
        with pytest.raises(ValueError, match="pending application"):
            p.apply(
                application_id="a2",
                applicant_id="u2",
                desired_role=ProjectRole.MEMBER,
                motivation="Again.",
                applicant_skills=[],
            )


# =============================================================================
# Review Applications
# =============================================================================


class TestProjectAcceptApplication:
    """Accepting an application creates a membership."""

    def test_accept_creates_membership(self) -> None:
        p = _recruiting_project()
        p.apply(
            application_id="a1",
            applicant_id="u2",
            desired_role=ProjectRole.MEMBER,
            motivation="Hello.",
            applicant_skills=[],
        )
        p.collect_events()
        p.accept_application(application_id="a1", reviewed_by="owner1")
        # Owner + new member
        active = [m for m in p.memberships if m.is_active]
        assert len(active) == 2
        new_member = [m for m in active if m.user_id == "u2"][0]
        assert new_member.role == ProjectRole.MEMBER

    def test_accept_emits_accepted_and_joined_events(self) -> None:
        p = _recruiting_project(project_id="p1")
        p.apply(
            application_id="a1",
            applicant_id="u2",
            desired_role=ProjectRole.MEMBER,
            motivation="Hello.",
            applicant_skills=[],
        )
        p.collect_events()
        p.accept_application(application_id="a1", reviewed_by="owner1")
        events = p.collect_events()
        types = [type(e) for e in events]
        assert ApplicationAccepted in types
        assert MemberJoined in types

    def test_accept_when_at_max_members_raises(self) -> None:
        p = _recruiting_project(max_members=1)  # owner fills the 1 slot
        p.apply(
            application_id="a1",
            applicant_id="u2",
            desired_role=ProjectRole.MEMBER,
            motivation="Hello.",
            applicant_skills=[],
        )
        with pytest.raises(ValueError, match="max.*member"):
            p.accept_application(application_id="a1", reviewed_by="owner1")

    def test_accept_nonexistent_application_raises(self) -> None:
        p = _recruiting_project()
        with pytest.raises(LookupError, match="not found"):
            p.accept_application(application_id="a999", reviewed_by="owner1")


class TestProjectRejectApplication:
    """Rejecting an application marks it rejected."""

    def test_reject_sets_status(self) -> None:
        p = _recruiting_project()
        p.apply(
            application_id="a1",
            applicant_id="u2",
            desired_role=ProjectRole.MEMBER,
            motivation="Hello.",
            applicant_skills=[],
        )
        p.reject_application(application_id="a1", reviewed_by="owner1")
        assert p.applications[0].status == ApplicationStatus.REJECTED

    def test_reject_emits_event(self) -> None:
        p = _recruiting_project(project_id="p1")
        p.apply(
            application_id="a1",
            applicant_id="u2",
            desired_role=ProjectRole.MEMBER,
            motivation="Hello.",
            applicant_skills=[],
        )
        p.collect_events()
        p.reject_application(application_id="a1", reviewed_by="owner1")
        events = p.collect_events()
        assert any(isinstance(e, ApplicationRejected) for e in events)


# =============================================================================
# Member Management
# =============================================================================


class TestProjectChangeMemberRole:
    """Changing a member's role within the project."""

    def test_change_role_updates_membership(self) -> None:
        p = _recruiting_project()
        # Add a member
        p.apply(
            application_id="a1",
            applicant_id="u2",
            desired_role=ProjectRole.MEMBER,
            motivation="Hi.",
            applicant_skills=[],
        )
        p.accept_application(application_id="a1", reviewed_by="owner1")
        member = [m for m in p.memberships if m.user_id == "u2"][0]
        p.collect_events()

        p.change_member_role(
            membership_id=member.membership_id, new_role=ProjectRole.ADMIN
        )
        assert member.role == ProjectRole.ADMIN

    def test_change_role_emits_event(self) -> None:
        p = _recruiting_project(project_id="p1")
        p.apply(
            application_id="a1",
            applicant_id="u2",
            desired_role=ProjectRole.MEMBER,
            motivation="Hi.",
            applicant_skills=[],
        )
        p.accept_application(application_id="a1", reviewed_by="owner1")
        member = [m for m in p.memberships if m.user_id == "u2"][0]
        p.collect_events()

        p.change_member_role(
            membership_id=member.membership_id, new_role=ProjectRole.ADMIN
        )
        events = p.collect_events()
        assert any(isinstance(e, MemberRoleChanged) for e in events)

    def test_change_owner_role_raises(self) -> None:
        p = _recruiting_project(owner_id="u1")
        owner_membership = [m for m in p.memberships if m.role == ProjectRole.OWNER][0]
        with pytest.raises(ValueError, match="[Oo]wner"):
            p.change_member_role(
                membership_id=owner_membership.membership_id,
                new_role=ProjectRole.ADMIN,
            )

    def test_change_role_nonexistent_membership_raises(self) -> None:
        p = _recruiting_project()
        with pytest.raises(LookupError, match="not found"):
            p.change_member_role(membership_id="m999", new_role=ProjectRole.ADMIN)


class TestProjectRemoveMember:
    """Removing a member deactivates their membership."""

    def test_remove_deactivates_membership(self) -> None:
        p = _recruiting_project()
        p.apply(
            application_id="a1",
            applicant_id="u2",
            desired_role=ProjectRole.MEMBER,
            motivation="Hi.",
            applicant_skills=[],
        )
        p.accept_application(application_id="a1", reviewed_by="owner1")
        member = [m for m in p.memberships if m.user_id == "u2"][0]
        p.collect_events()

        p.remove_member(membership_id=member.membership_id)
        assert member.is_active is False

    def test_remove_emits_event(self) -> None:
        p = _recruiting_project(project_id="p1")
        p.apply(
            application_id="a1",
            applicant_id="u2",
            desired_role=ProjectRole.MEMBER,
            motivation="Hi.",
            applicant_skills=[],
        )
        p.accept_application(application_id="a1", reviewed_by="owner1")
        member = [m for m in p.memberships if m.user_id == "u2"][0]
        p.collect_events()

        p.remove_member(membership_id=member.membership_id)
        events = p.collect_events()
        assert any(isinstance(e, MemberRemoved) for e in events)

    def test_remove_owner_raises(self) -> None:
        p = _recruiting_project(owner_id="u1")
        owner_membership = [m for m in p.memberships if m.role == ProjectRole.OWNER][0]
        with pytest.raises(ValueError, match="[Oo]wner"):
            p.remove_member(membership_id=owner_membership.membership_id)

    def test_remove_nonexistent_membership_raises(self) -> None:
        p = _recruiting_project()
        with pytest.raises(LookupError, match="not found"):
            p.remove_member(membership_id="m999")


# =============================================================================
# Event collection
# =============================================================================


class TestProjectEventCollection:
    """collect_events() returns and clears uncommitted events."""

    def test_collect_events_returns_and_clears(self) -> None:
        p = _make_project()
        events = p.collect_events()
        assert len(events) >= 1  # at least ProjectCreated
        assert p.collect_events() == []  # cleared
