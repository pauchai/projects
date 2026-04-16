"""GetPendingCompetencyValidations use case — Stage 17.

Returns PendingCompetencyValidation records for a cohort, filtered to
exclude learners who have already received a TopicCompetency for the
same (learner, topic, cohort).

Authorization: Master or Module Curator only.
"""

from __future__ import annotations

from cohort_learning.application._helpers import (
    get_cohort_or_raise,
    require_master_or_curator,
)
from cohort_learning.domain.pending_competency_validation import (
    PendingCompetencyValidation,
)
from cohort_learning.domain.ports import UnitOfWork


class GetPendingCompetencyValidationsUseCase:
    """Query pending competency validations for a cohort.

    Returns all ``PendingCompetencyValidation`` records where the learner
    has not yet been granted a ``TopicCompetency`` for the same topic.
    Stale records (learner already validated) are filtered out at query
    time without being deleted from the store.

    Authorization:
    - Master can query for any cohort they own.
    - Module Curator can query for their cohort.
    - Regular learners are not permitted.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        cohort_id: str,
        caller_id: str,
    ) -> list[PendingCompetencyValidation]:
        with self._uow as uow:
            cohort = get_cohort_or_raise(uow, cohort_id)
            require_master_or_curator(cohort, caller_id)

            pending = uow.pending_competency_validations.find_by_cohort(cohort_id)

            result = [
                record
                for record in pending
                if uow.topic_competencies.find_by_learner_and_topic(
                    learner_id=record.learner_id,
                    topic_id=record.topic_id,
                    cohort_id=cohort_id,
                )
                is None
            ]

            uow.commit()
            return result
