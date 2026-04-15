"""RecordHelperActivity use case."""

from datetime import datetime, timezone
from decimal import Decimal

from cohort_learning.application._helpers import get_cohort_or_raise
from cohort_learning.domain.helper_metrics import HelperMetrics
from cohort_learning.domain.ports import UnitOfWork


class RecordHelperActivityUseCase:
    """Record peer helping activity (reviews, learners helped).

    This use case is typically triggered by domain event handlers rather than
    direct user API calls. For example:
    - PeerReviewSubmitted event → record peer review activity
    - Task submission helped → record learner helped

    Creates HelperMetrics if it doesn't exist, updates if it does.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        learner_id: str,
        cohort_id: str,
        activity_type: str,
        satisfaction_score: Decimal | None = None,
        helped_learner_id: str | None = None,
    ) -> HelperMetrics:
        with self._uow as uow:
            # Verify cohort exists
            get_cohort_or_raise(uow, cohort_id)

            # Get or create helper metrics
            metrics = uow.helper_metrics.find_by_learner(learner_id, cohort_id)
            if metrics is None:
                metrics = HelperMetrics(
                    learner_id=learner_id,
                    cohort_id=cohort_id,
                    learners_helped=0,
                    questions_answered=0,
                    tasks_reviewed=0,
                    average_satisfaction=None,
                    updated_at=datetime.now(timezone.utc),
                )

            # Update metrics based on activity type
            timestamp = datetime.now(timezone.utc)

            if activity_type == "peer_review":
                if satisfaction_score is None:
                    raise ValueError(
                        "satisfaction_score is required for peer_review activity"
                    )
                metrics = metrics.record_peer_review(satisfaction_score, timestamp)

            elif activity_type == "learner_helped":
                if helped_learner_id is None:
                    raise ValueError(
                        "helped_learner_id is required for learner_helped activity"
                    )
                metrics = metrics.record_learner_helped(helped_learner_id, timestamp)

            else:
                raise ValueError(f"Invalid activity_type: '{activity_type}'")

            uow.helper_metrics.save(metrics)
            uow.commit()
            return metrics
