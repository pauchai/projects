"""Pydantic schemas for Cohort Learning API request/response serialization."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class FormCohortRequest(BaseModel):
    """POST /cohorts"""

    cohort_id: str
    module_id: str


class EnrolLearnerRequest(BaseModel):
    """POST /cohorts/{cohort_id}/learners"""

    membership_id: str
    learner_id: str


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class CohortMembershipResponse(BaseModel):
    """Serialized CohortMembership entity."""

    membership_id: str
    learner_id: str
    cohort_id: str
    role: str
    is_active: bool
    joined_at: datetime


class CohortResponse(BaseModel):
    """Serialized LearningCohort aggregate."""

    cohort_id: str
    master_id: str
    module_id: str
    status: str
    formed_at: datetime
    memberships: list[CohortMembershipResponse]


class MessageResponse(BaseModel):
    """Generic success/info response."""

    message: str
