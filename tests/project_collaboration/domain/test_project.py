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
    ProjectUpdated,
)
from project_collaboration.domain.application_form import ApplicationStatus
from tests.project_collaboration.factories import (
    make_project,
    make_recruiting_project,
    make_active_project,
)


# =============================================================================
# Project creation
# =============================================================================


class TestProjectCreation:
    def test_creates_project_in_draft_status(self) -> None:
        p = make_project()
        assert p.status == ProjectStatus.DRAFT

    def test_stores_basic_attributes(self) -> None:
        p = make_project(
            project_id="abc",
            title="My Title",
            description="My Desc.",
            owner_id="u1",
        )
        assert p.project_id == "abc"
        assert p.title == "My Title"
        assert p.description == "My Desc."
        assert p.owner_id == "u1"

    def test_stores_required_skills(self) -> None:
        skills = [SkillTag("python"), SkillTag("docker")]
        p = make_project(required_skills=skills)
        assert p.required_skills == skills

    def test_default_max_members_is_none(self) -> None:
        p = make_project()
        assert p.max_members is None

    def test_custom_max_members(self) -> None:
        p = make_project(max_members=5)
        assert p.max_members == 5

    def test_creates_owner_membership(self) -> None:
        p = make_project(owner_id="u1")
        assert len(p.memberships) == 1
        m = p.memberships[0]
        assert m.user_id == "u1"
        assert m.role == ProjectRole.OWNER
        assert m.is_active is True

    def test_sets_created_at_timestamp(self) -> None:
        before = datetime.now(timezone.utc)
        p = make_project()
        after = datetime.now(timezone.utc)
        assert before <= p.created_at <= after

    def test_emits_project_created_event(self) -> None:
        p = make_project(project_id="p1", owner_id="u1", title="Alpha")
        events = p.collect_events()
        assert len(events) == 1
        event = events[0]
        assert isinstance(event, ProjectCreated)
        assert event.project_id == "p1"
        assert event.owner_id == "u1"
        assert event.title == "Alpha"


class TestProjectCreationValidation:
    def test_title_too_short_raises(self) -> None:
        with pytest.raises(ValueError, match="3.*200"):
            make_project(title="ab")

    def test_title_too_long_raises(self) -> None:
        with pytest.raises(ValueError, match="3.*200"):
            make_project(title="x" * 201)

    def test_title_at_min_boundary(self) -> None:
        p = make_project(title="abc")
        assert p.title == "abc"

    def test_title_at_max_boundary(self) -> None:
        p = make_project(title="x" * 200)
        assert len(p.title) == 200

    def test_description_too_long_raises(self) -> None:
        with pytest.raises(ValueError, match="5000"):
            make_project(description="x" * 5001)

    def test_description_at_max_boundary(self) -> None:
        p = make_project(description="x" * 5000)
        assert len(p.description) == 5000


# =============================================================================
# Authorization queries
# =============================================================================


class TestAuthorizationQueries:
    def test_is_owner_returns_true_for_owner(self) -> None:
        p = make_project(owner_id="u1")
        assert p.is_owner("u1") is True

    def test_is_owner_returns_false_for_non_owner(self) -> None:
        p = make_project(owner_id="u1")
        assert p.is_owner("u2") is False

    def test_find_membership_by_user_id_returns_owner(self) -> None:
        p = make_project(owner_id="u1")
        m = p.find_membership_by_user_id("u1")
        assert m is not None
        assert m.role == ProjectRole.OWNER

    def test_find_membership_by_user_id_returns_none_for_stranger(self) -> None:
        p = make_project()
        assert p.find_membership_by_user_id("stranger") is None

    def test_has_management_rights_true_for_owner(self) -> None:
        p = make_project(owner_id="u1")
        assert p.has_management_rights("u1") is True

    def test_has_management_rights_false_for_stranger(self) -> None:
        p = make_project()
        assert p.has_management_rights("stranger") is False


# =============================================================================
# Status transitions
# =============================================================================


class TestPublish:
    def test_transitions_draft_to_recruiting(self) -> None:
        p = make_project()
        p.publish()
        assert p.status == ProjectStatus.RECRUITING

    def test_emits_project_published_event(self) -> None:
        p = make_project(project_id="p1")
        p.collect_events()  # clear creation event
        p.publish()
        events = p.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], ProjectPublished)
        assert events[0].project_id == "p1"

    def test_raises_when_not_in_draft(self) -> None:
        p = make_recruiting_project()
        with pytest.raises(ValueError, match="transition"):
            p.publish()


class TestActivate:
    def test_transitions_recruiting_to_active(self) -> None:
        p = make_recruiting_project()
        p.activate()
        assert p.status == ProjectStatus.ACTIVE

    def test_emits_project_activated_event(self) -> None:
        p = make_recruiting_project(project_id="p1")
        p.activate()
        events = p.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], ProjectActivated)

    def test_raises_when_not_recruiting(self) -> None:
        p = make_project()
        with pytest.raises(ValueError, match="transition"):
            p.activate()


class TestSuspend:
    def test_suspends_recruiting_project(self) -> None:
        p = make_recruiting_project()
        p.suspend()
        assert p.status == ProjectStatus.SUSPENDED

    def test_suspends_active_project(self) -> None:
        p = make_active_project()
        p.suspend()
        assert p.status == ProjectStatus.SUSPENDED

    def test_emits_project_suspended_event(self) -> None:
        p = make_recruiting_project(project_id="p1")
        p.suspend()
        events = p.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], ProjectSuspended)

    def test_raises_when_in_draft(self) -> None:
        p = make_project()
        with pytest.raises(ValueError, match="transition"):
            p.suspend()


class TestResume:
    def test_resumes_to_recruiting(self) -> None:
        p = make_recruiting_project()
        p.suspend()
        p.resume()
        assert p.status == ProjectStatus.RECRUITING

    def test_resumes_to_active(self) -> None:
        p = make_active_project()
        p.suspend()
        p.resume()
        assert p.status == ProjectStatus.ACTIVE

    def test_emits_project_resumed_event(self) -> None:
        p = make_recruiting_project(project_id="p1")
        p.suspend()
        p.collect_events()
        p.resume()
        events = p.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], ProjectResumed)

    def test_raises_when_not_suspended(self) -> None:
        p = make_recruiting_project()
        with pytest.raises(ValueError, match="[Ss]uspended"):
            p.resume()


class TestComplete:
    def test_transitions_active_to_completed(self) -> None:
        p = make_active_project()
        p.complete()
        assert p.status == ProjectStatus.COMPLETED

    def test_emits_project_completed_event(self) -> None:
        p = make_active_project(project_id="p1")
        p.complete()
        events = p.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], ProjectCompleted)

    def test_raises_when_not_active(self) -> None:
        p = make_recruiting_project()
        with pytest.raises(ValueError, match="transition"):
            p.complete()


class TestCancel:
    def test_cancels_recruiting_project(self) -> None:
        p = make_recruiting_project()
        p.cancel()
        assert p.status == ProjectStatus.CANCELLED

    def test_cancels_active_project(self) -> None:
        p = make_active_project()
        p.cancel()
        assert p.status == ProjectStatus.CANCELLED

    def test_emits_project_cancelled_event(self) -> None:
        p = make_recruiting_project(project_id="p1")
        p.cancel()
        events = p.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], ProjectCancelled)

    def test_raises_when_in_draft(self) -> None:
        p = make_project()
        with pytest.raises(ValueError, match="transition"):
            p.cancel()

    def test_completed_is_terminal(self) -> None:
        p = make_active_project()
        p.complete()
        with pytest.raises(ValueError, match="transition"):
            p.cancel()

    def test_cancelled_is_terminal(self) -> None:
        p = make_recruiting_project()
        p.cancel()
        with pytest.raises(ValueError, match="transition"):
            p.publish()


# =============================================================================
# Applications
# =============================================================================


class TestApply:
    def test_adds_pending_application(self) -> None:
        p = make_recruiting_project()
        p.apply(
            application_id="a1",
            applicant_id="u2",
            desired_role=ProjectRole.MEMBER,
            motivation="I want to join.",
            applicant_skills=[SkillTag("python")],
        )
        assert len(p.applications) == 1
        app = p.applications[0]
        assert app.application_id == "a1"
        assert app.applicant_id == "u2"
        assert app.status == ApplicationStatus.PENDING

    def test_emits_application_submitted_event(self) -> None:
        p = make_recruiting_project(project_id="p1")
        p.apply(
            application_id="a1",
            applicant_id="u2",
            desired_role=ProjectRole.MEMBER,
            motivation="Motivation.",
            applicant_skills=[],
        )
        events = p.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], ApplicationSubmitted)
        assert events[0].application_id == "a1"

    def test_raises_when_not_recruiting(self) -> None:
        p = make_project()
        with pytest.raises(ValueError, match="[Rr]ecruiting"):
            p.apply(
                application_id="a1",
                applicant_id="u2",
                desired_role=ProjectRole.MEMBER,
                motivation="Hi.",
                applicant_skills=[],
            )

    def test_raises_when_already_member(self) -> None:
        p = make_recruiting_project(owner_id="u1")
        with pytest.raises(ValueError, match="already.*member"):
            p.apply(
                application_id="a1",
                applicant_id="u1",
                desired_role=ProjectRole.MEMBER,
                motivation="Hi.",
                applicant_skills=[],
            )

    def test_raises_when_duplicate_pending_application(self) -> None:
        p = make_recruiting_project()
        p.apply(
            application_id="a1",
            applicant_id="u2",
            desired_role=ProjectRole.MEMBER,
            motivation="First.",
            applicant_skills=[],
        )
        with pytest.raises(ValueError, match="pending"):
            p.apply(
                application_id="a2",
                applicant_id="u2",
                desired_role=ProjectRole.MEMBER,
                motivation="Second.",
                applicant_skills=[],
            )


class TestAcceptApplication:
    def _project_with_application(self, **overrides: object) -> Project:
        p = make_recruiting_project(**overrides)
        p.apply(
            application_id="a1",
            applicant_id="u2",
            desired_role=ProjectRole.MEMBER,
            motivation="I want to join.",
            applicant_skills=[SkillTag("python")],
        )
        p.collect_events()
        return p

    def test_accepts_application(self) -> None:
        p = self._project_with_application()
        p.accept_application(application_id="a1", reviewed_by="owner1")
        app = p.applications[0]
        assert app.status == ApplicationStatus.ACCEPTED

    def test_creates_membership(self) -> None:
        p = self._project_with_application()
        p.accept_application(application_id="a1", reviewed_by="owner1")
        active = [m for m in p.memberships if m.is_active]
        assert len(active) == 2
        new_member = [m for m in active if m.user_id == "u2"][0]
        assert new_member.role == ProjectRole.MEMBER

    def test_emits_accepted_and_joined_events(self) -> None:
        p = self._project_with_application(project_id="p1")
        p.accept_application(application_id="a1", reviewed_by="owner1")
        events = p.collect_events()
        assert len(events) == 2
        assert isinstance(events[0], ApplicationAccepted)
        assert isinstance(events[1], MemberJoined)

    def test_raises_when_application_not_found(self) -> None:
        p = self._project_with_application()
        with pytest.raises(LookupError, match="not found"):
            p.accept_application(application_id="a999", reviewed_by="owner1")

    def test_raises_when_at_max_members(self) -> None:
        p = self._project_with_application(max_members=1)
        with pytest.raises(ValueError, match="max.*member"):
            p.accept_application(application_id="a1", reviewed_by="owner1")


class TestRejectApplication:
    def test_rejects_application(self) -> None:
        p = make_recruiting_project()
        p.apply(
            application_id="a1",
            applicant_id="u2",
            desired_role=ProjectRole.MEMBER,
            motivation="Hi.",
            applicant_skills=[],
        )
        p.collect_events()
        p.reject_application(application_id="a1", reviewed_by="owner1")
        assert p.applications[0].status == ApplicationStatus.REJECTED

    def test_emits_application_rejected_event(self) -> None:
        p = make_recruiting_project(project_id="p1")
        p.apply(
            application_id="a1",
            applicant_id="u2",
            desired_role=ProjectRole.MEMBER,
            motivation="Hi.",
            applicant_skills=[],
        )
        p.collect_events()
        p.reject_application(application_id="a1", reviewed_by="owner1")
        events = p.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], ApplicationRejected)


# =============================================================================
# Member management
# =============================================================================


class TestChangeMemberRole:
    def _project_with_member(self) -> tuple[Project, str]:
        p = make_recruiting_project()
        p.apply(
            application_id="a1",
            applicant_id="u2",
            desired_role=ProjectRole.MEMBER,
            motivation="Hi.",
            applicant_skills=[],
        )
        p.accept_application(application_id="a1", reviewed_by="owner1")
        p.collect_events()
        member = [m for m in p.memberships if m.user_id == "u2"][0]
        return p, member.membership_id

    def test_changes_role(self) -> None:
        p, mid = self._project_with_member()
        p.change_member_role(membership_id=mid, new_role=ProjectRole.ADMIN)
        member = [m for m in p.memberships if m.membership_id == mid][0]
        assert member.role == ProjectRole.ADMIN

    def test_emits_member_role_changed_event(self) -> None:
        p, mid = self._project_with_member()
        p.change_member_role(membership_id=mid, new_role=ProjectRole.ADMIN)
        events = p.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], MemberRoleChanged)
        assert events[0].new_role == ProjectRole.ADMIN

    def test_raises_when_changing_owner_role(self) -> None:
        p, _ = self._project_with_member()
        owner_m = [m for m in p.memberships if m.role == ProjectRole.OWNER][0]
        with pytest.raises(ValueError, match="[Oo]wner"):
            p.change_member_role(
                membership_id=owner_m.membership_id, new_role=ProjectRole.ADMIN
            )

    def test_raises_when_membership_not_found(self) -> None:
        p, _ = self._project_with_member()
        with pytest.raises(LookupError, match="not found"):
            p.change_member_role(membership_id="m999", new_role=ProjectRole.ADMIN)


class TestRemoveMember:
    def _project_with_member(self) -> tuple[Project, str]:
        p = make_recruiting_project()
        p.apply(
            application_id="a1",
            applicant_id="u2",
            desired_role=ProjectRole.MEMBER,
            motivation="Hi.",
            applicant_skills=[],
        )
        p.accept_application(application_id="a1", reviewed_by="owner1")
        p.collect_events()
        member = [m for m in p.memberships if m.user_id == "u2"][0]
        return p, member.membership_id

    def test_deactivates_member(self) -> None:
        p, mid = self._project_with_member()
        p.remove_member(membership_id=mid)
        member = [m for m in p.memberships if m.membership_id == mid][0]
        assert member.is_active is False

    def test_emits_member_removed_event(self) -> None:
        p, mid = self._project_with_member()
        p.remove_member(membership_id=mid)
        events = p.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], MemberRemoved)
        assert events[0].user_id == "u2"

    def test_raises_when_removing_owner(self) -> None:
        p, _ = self._project_with_member()
        owner_m = [m for m in p.memberships if m.role == ProjectRole.OWNER][0]
        with pytest.raises(ValueError, match="[Oo]wner"):
            p.remove_member(membership_id=owner_m.membership_id)

    def test_raises_when_membership_not_found(self) -> None:
        p, _ = self._project_with_member()
        with pytest.raises(LookupError, match="not found"):
            p.remove_member(membership_id="m999")


# =============================================================================
# Project update
# =============================================================================


class TestProjectUpdate:
    def test_updates_title(self) -> None:
        p = make_project(title="Original Title")
        new_skills = [SkillTag("python")]

        p.update(
            title="New Title",
            description="Updated desc",
            required_skills=new_skills,
            max_members=5,
        )

        assert p.title == "New Title"

    def test_updates_description(self) -> None:
        p = make_project(description="Original desc")

        p.update(
            title="Same Title",
            description="New description",
            required_skills=[],
            max_members=None,
        )

        assert p.description == "New description"

    def test_updates_required_skills(self) -> None:
        p = make_project(required_skills=[SkillTag("python")])

        p.update(
            title="Title",
            description="desc",
            required_skills=[SkillTag("rust"), SkillTag("go")],
            max_members=None,
        )

        assert p.required_skills == [SkillTag("rust"), SkillTag("go")]

    def test_updates_max_members(self) -> None:
        p = make_project(max_members=None)

        p.update(
            title="Title",
            description="desc",
            required_skills=[],
            max_members=10,
        )

        assert p.max_members == 10

    def test_raises_when_title_too_short(self) -> None:
        p = make_project()
        with pytest.raises(ValueError, match="Title must be between"):
            p.update(
                title="AB",
                description="desc",
                required_skills=[],
                max_members=None,
            )

    def test_raises_when_title_too_long(self) -> None:
        p = make_project()
        with pytest.raises(ValueError, match="Title must be between"):
            p.update(
                title="A" * 201,
                description="desc",
                required_skills=[],
                max_members=None,
            )

    def test_raises_when_description_too_long(self) -> None:
        p = make_project()
        with pytest.raises(ValueError, match="Description must not exceed"):
            p.update(
                title="Title",
                description="A" * 5001,
                required_skills=[],
                max_members=None,
            )

    def test_emits_project_updated_event_when_title_changes(self) -> None:
        p = make_project(title="Old Title")
        p.collect_events()

        p.update(
            title="New Title",
            description="desc",
            required_skills=[],
            max_members=None,
        )

        events = p.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], ProjectUpdated)
        assert events[0].project_id == p.project_id
        assert "title" in events[0].updated_fields

    def test_emits_project_updated_event_when_description_changes(self) -> None:
        p = make_project(description="Old")
        p.collect_events()

        p.update(
            title="Title",
            description="New",
            required_skills=[],
            max_members=None,
        )

        events = p.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], ProjectUpdated)
        assert "description" in events[0].updated_fields

    def test_emits_project_updated_event_when_skills_change(self) -> None:
        p = make_project(required_skills=[SkillTag("python")])
        p.collect_events()

        p.update(
            title="Title",
            description="desc",
            required_skills=[SkillTag("rust")],
            max_members=None,
        )

        events = p.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], ProjectUpdated)
        assert "required_skills" in events[0].updated_fields

    def test_emits_project_updated_event_when_max_members_changes(self) -> None:
        p = make_project(max_members=5)
        p.collect_events()

        p.update(
            title="Title",
            description="desc",
            required_skills=[],
            max_members=10,
        )

        events = p.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], ProjectUpdated)
        assert "max_members" in events[0].updated_fields

    def test_emits_event_with_multiple_fields_when_multiple_change(self) -> None:
        p = make_project(
            title="Old", description="old", max_members=5, required_skills=[]
        )
        p.collect_events()

        p.update(
            title="New",
            description="new",
            required_skills=[],
            max_members=10,
        )

        events = p.collect_events()
        assert len(events) == 1
        assert set(events[0].updated_fields) == {"title", "description", "max_members"}

    def test_no_event_emitted_when_nothing_changes(self) -> None:
        p = make_project(
            title="Same",
            description="same",
            max_members=5,
            required_skills=[SkillTag("python")],
        )
        p.collect_events()

        p.update(
            title="Same",
            description="same",
            required_skills=[SkillTag("python")],
            max_members=5,
        )

        events = p.collect_events()
        assert len(events) == 0

    def test_no_event_emitted_when_only_same_skills_passed(self) -> None:
        p = make_project(required_skills=[SkillTag("python")])
        p.collect_events()

        p.update(
            title="Test Project",
            description="A test project description.",
            required_skills=[SkillTag("python")],
            max_members=None,
        )

        events = p.collect_events()
        assert len(events) == 0
