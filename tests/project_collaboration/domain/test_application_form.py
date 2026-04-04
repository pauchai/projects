"""Tests for ApplicationForm entity and ApplicationStatus enum."""

import pytest
from datetime import datetime, timezone

from project_collaboration.domain.application_form import (
    ApplicationForm,
    ApplicationStatus,
)
from project_collaboration.domain.role import ProjectRole
from project_collaboration.domain.skill_tag import SkillTag


class TestApplicationStatusEnum:
    """ApplicationStatus has three values."""

    def test_has_pending_value(self) -> None:
        assert ApplicationStatus.PENDING.value == "pending"

    def test_has_accepted_value(self) -> None:
        assert ApplicationStatus.ACCEPTED.value == "accepted"

    def test_has_rejected_value(self) -> None:
        assert ApplicationStatus.REJECTED.value == "rejected"

    def test_has_exactly_three_members(self) -> None:
        assert len(ApplicationStatus) == 3


class TestApplicationFormCreation:
    """ApplicationForm is created with Pending status and validated fields."""

    def test_creates_with_pending_status(self) -> None:
        form = ApplicationForm(
            application_id="a1",
            applicant_id="u1",
            project_id="p1",
            desired_role=ProjectRole.MEMBER,
            motivation="I want to help.",
            applicant_skills=[SkillTag("python")],
        )
        assert form.status == ApplicationStatus.PENDING

    def test_stores_identity_fields(self) -> None:
        form = ApplicationForm(
            application_id="a1",
            applicant_id="u1",
            project_id="p1",
            desired_role=ProjectRole.MEMBER,
            motivation="I want to help.",
            applicant_skills=[SkillTag("python")],
        )
        assert form.application_id == "a1"
        assert form.applicant_id == "u1"
        assert form.project_id == "p1"

    def test_stores_desired_role(self) -> None:
        form = ApplicationForm(
            application_id="a1",
            applicant_id="u1",
            project_id="p1",
            desired_role=ProjectRole.ADMIN,
            motivation="I can manage.",
            applicant_skills=[],
        )
        assert form.desired_role == ProjectRole.ADMIN

    def test_stores_motivation_and_skills(self) -> None:
        skills = [SkillTag("python"), SkillTag("design")]
        form = ApplicationForm(
            application_id="a1",
            applicant_id="u1",
            project_id="p1",
            desired_role=ProjectRole.MEMBER,
            motivation="Excited to join!",
            applicant_skills=skills,
        )
        assert form.motivation == "Excited to join!"
        assert form.applicant_skills == skills

    def test_reviewed_by_is_none_initially(self) -> None:
        form = ApplicationForm(
            application_id="a1",
            applicant_id="u1",
            project_id="p1",
            desired_role=ProjectRole.MEMBER,
            motivation="Hello.",
            applicant_skills=[],
        )
        assert form.reviewed_by is None

    def test_has_submitted_at_timestamp(self) -> None:
        before = datetime.now(timezone.utc)
        form = ApplicationForm(
            application_id="a1",
            applicant_id="u1",
            project_id="p1",
            desired_role=ProjectRole.MEMBER,
            motivation="Hello.",
            applicant_skills=[],
        )
        after = datetime.now(timezone.utc)
        assert before <= form.submitted_at <= after

    def test_desired_role_owner_raises(self) -> None:
        with pytest.raises(ValueError, match="cannot be Owner"):
            ApplicationForm(
                application_id="a1",
                applicant_id="u1",
                project_id="p1",
                desired_role=ProjectRole.OWNER,
                motivation="I want to own it.",
                applicant_skills=[],
            )

    def test_motivation_exceeding_2000_chars_raises(self) -> None:
        with pytest.raises(ValueError, match="2000 characters"):
            ApplicationForm(
                application_id="a1",
                applicant_id="u1",
                project_id="p1",
                desired_role=ProjectRole.MEMBER,
                motivation="x" * 2001,
                applicant_skills=[],
            )


class TestApplicationFormAccept:
    """Accepting an application transitions to Accepted."""

    def test_accept_sets_accepted_status(self) -> None:
        form = _make_form()
        form.accept(reviewed_by="admin1")
        assert form.status == ApplicationStatus.ACCEPTED

    def test_accept_records_reviewer(self) -> None:
        form = _make_form()
        form.accept(reviewed_by="admin1")
        assert form.reviewed_by == "admin1"

    def test_accept_already_accepted_raises(self) -> None:
        form = _make_form()
        form.accept(reviewed_by="admin1")
        with pytest.raises(ValueError, match="not pending"):
            form.accept(reviewed_by="admin2")

    def test_accept_rejected_raises(self) -> None:
        form = _make_form()
        form.reject(reviewed_by="admin1")
        with pytest.raises(ValueError, match="not pending"):
            form.accept(reviewed_by="admin2")


class TestApplicationFormReject:
    """Rejecting an application transitions to Rejected."""

    def test_reject_sets_rejected_status(self) -> None:
        form = _make_form()
        form.reject(reviewed_by="admin1")
        assert form.status == ApplicationStatus.REJECTED

    def test_reject_records_reviewer(self) -> None:
        form = _make_form()
        form.reject(reviewed_by="admin1")
        assert form.reviewed_by == "admin1"

    def test_reject_already_rejected_raises(self) -> None:
        form = _make_form()
        form.reject(reviewed_by="admin1")
        with pytest.raises(ValueError, match="not pending"):
            form.reject(reviewed_by="admin2")

    def test_reject_accepted_raises(self) -> None:
        form = _make_form()
        form.accept(reviewed_by="admin1")
        with pytest.raises(ValueError, match="not pending"):
            form.reject(reviewed_by="admin2")


# --- Helper ---


def _make_form() -> ApplicationForm:
    return ApplicationForm(
        application_id="a1",
        applicant_id="u1",
        project_id="p1",
        desired_role=ProjectRole.MEMBER,
        motivation="I want to help.",
        applicant_skills=[SkillTag("python")],
    )
