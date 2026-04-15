"""Topic Expert entity — learner who achieved topic-level mastery."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class TopicExpert:
    """
    A learner who has achieved Topic Competency and is authorized to help
    other learners with that specific topic.

    Topic Expert status is earned per-topic — a learner can be an expert in
    Topic A while still a regular learner in Topic B. The status is granted
    immediately upon passing Competency Validation for the topic.

    Business rules:
    - Topic Expert status is permanent (cannot be revoked under normal circumstances)
    - Experts from graduated cohorts can return to help new cohorts
    - One learner can be an expert in multiple topics
    - Expert status is topic-specific and version-specific
    """

    expert_id: str
    learner_id: str
    topic_id: str
    cohort_id: str  # cohort where status was earned
    validated_at: datetime
    validator_id: str  # Master or Module Curator who approved

    def __eq__(self, other: object) -> bool:
        """Topic Experts are identified by expert_id."""
        if not isinstance(other, TopicExpert):
            return NotImplemented
        return self.expert_id == other.expert_id

    def __hash__(self) -> int:
        return hash(self.expert_id)
