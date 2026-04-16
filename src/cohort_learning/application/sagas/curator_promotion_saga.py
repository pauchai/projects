"""CuratorPromotionSaga — Stage 16.

Listens to ``HelperMetricsUpdated`` events and emits
``CuratorPromotionEligible`` when a learner's helper metrics satisfy all
three curator promotion thresholds:

- ``learners_helped >= 3``
- ``tasks_reviewed >= 5``
- ``average_satisfaction >= 4.0``

The saga is idempotent: it will NOT re-emit the event if the learner is
already recorded as a ``ModuleCurator`` for the cohort's module.

Full promotion still requires a Master to call
``PromoteToModuleCuratorUseCase``.  This saga is a notification-only step.
"""

from __future__ import annotations

from cohort_learning.domain.events import CuratorPromotionEligible, HelperMetricsUpdated
from cohort_learning.domain.ports import UnitOfWork
from shared_kernel.events import DomainEvent, EventBus


class CuratorPromotionSaga:
    """Saga: notify when a helper becomes eligible for curator promotion.

    Constructor args:
        uow: UnitOfWork — used for read-only queries on HelperMetrics,
            ModuleCurators and Cohorts.
        event_bus: EventBus — receives ``CuratorPromotionEligible`` when
            all thresholds are satisfied.
    """

    def __init__(self, uow: UnitOfWork, event_bus: EventBus) -> None:
        self._uow = uow
        self._event_bus = event_bus

    def handle(self, event: DomainEvent) -> None:
        assert isinstance(event, HelperMetricsUpdated)
        self._process(event)

    # -------------------------------------------------------------------------
    # Internal processing
    # -------------------------------------------------------------------------

    def _process(self, event: HelperMetricsUpdated) -> None:
        with self._uow:
            # Read full HelperMetrics to access average_satisfaction
            metrics = self._uow.helper_metrics.find_by_learner_and_cohort(
                event.learner_id, event.cohort_id
            )
            if metrics is None:
                return

            if not metrics.meets_curator_threshold():
                return

            # Resolve module_id from the cohort
            cohort = self._uow.cohorts.find_by_id(event.cohort_id)
            if cohort is None:
                return

            # Idempotency: skip if already a curator for this module
            existing = self._uow.module_curators.find_by_learner_and_module(
                learner_id=event.learner_id,
                module_id=cohort.module_id,
                cohort_id=event.cohort_id,
            )
            if existing is not None:
                return

            self._event_bus.publish(
                [
                    CuratorPromotionEligible(
                        cohort_id=event.cohort_id,
                        learner_id=event.learner_id,
                        module_id=cohort.module_id,
                    )
                ]
            )
