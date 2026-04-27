"""Pydantic schemas for Cohort Learning API request/response serialization."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

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
# Request schemas — Partner Progression
# ---------------------------------------------------------------------------


class ValidateTopicCompetencyRequest(BaseModel):
    """POST /cohorts/{cohort_id}/members/{learner_id}/validate-competency"""

    topic_id: str
    knowledge_check_score: int
    mentor_approved: bool


class PromoteToTopicExpertRequest(BaseModel):
    """POST /cohorts/{cohort_id}/members/{learner_id}/promote-expert"""

    expert_id: str
    topic_id: str


class PromoteToModuleCuratorRequest(BaseModel):
    """POST /cohorts/{cohort_id}/members/{learner_id}/promote-curator"""

    curator_id: str
    module_id: str


# ---------------------------------------------------------------------------
# Response schemas — Partner Progression
# ---------------------------------------------------------------------------


class TopicExpertResponse(BaseModel):
    """Serialized TopicExpert entity."""

    expert_id: str
    learner_id: str
    topic_id: str
    cohort_id: str
    validated_at: datetime
    validator_id: str


class HelperMetricsResponse(BaseModel):
    """Serialized HelperMetrics entity."""

    learner_id: str
    cohort_id: str
    learners_helped: int
    questions_answered: int
    tasks_reviewed: int
    average_satisfaction: Decimal | None
    updated_at: datetime


class ModuleCuratorResponse(BaseModel):
    """Serialized ModuleCurator entity."""

    curator_id: str
    learner_id: str
    module_id: str
    cohort_id: str
    promoted_at: datetime
    promoted_by: str


class CompetencyValidationResult(BaseModel):
    """Result of competency validation check."""

    topic_id: str
    is_validated: bool
    missing_steps: list[str]


# ---------------------------------------------------------------------------
# Generic responses
# ---------------------------------------------------------------------------


class MessageResponse(BaseModel):
    """Generic success/info response."""

    message: str


# ---------------------------------------------------------------------------
# Response schemas — Rewards
# ---------------------------------------------------------------------------


class RewardBalanceResponse(BaseModel):
    """Serialized RewardBalance — current accumulated rewards for a learner."""

    learner_id: str
    total_xp: int
    total_credits: int
    badges: list[str]
    reputation_score: int | None


class RewardEntryResponse(BaseModel):
    """Serialized RewardEntry — a single reward ledger entry."""

    entry_id: str
    learner_id: str
    reward_type: str
    amount: int | None
    metadata: dict[str, str]
    granted_at: datetime
    triggering_event: str | None
    cohort_id: str | None


class LeaderboardEntryResponse(BaseModel):
    """A single entry in the cohort XP leaderboard."""

    learner_id: str
    total_xp: int
    rank: int


# ---------------------------------------------------------------------------
# Response schemas — Eligibility Notifications (Stage 17-18)
# ---------------------------------------------------------------------------


class PendingCompetencyValidationResponse(BaseModel):
    """Serialized PendingCompetencyValidation — a learner awaiting knowledge-check."""

    pending_id: str
    learner_id: str
    topic_id: str
    cohort_id: str
    created_at: datetime


class PendingCuratorPromotionResponse(BaseModel):
    """Serialized PendingCuratorPromotion — a learner eligible for curator promotion."""

    pending_id: str
    learner_id: str
    module_id: str
    cohort_id: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Request / Response schemas — Modules & Topics
# ---------------------------------------------------------------------------


class CreateModuleRequest(BaseModel):
    """Request body for POST /modules."""

    module_id: str
    title: str


class AddTopicRequest(BaseModel):
    """Request body for POST /modules/{module_id}/topics."""

    topic_id: str
    title: str
    position: int
    description: str = ""


class TopicResponse(BaseModel):
    """Serialized Topic."""

    topic_id: str
    title: str
    position: int
    description: str


class ModuleResponse(BaseModel):
    """Serialized ModuleProgression with topics."""

    module_id: str
    title: str
    master_id: str
    topics: list[TopicResponse]
    topic_count: int
