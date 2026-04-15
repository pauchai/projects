"""Pydantic schemas for Cohort Learning API request/response serialization."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Request schemas — Cohorts
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
# Request schemas — Practice Tasks
# ---------------------------------------------------------------------------


class CreatePracticeTaskRequest(BaseModel):
    """POST /cohorts/{cohort_id}/tasks"""

    task_id: str
    topic_id: str
    title: str
    description: str = ""


class SubmitTaskSolutionRequest(BaseModel):
    """POST /cohorts/{cohort_id}/tasks/{task_id}/submissions"""

    submission_id: str
    content: str


# ---------------------------------------------------------------------------
# Request schemas — Peer Reviews
# ---------------------------------------------------------------------------


class ReviewScoreInput(BaseModel):
    """A single criterion score within a review."""

    criterion: str
    score: int
    comment: str = ""


class SubmitPeerReviewRequest(BaseModel):
    """POST /cohorts/{cohort_id}/tasks/{task_id}/submissions/{submission_id}/reviews"""

    review_id: str
    scores: list[ReviewScoreInput]
    overall_feedback: str = ""


# ---------------------------------------------------------------------------
# Response schemas — Cohorts
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


# ---------------------------------------------------------------------------
# Response schemas — Practice Tasks
# ---------------------------------------------------------------------------


class TaskSubmissionResponse(BaseModel):
    """Serialized TaskSubmission entity."""

    submission_id: str
    task_id: str
    learner_id: str
    content: str
    status: str
    submitted_at: datetime


class PracticeTaskResponse(BaseModel):
    """Serialized PracticeTask aggregate."""

    task_id: str
    cohort_id: str
    topic_id: str
    creator_id: str
    title: str
    description: str
    status: str
    created_at: datetime
    submissions: list[TaskSubmissionResponse]


# ---------------------------------------------------------------------------
# Response schemas — Peer Reviews
# ---------------------------------------------------------------------------


class ReviewScoreResponse(BaseModel):
    """Serialized ReviewScore value object."""

    criterion: str
    score: int
    comment: str


class PeerReviewResponse(BaseModel):
    """Serialized PeerReview aggregate."""

    review_id: str
    submission_id: str
    reviewer_id: str
    task_id: str
    cohort_id: str
    status: str
    overall_feedback: str
    created_at: datetime
    reviewed_at: datetime | None
    scores: list[ReviewScoreResponse]


# ---------------------------------------------------------------------------
# Generic responses
# ---------------------------------------------------------------------------


class MessageResponse(BaseModel):
    """Generic success/info response."""

    message: str
