"""ApplicationForm entity and ApplicationStatus enum."""

from datetime import datetime, timezone
from enum import Enum

from project_collaboration.domain.role import ProjectRole
from project_collaboration.domain.skill_tag import SkillTag

MAX_MOTIVATION_LENGTH = 2000


class ApplicationStatus(Enum):
    """Status of an application to join a project."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class ApplicationForm:
    """A user's request to join a project."""

    def __init__(
        self,
        application_id: str,
        applicant_id: str,
        project_id: str,
        desired_role: ProjectRole,
        motivation: str,
        applicant_skills: list[SkillTag],
    ) -> None:
        if desired_role == ProjectRole.OWNER:
            raise ValueError("Desired role cannot be Owner")
        if len(motivation) > MAX_MOTIVATION_LENGTH:
            raise ValueError(
                f"Motivation must not exceed {MAX_MOTIVATION_LENGTH} characters"
            )

        self.application_id = application_id
        self.applicant_id = applicant_id
        self.project_id = project_id
        self.desired_role = desired_role
        self.motivation = motivation
        self.applicant_skills = list(applicant_skills)
        self.status: ApplicationStatus = ApplicationStatus.PENDING
        self.reviewed_by: str | None = None
        self.submitted_at: datetime = datetime.now(timezone.utc)

    def accept(self, reviewed_by: str) -> None:
        """Accept this application. Raises if not pending."""
        self._ensure_pending()
        self.status = ApplicationStatus.ACCEPTED
        self.reviewed_by = reviewed_by

    def reject(self, reviewed_by: str) -> None:
        """Reject this application. Raises if not pending."""
        self._ensure_pending()
        self.status = ApplicationStatus.REJECTED
        self.reviewed_by = reviewed_by

    def _ensure_pending(self) -> None:
        if self.status != ApplicationStatus.PENDING:
            raise ValueError(
                f"Application is not pending (current: {self.status.value})"
            )
