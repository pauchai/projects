"""Domain events for the Cohort Learning bounded context."""

from dataclasses import dataclass

from shared_kernel.events import DomainEvent


# --- Cohort lifecycle events ---


@dataclass(frozen=True)
class CohortFormed(DomainEvent):
    cohort_id: str
    master_id: str
    module_id: str


@dataclass(frozen=True)
class CohortActivated(DomainEvent):
    cohort_id: str


@dataclass(frozen=True)
class CohortGraduated(DomainEvent):
    cohort_id: str


@dataclass(frozen=True)
class CohortCancelled(DomainEvent):
    cohort_id: str


# --- Membership events ---


@dataclass(frozen=True)
class LearnerEnrolled(DomainEvent):
    cohort_id: str
    membership_id: str
    learner_id: str


@dataclass(frozen=True)
class LearnerRemoved(DomainEvent):
    cohort_id: str
    membership_id: str
    learner_id: str


# --- Progression events ---


@dataclass(frozen=True)
class TopicExpertPromoted(DomainEvent):
    cohort_id: str
    learner_id: str
    topic_id: str


@dataclass(frozen=True)
class CuratorPromoted(DomainEvent):
    cohort_id: str
    learner_id: str
    module_id: str


# --- Competency events ---


@dataclass(frozen=True)
class TopicCompetencyAchieved(DomainEvent):
    cohort_id: str
    learner_id: str
    topic_id: str


@dataclass(frozen=True)
class PracticeTaskCompleted(DomainEvent):
    cohort_id: str
    learner_id: str
    task_id: str
    topic_id: str


# --- Peer review events ---


@dataclass(frozen=True)
class PracticeTaskCreated(DomainEvent):
    task_id: str
    cohort_id: str
    topic_id: str
    creator_id: str
    title: str


@dataclass(frozen=True)
class TaskSubmissionCreated(DomainEvent):
    submission_id: str
    task_id: str
    learner_id: str
    cohort_id: str


@dataclass(frozen=True)
class PeerReviewSubmitted(DomainEvent):
    review_id: str
    submission_id: str
    reviewer_id: str
    task_id: str
    cohort_id: str


# --- Reward events ---


@dataclass(frozen=True)
class ExpertRewardGranted(DomainEvent):
    """Emitted when any reward (XP, badge, credits) is granted to a learner."""

    learner_id: str
    reward_type: str  # 'xp', 'badge', 'credits'
    amount: int | None  # None for badge entries
    cohort_id: str | None


@dataclass(frozen=True)
class HelperMetricsUpdated(DomainEvent):
    """Emitted after a learner's HelperMetrics are updated.

    Used to trigger automatic reward calculations:
    - Reputation recalculation
    - Learning credits milestones (every 10 learners helped → +5%)
    """

    learner_id: str
    cohort_id: str
    learners_helped: int
    tasks_reviewed: int
