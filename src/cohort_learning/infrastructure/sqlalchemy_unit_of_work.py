"""SQLAlchemy implementation of UnitOfWork (driven adapter) for Cohort Learning.

Supports optional event publishing: when an ``EventBus`` is provided,
domain events collected during ``save()`` are published **after** a
successful ``commit()``.  If no bus is given, events are silently
discarded — this keeps the system backward-compatible and testable.

Exposes nine repositories:
- ``cohorts`` — SqlAlchemyCohortRepository
- ``practice_tasks`` — SqlAlchemyPracticeTaskRepository
- ``peer_reviews`` — SqlAlchemyPeerReviewRepository
- ``topic_experts`` — SqlAlchemyTopicExpertRepository
- ``helper_metrics`` — SqlAlchemyHelperMetricsRepository
- ``module_curators`` — SqlAlchemyModuleCuratorRepository
- ``reward_ledgers`` — SqlAlchemyRewardLedgerRepository
- ``pending_competency_validations`` — SqlAlchemyPendingCompetencyValidationRepository
- ``pending_curator_promotions`` — SqlAlchemyPendingCuratorPromotionRepository
"""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from shared_kernel.events import DomainEvent, EventBus
from cohort_learning.infrastructure.sqlalchemy_repository import (
    SqlAlchemyCohortRepository,
    SqlAlchemyHelperMetricsRepository,
    SqlAlchemyModuleCuratorRepository,
    SqlAlchemyPeerReviewRepository,
    SqlAlchemyPendingCompetencyValidationRepository,
    SqlAlchemyPendingCuratorPromotionRepository,
    SqlAlchemyPracticeTaskRepository,
    SqlAlchemyRewardLedgerRepository,
    SqlAlchemyTopicCompetencyRepository,
    SqlAlchemyTopicExpertRepository,
)


class SqlAlchemyUnitOfWork:
    """UnitOfWork backed by a SQLAlchemy Session.

    Implements the UnitOfWork Protocol defined in ``domain.ports``.
    Application Services manage the lifecycle: ``with uow: ... uow.commit()``.
    """

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        event_bus: EventBus | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._event_bus = event_bus
        self._pending_events: list[DomainEvent] = []

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self._session = self._session_factory()
        self.cohorts = SqlAlchemyCohortRepository(self._session, self)
        self.practice_tasks = SqlAlchemyPracticeTaskRepository(self._session, self)
        self.peer_reviews = SqlAlchemyPeerReviewRepository(self._session, self)
        self.topic_experts = SqlAlchemyTopicExpertRepository(self._session)
        self.helper_metrics = SqlAlchemyHelperMetricsRepository(self._session)
        self.module_curators = SqlAlchemyModuleCuratorRepository(self._session)
        self.topic_competencies = SqlAlchemyTopicCompetencyRepository(self._session)
        self.reward_ledgers = SqlAlchemyRewardLedgerRepository(self._session, self)
        self.pending_competency_validations = (
            SqlAlchemyPendingCompetencyValidationRepository(self._session)
        )
        self.pending_curator_promotions = SqlAlchemyPendingCuratorPromotionRepository(
            self._session
        )
        return self

    def __exit__(self, exc_type: type[BaseException] | None, *args: object) -> None:
        if exc_type is not None:
            self._session.rollback()
            self._pending_events.clear()
        self._session.close()

    def commit(self) -> None:
        """Persist changes and publish collected domain events."""
        self._session.commit()
        # Publish events only after successful DB commit
        if self._event_bus and self._pending_events:
            self._event_bus.publish(self._pending_events)
        self._pending_events.clear()

    def rollback(self) -> None:
        self._session.rollback()
        self._pending_events.clear()

    def collect_events(self, events: list[DomainEvent]) -> None:
        """Accumulate domain events for publishing after commit.

        Called by the repository when an aggregate is saved.
        """
        self._pending_events.extend(events)
