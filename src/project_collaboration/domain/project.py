"""Project aggregate root."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from project_collaboration.domain.application_form import (
    ApplicationForm,
    ApplicationStatus,
)
from project_collaboration.domain.events import (
    ApplicationAccepted,
    ApplicationRejected,
    ApplicationSubmitted,
    DomainEvent,
    MemberJoined,
    MemberRemoved,
    MemberRoleChanged,
    ProjectActivated,
    ProjectCancelled,
    ProjectCompleted,
    ProjectCreated,
    ProjectPublished,
    ProjectResumed,
    ProjectSuspended,
    ProjectUpdated,
)
from project_collaboration.domain.membership import Membership
from project_collaboration.domain.project_status import ProjectStatus
from project_collaboration.domain.role import ProjectRole
from project_collaboration.domain.skill_tag import SkillTag

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 5000


class Project:
    """Aggregate root for a collaborative project."""

    def __init__(
        self,
        project_id: str,
        title: str,
        description: str,
        owner_id: str,
        required_skills: list[SkillTag],
        max_members: int | None = None,
        docs_repo_url: str | None = None,
    ) -> None:
        if len(title) < MIN_TITLE_LENGTH or len(title) > MAX_TITLE_LENGTH:
            raise ValueError(
                f"Title must be between {MIN_TITLE_LENGTH} and {MAX_TITLE_LENGTH} characters"
            )
        if len(description) > MAX_DESCRIPTION_LENGTH:
            raise ValueError(
                f"Description must not exceed {MAX_DESCRIPTION_LENGTH} characters"
            )

        self.project_id = project_id
        self.title = title
        self.description = description
        self.owner_id = owner_id
        self.required_skills = list(required_skills)
        self.max_members = max_members
        self.docs_repo_url = docs_repo_url
        self.status = ProjectStatus.DRAFT
        self.created_at: datetime = datetime.now(timezone.utc)
        self.previous_status: ProjectStatus | None = None

        self.memberships: list[Membership] = []
        self.applications: list[ApplicationForm] = []
        self._events: list[DomainEvent] = []

        # Create owner membership
        owner_membership = Membership(
            membership_id=str(uuid.uuid4()),
            user_id=owner_id,
            project_id=project_id,
            role=ProjectRole.OWNER,
        )
        self.memberships.append(owner_membership)

        self._emit(
            ProjectCreated(
                project_id=project_id,
                owner_id=owner_id,
                title=title,
            )
        )

    # -------------------------------------------------------------------------
    # Event helpers
    # -------------------------------------------------------------------------

    def collect_events(self) -> list[DomainEvent]:
        """Return and clear uncommitted domain events."""
        events = list(self._events)
        self._events.clear()
        return events

    def _emit(self, event: DomainEvent) -> None:
        self._events.append(event)

    # -------------------------------------------------------------------------
    # Authorization queries
    # -------------------------------------------------------------------------

    def is_owner(self, user_id: str) -> bool:
        """Return True if the user is the project Owner."""
        return self.owner_id == user_id

    def find_membership_by_user_id(self, user_id: str) -> Membership | None:
        """Return the active membership for a user, or None."""
        for m in self.memberships:
            if m.user_id == user_id and m.is_active:
                return m
        return None

    def has_management_rights(self, user_id: str) -> bool:
        """Return True if the user has an active membership with management rights."""
        membership = self.find_membership_by_user_id(user_id)
        return membership is not None and membership.role.has_management_rights()

    # -------------------------------------------------------------------------
    # Status transitions
    # -------------------------------------------------------------------------

    def _transition_to(self, target: ProjectStatus) -> None:
        if not self.status.can_transition_to(target):
            raise ValueError(
                f"Cannot transition from {self.status.value} to {target.value}"
            )
        self.status = target

    def publish(self) -> None:
        """Draft -> Recruiting."""
        self._transition_to(ProjectStatus.RECRUITING)
        self._emit(ProjectPublished(project_id=self.project_id))

    def activate(self) -> None:
        """Recruiting -> Active."""
        self._transition_to(ProjectStatus.ACTIVE)
        self._emit(ProjectActivated(project_id=self.project_id))

    def suspend(self) -> None:
        """Recruiting/Active -> Suspended. Remembers previous status."""
        previous = self.status
        self._transition_to(ProjectStatus.SUSPENDED)
        self.previous_status = previous
        self._emit(ProjectSuspended(project_id=self.project_id))

    def resume(self) -> None:
        """Suspended -> previous status (Recruiting or Active)."""
        if self.status != ProjectStatus.SUSPENDED:
            raise ValueError("Can only resume from Suspended status")
        if self.previous_status is None:
            raise ValueError("No previous status to resume to")
        self._transition_to(self.previous_status)
        self.previous_status = None
        self._emit(ProjectResumed(project_id=self.project_id))

    def complete(self) -> None:
        """Active -> Completed (terminal)."""
        self._transition_to(ProjectStatus.COMPLETED)
        self._emit(ProjectCompleted(project_id=self.project_id))

    def cancel(self) -> None:
        """Recruiting/Active/Suspended -> Cancelled (terminal)."""
        self._transition_to(ProjectStatus.CANCELLED)
        self._emit(ProjectCancelled(project_id=self.project_id))

    # -------------------------------------------------------------------------
    # Applications
    # -------------------------------------------------------------------------

    def apply(
        self,
        application_id: str,
        applicant_id: str,
        desired_role: ProjectRole,
        motivation: str,
        applicant_skills: list[SkillTag],
    ) -> None:
        """Submit an application to join this project."""
        if self.status != ProjectStatus.RECRUITING:
            raise ValueError(
                "Applications are only accepted when project is Recruiting"
            )

        # Check if user is already an active member
        if any(m.user_id == applicant_id and m.is_active for m in self.memberships):
            raise ValueError("User is already a member of this project")

        # Check for existing pending application
        if any(
            a.applicant_id == applicant_id and a.status == ApplicationStatus.PENDING
            for a in self.applications
        ):
            raise ValueError("User already has a pending application for this project")

        form = ApplicationForm(
            application_id=application_id,
            applicant_id=applicant_id,
            project_id=self.project_id,
            desired_role=desired_role,
            motivation=motivation,
            applicant_skills=applicant_skills,
        )
        self.applications.append(form)
        self._emit(
            ApplicationSubmitted(
                application_id=application_id,
                project_id=self.project_id,
                applicant_id=applicant_id,
            )
        )

    def _find_application(self, application_id: str) -> ApplicationForm:
        for app in self.applications:
            if app.application_id == application_id:
                return app
        raise LookupError(f"Application {application_id} not found")

    def accept_application(self, application_id: str, reviewed_by: str) -> None:
        """Accept a pending application, creating a new membership."""
        app = self._find_application(application_id)

        # Check max_members
        active_count = sum(1 for m in self.memberships if m.is_active)
        if self.max_members is not None and active_count >= self.max_members:
            raise ValueError(f"Project has reached max members ({self.max_members})")

        app.accept(reviewed_by=reviewed_by)

        membership_id = str(uuid.uuid4())
        new_membership = Membership(
            membership_id=membership_id,
            user_id=app.applicant_id,
            project_id=self.project_id,
            role=app.desired_role,
        )
        self.memberships.append(new_membership)

        self._emit(
            ApplicationAccepted(
                application_id=application_id,
                project_id=self.project_id,
                applicant_id=app.applicant_id,
            )
        )
        self._emit(
            MemberJoined(
                membership_id=membership_id,
                project_id=self.project_id,
                user_id=app.applicant_id,
                role=app.desired_role,
            )
        )

    def reject_application(self, application_id: str, reviewed_by: str) -> None:
        """Reject a pending application."""
        app = self._find_application(application_id)
        app.reject(reviewed_by=reviewed_by)
        self._emit(
            ApplicationRejected(
                application_id=application_id,
                project_id=self.project_id,
                applicant_id=app.applicant_id,
            )
        )

    # -------------------------------------------------------------------------
    # Member management
    # -------------------------------------------------------------------------

    def _find_membership(self, membership_id: str) -> Membership:
        for m in self.memberships:
            if m.membership_id == membership_id:
                return m
        raise LookupError(f"Membership {membership_id} not found")

    def change_member_role(self, membership_id: str, new_role: ProjectRole) -> None:
        """Change a member's role. Cannot change the Owner's role."""
        member = self._find_membership(membership_id)
        if member.role == ProjectRole.OWNER:
            raise ValueError("Cannot change the Owner's role")
        member.change_role(new_role)
        self._emit(
            MemberRoleChanged(
                membership_id=membership_id,
                project_id=self.project_id,
                new_role=new_role,
            )
        )

    def remove_member(self, membership_id: str) -> None:
        """Remove a member by deactivating their membership."""
        member = self._find_membership(membership_id)
        if member.role == ProjectRole.OWNER:
            raise ValueError("Cannot remove the Owner from the project")
        member.deactivate()
        self._emit(
            MemberRemoved(
                membership_id=membership_id,
                project_id=self.project_id,
                user_id=member.user_id,
            )
        )

    # -------------------------------------------------------------------------
    # Project details update
    # -------------------------------------------------------------------------

    def update(
        self,
        title: str,
        description: str,
        required_skills: list[SkillTag],
        max_members: int | None,
    ) -> None:
        """Update project details. Only owner can call this."""
        if len(title) < MIN_TITLE_LENGTH or len(title) > MAX_TITLE_LENGTH:
            raise ValueError(
                f"Title must be between {MIN_TITLE_LENGTH} and {MAX_TITLE_LENGTH} characters"
            )
        if len(description) > MAX_DESCRIPTION_LENGTH:
            raise ValueError(
                f"Description must not exceed {MAX_DESCRIPTION_LENGTH} characters"
            )

        updated_fields: list[str] = []
        if self.title != title:
            self.title = title
            updated_fields.append("title")
        if self.description != description:
            self.description = description
            updated_fields.append("description")
        if self.max_members != max_members:
            self.max_members = max_members
            updated_fields.append("max_members")

        new_skills = set(required_skills)
        old_skills = set(self.required_skills)
        if new_skills != old_skills:
            self.required_skills = list(required_skills)
            updated_fields.append("required_skills")

        if updated_fields:
            self._emit(
                ProjectUpdated(
                    project_id=self.project_id, updated_fields=updated_fields
                )
            )
