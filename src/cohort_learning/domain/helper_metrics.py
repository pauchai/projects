"""Helper Metrics value object — aggregated view of peer helping activity."""

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal


# Curator promotion thresholds (per glossary)
CURATOR_MIN_LEARNERS_HELPED = 3
CURATOR_MIN_TASKS_REVIEWED = 5
CURATOR_MIN_SATISFACTION = Decimal("4.0")


@dataclass(frozen=True)
class HelperMetrics:
    """
    Aggregated view of a Peer Helper's activity and effectiveness.

    Tracks:
    - Total learners helped
    - Questions answered
    - Practice tasks reviewed
    - Average satisfaction rating from helped learners
    - Last update timestamp

    Purpose:
    1. Determine eligibility for Expert Rewards
    2. Qualify for Module Curator promotion
    3. Build reputation score across cohorts
    """

    learner_id: str
    cohort_id: str
    learners_helped: int
    questions_answered: int
    tasks_reviewed: int
    average_satisfaction: Decimal | None  # None if no reviews yet
    updated_at: datetime

    def record_peer_review(
        self, satisfaction_score: Decimal, timestamp: datetime
    ) -> "HelperMetrics":
        """
        Record a peer review submission. Updates tasks_reviewed count and
        recalculates average satisfaction.

        Returns new HelperMetrics instance (immutable).
        """
        new_tasks_reviewed = self.tasks_reviewed + 1

        # Calculate new average satisfaction
        if self.average_satisfaction is None:
            new_avg = satisfaction_score
        else:
            total = self.average_satisfaction * self.tasks_reviewed
            new_avg = (total + satisfaction_score) / new_tasks_reviewed

        return replace(
            self,
            tasks_reviewed=new_tasks_reviewed,
            average_satisfaction=new_avg,
            updated_at=timestamp,
        )

    def record_learner_helped(
        self, helped_learner_id: str, timestamp: datetime
    ) -> "HelperMetrics":
        """
        Record that this helper assisted a new learner.

        Returns new HelperMetrics instance (immutable).
        """
        return replace(
            self,
            learners_helped=self.learners_helped + 1,
            updated_at=timestamp,
        )

    def meets_curator_threshold(self) -> bool:
        """
        Check if metrics meet the minimum threshold for Module Curator promotion.

        Requirements (per glossary):
        - Helped ≥ 3 learners
        - Reviewed ≥ 5 practice tasks
        - Average satisfaction ≥ 4.0/5.0
        """
        if self.average_satisfaction is None:
            return False

        return (
            self.learners_helped >= CURATOR_MIN_LEARNERS_HELPED
            and self.tasks_reviewed >= CURATOR_MIN_TASKS_REVIEWED
            and self.average_satisfaction >= CURATOR_MIN_SATISFACTION
        )
