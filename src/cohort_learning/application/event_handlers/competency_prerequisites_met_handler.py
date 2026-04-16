"""CompetencyPrerequisitesMetHandler — Stage 17.

Persists a ``PendingCompetencyValidation`` record whenever a
``CompetencyPrerequisitesMet`` event is received, so Masters and Curators
can discover which learners are waiting for knowledge-check validation.

Idempotency: if a record for the same (learner, topic, cohort) already
exists, the handler does nothing.  The use-case layer handles dynamic
filtering of already-validated learners.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from cohort_learning.domain.events import CompetencyPrerequisitesMet
from cohort_learning.domain.pending_competency_validation import (
    PendingCompetencyValidation,
)
from cohort_learning.domain.ports import UnitOfWork
from shared_kernel.events import DomainEvent


class CompetencyPrerequisitesMetHandler:
    """Subscribe to ``CompetencyPrerequisitesMet`` and persist a pending record.

    Triggered by: ``CompetencyPrerequisitesMet``
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, event: DomainEvent) -> None:
        assert isinstance(event, CompetencyPrerequisitesMet)

        with self._uow:
            existing = (
                self._uow.pending_competency_validations.find_by_learner_topic_cohort(
                    learner_id=event.learner_id,
                    topic_id=event.topic_id,
                    cohort_id=event.cohort_id,
                )
            )
            if existing is not None:
                return

            record = PendingCompetencyValidation(
                pending_id=str(uuid.uuid4()),
                learner_id=event.learner_id,
                topic_id=event.topic_id,
                cohort_id=event.cohort_id,
                created_at=datetime.now(tz=timezone.utc),
            )
            self._uow.pending_competency_validations.save(record)
            self._uow.commit()
