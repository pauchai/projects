"""Tests for CuratorPromotionSaga (Stage 16).

The saga listens to ``HelperMetricsUpdated`` events and emits
``CuratorPromotionEligible`` when a learner's metrics cross all three
promotion thresholds (learners_helped >= 3, tasks_reviewed >= 5,
average_satisfaction >= 4.0) and the learner is not already a
ModuleCurator for that module (idempotency guard).
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from cohort_learning.application.sagas.curator_promotion_saga import (
    CuratorPromotionSaga,
)
from cohort_learning.domain.events import CuratorPromotionEligible, HelperMetricsUpdated
from tests.cohort_learning.factories import (
    create_helper_metrics,
    create_module_curator,
    make_cohort,
)
from tests.cohort_learning.fakes.fake_unit_of_work import FakeUnitOfWork


def _make_event(
    learner_id: str = "learner1",
    cohort_id: str = "c1",
    learners_helped: int = 3,
    tasks_reviewed: int = 5,
) -> HelperMetricsUpdated:
    return HelperMetricsUpdated(
        learner_id=learner_id,
        cohort_id=cohort_id,
        learners_helped=learners_helped,
        tasks_reviewed=tasks_reviewed,
    )


def _save_eligible_metrics(uow: FakeUnitOfWork, learner_id: str = "learner1") -> None:
    """Persist HelperMetrics that cross all three promotion thresholds."""
    metrics = create_helper_metrics(
        learner_id=learner_id,
        cohort_id="c1",
        learners_helped=3,
        tasks_reviewed=5,
        average_satisfaction=Decimal("4.0"),
    )
    uow.helper_metrics._storage[(learner_id, "c1")] = metrics


def _save_cohort(uow: FakeUnitOfWork, cohort_id: str = "c1") -> None:
    cohort = make_cohort(cohort_id=cohort_id, module_id="mod1")
    cohort.collect_events()
    uow.cohorts._storage[cohort_id] = cohort


class TestCuratorPromotionSagaDoesNothing:
    """Saga emits nothing when thresholds are not met or already promoted."""

    def test_does_nothing_when_metrics_not_found(self) -> None:
        bus = MagicMock()
        uow = FakeUnitOfWork()
        _save_cohort(uow)
        saga = CuratorPromotionSaga(uow=uow, event_bus=bus)

        saga.handle(_make_event())

        bus.publish.assert_not_called()

    def test_does_nothing_when_cohort_not_found(self) -> None:
        bus = MagicMock()
        uow = FakeUnitOfWork()
        _save_eligible_metrics(uow)
        # Cohort NOT saved
        saga = CuratorPromotionSaga(uow=uow, event_bus=bus)

        saga.handle(_make_event())

        bus.publish.assert_not_called()

    def test_does_nothing_when_learners_helped_below_threshold(self) -> None:
        bus = MagicMock()
        uow = FakeUnitOfWork()
        _save_cohort(uow)
        metrics = create_helper_metrics(
            learner_id="learner1",
            cohort_id="c1",
            learners_helped=2,
            tasks_reviewed=5,  # below minimum 3
            average_satisfaction=Decimal("4.0"),
        )
        uow.helper_metrics._storage[("learner1", "c1")] = metrics
        saga = CuratorPromotionSaga(uow=uow, event_bus=bus)

        saga.handle(_make_event())

        bus.publish.assert_not_called()

    def test_does_nothing_when_tasks_reviewed_below_threshold(self) -> None:
        bus = MagicMock()
        uow = FakeUnitOfWork()
        _save_cohort(uow)
        metrics = create_helper_metrics(
            learner_id="learner1",
            cohort_id="c1",
            learners_helped=3,
            tasks_reviewed=4,  # below minimum 5
            average_satisfaction=Decimal("4.0"),
        )
        uow.helper_metrics._storage[("learner1", "c1")] = metrics
        saga = CuratorPromotionSaga(uow=uow, event_bus=bus)

        saga.handle(_make_event())

        bus.publish.assert_not_called()

    def test_does_nothing_when_satisfaction_below_threshold(self) -> None:
        bus = MagicMock()
        uow = FakeUnitOfWork()
        _save_cohort(uow)
        metrics = create_helper_metrics(
            learner_id="learner1",
            cohort_id="c1",
            learners_helped=3,
            tasks_reviewed=5,
            average_satisfaction=Decimal("3.9"),  # below 4.0
        )
        uow.helper_metrics._storage[("learner1", "c1")] = metrics
        saga = CuratorPromotionSaga(uow=uow, event_bus=bus)

        saga.handle(_make_event())

        bus.publish.assert_not_called()

    def test_does_nothing_when_satisfaction_is_none(self) -> None:
        bus = MagicMock()
        uow = FakeUnitOfWork()
        _save_cohort(uow)
        metrics = create_helper_metrics(
            learner_id="learner1",
            cohort_id="c1",
            learners_helped=3,
            tasks_reviewed=5,
            average_satisfaction=None,
        )
        uow.helper_metrics._storage[("learner1", "c1")] = metrics
        saga = CuratorPromotionSaga(uow=uow, event_bus=bus)

        saga.handle(_make_event())

        bus.publish.assert_not_called()

    def test_does_nothing_when_already_a_module_curator(self) -> None:
        """Idempotency: if learner is already a curator for this module, skip."""
        bus = MagicMock()
        uow = FakeUnitOfWork()
        _save_cohort(uow)
        _save_eligible_metrics(uow)

        curator = create_module_curator(
            curator_id="cur1",
            learner_id="learner1",
            module_id="mod1",
            cohort_id="c1",
            promoted_by="master1",
        )
        uow.module_curators._storage["cur1"] = curator

        saga = CuratorPromotionSaga(uow=uow, event_bus=bus)
        saga.handle(_make_event())

        bus.publish.assert_not_called()


class TestCuratorPromotionSagaEmitsEvent:
    """Saga emits CuratorPromotionEligible when all conditions are met."""

    def test_emits_eligible_on_happy_path(self) -> None:
        bus = MagicMock()
        uow = FakeUnitOfWork()
        _save_cohort(uow)
        _save_eligible_metrics(uow)

        saga = CuratorPromotionSaga(uow=uow, event_bus=bus)
        saga.handle(_make_event())

        bus.publish.assert_called_once()
        events = bus.publish.call_args[0][0]
        assert len(events) == 1
        evt = events[0]
        assert isinstance(evt, CuratorPromotionEligible)
        assert evt.learner_id == "learner1"
        assert evt.cohort_id == "c1"
        assert evt.module_id == "mod1"

    def test_emits_at_exact_thresholds(self) -> None:
        """Exactly 3 learners_helped, 5 tasks_reviewed, 4.0 satisfaction = eligible."""
        bus = MagicMock()
        uow = FakeUnitOfWork()
        _save_cohort(uow)
        _save_eligible_metrics(uow)  # uses 3, 5, 4.0 exactly

        saga = CuratorPromotionSaga(uow=uow, event_bus=bus)
        saga.handle(_make_event())

        bus.publish.assert_called_once()

    def test_does_not_emit_for_different_module_curator(self) -> None:
        """Being a curator in a different module does not block this module."""
        bus = MagicMock()
        uow = FakeUnitOfWork()
        _save_cohort(uow)
        _save_eligible_metrics(uow)

        # Curator for a DIFFERENT module
        curator = create_module_curator(
            curator_id="cur1",
            learner_id="learner1",
            module_id="other_module",
            cohort_id="c1",
            promoted_by="master1",
        )
        uow.module_curators._storage["cur1"] = curator

        saga = CuratorPromotionSaga(uow=uow, event_bus=bus)
        saga.handle(_make_event())

        bus.publish.assert_called_once()

    def test_emits_with_above_threshold_values(self) -> None:
        """Well above thresholds → still eligible."""
        bus = MagicMock()
        uow = FakeUnitOfWork()
        _save_cohort(uow)
        metrics = create_helper_metrics(
            learner_id="learner1",
            cohort_id="c1",
            learners_helped=10,
            tasks_reviewed=20,
            average_satisfaction=Decimal("4.8"),
        )
        uow.helper_metrics._storage[("learner1", "c1")] = metrics

        saga = CuratorPromotionSaga(uow=uow, event_bus=bus)
        saga.handle(_make_event())

        bus.publish.assert_called_once()
