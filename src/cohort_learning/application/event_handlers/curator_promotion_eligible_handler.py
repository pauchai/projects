"""CuratorPromotionEligibleHandler — Stage 18.

Persists a ``PendingCuratorPromotion`` record whenever a
``CuratorPromotionEligible`` event is received, so Masters can discover
which learners have met all helper-metric thresholds and are waiting for
the formal promotion via ``PromoteToModuleCuratorUseCase``.

Idempotency: if a record for the same (learner, module, cohort) already
exists, the handler does nothing.  The use-case layer handles dynamic
filtering of already-promoted learners.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from cohort_learning.domain.events import CuratorPromotionEligible
from cohort_learning.domain.pending_curator_promotion import PendingCuratorPromotion
from cohort_learning.domain.ports import UnitOfWork
from shared_kernel.events import DomainEvent


class CuratorPromotionEligibleHandler:
    """Subscribe to ``CuratorPromotionEligible`` and persist a pending record.

    Triggered by: ``CuratorPromotionEligible``
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, event: DomainEvent) -> None:
        assert isinstance(event, CuratorPromotionEligible)

        with self._uow:
            existing = (
                self._uow.pending_curator_promotions.find_by_learner_module_cohort(
                    learner_id=event.learner_id,
                    module_id=event.module_id,
                    cohort_id=event.cohort_id,
                )
            )
            if existing is not None:
                return

            record = PendingCuratorPromotion(
                pending_id=str(uuid.uuid4()),
                learner_id=event.learner_id,
                module_id=event.module_id,
                cohort_id=event.cohort_id,
                created_at=datetime.now(tz=timezone.utc),
            )
            self._uow.pending_curator_promotions.save(record)
            self._uow.commit()
