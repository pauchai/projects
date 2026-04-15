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
