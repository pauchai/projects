"""Tests for PromoteToModuleCurator use case."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from cohort_learning.application.promote_to_module_curator import (
    PromoteToModuleCuratorUseCase,
)
from cohort_learning.domain.events import CuratorPromoted
from cohort_learning.domain.helper_metrics import HelperMetrics
from shared_kernel.events import DomainEvent
from tests.cohort_learning.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.cohort_learning.factories import make_active_cohort, save_cohort


class _SpyEventBus:
    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    def publish(self, events: list[DomainEvent]) -> None:
        self.published.extend(events)


class TestPromoteToModuleCuratorUseCase:
    """Promote a learner to Module Curator after meeting all requirements."""

    def test_creates_module_curator_when_all_requirements_met(self) -> None:
        """When all promotion requirements pass, creates ModuleCurator."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)

        # Create qualifying helper metrics
        metrics = HelperMetrics(
            learner_id="learner1",
            cohort_id="c1",
            learners_helped=5,
            questions_answered=10,
            tasks_reviewed=10,
            average_satisfaction=Decimal("4.5"),
            updated_at=datetime.now(timezone.utc),
        )
        with uow:
            uow.helper_metrics.save(metrics)
            uow.commit()

        use_case = PromoteToModuleCuratorUseCase(uow=uow)

        use_case.execute(
            curator_id="cur1",
            learner_id="learner1",
            module_id="mod1",
            cohort_id="c1",
            master_id="master1",
            module_completed=True,
            teaching_trial_passed=True,
        )

        curator = uow.module_curators.find_by_id("cur1")
        assert curator is not None
        assert curator.learner_id == "learner1"
        assert curator.module_id == "mod1"
        assert curator.promoted_by == "master1"

    def test_raises_when_helper_metrics_below_threshold(self) -> None:
        """Promotion fails if helper metrics don't meet curator threshold."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)

        # Create insufficient helper metrics
        metrics = HelperMetrics(
            learner_id="learner1",
            cohort_id="c1",
            learners_helped=1,  # Below threshold of 3
            questions_answered=0,
            tasks_reviewed=2,  # Below threshold of 5
            average_satisfaction=Decimal("3.0"),  # Below threshold of 4.0
            updated_at=datetime.now(timezone.utc),
        )
        with uow:
            uow.helper_metrics.save(metrics)
            uow.commit()

        use_case = PromoteToModuleCuratorUseCase(uow=uow)

        with pytest.raises(ValueError, match="does not meet promotion requirements"):
            use_case.execute(
                curator_id="cur1",
                learner_id="learner1",
                module_id="mod1",
                cohort_id="c1",
                master_id="master1",
                module_completed=True,
                teaching_trial_passed=True,
            )

    def test_raises_when_module_not_completed(self) -> None:
        """Promotion fails if module not completed."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)

        # Create qualifying helper metrics
        metrics = HelperMetrics(
            learner_id="learner1",
            cohort_id="c1",
            learners_helped=5,
            questions_answered=10,
            tasks_reviewed=10,
            average_satisfaction=Decimal("4.5"),
            updated_at=datetime.now(timezone.utc),
        )
        with uow:
            uow.helper_metrics.save(metrics)
            uow.commit()

        use_case = PromoteToModuleCuratorUseCase(uow=uow)

        with pytest.raises(ValueError, match="does not meet promotion requirements"):
            use_case.execute(
                curator_id="cur1",
                learner_id="learner1",
                module_id="mod1",
                cohort_id="c1",
                master_id="master1",
                module_completed=False,  # Not completed
                teaching_trial_passed=True,
            )

    def test_raises_when_already_curator(self) -> None:
        """Cannot promote same learner to curator for same module twice."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)

        # Create qualifying helper metrics
        metrics = HelperMetrics(
            learner_id="learner1",
            cohort_id="c1",
            learners_helped=5,
            questions_answered=10,
            tasks_reviewed=10,
            average_satisfaction=Decimal("4.5"),
            updated_at=datetime.now(timezone.utc),
        )
        with uow:
            uow.helper_metrics.save(metrics)
            uow.commit()

        use_case = PromoteToModuleCuratorUseCase(uow=uow)

        # First promotion
        use_case.execute(
            curator_id="cur1",
            learner_id="learner1",
            module_id="mod1",
            cohort_id="c1",
            master_id="master1",
            module_completed=True,
            teaching_trial_passed=True,
        )

        # Second promotion should fail
        with pytest.raises(ValueError, match="already a Module Curator"):
            use_case.execute(
                curator_id="cur2",
                learner_id="learner1",
                module_id="mod1",
                cohort_id="c1",
                master_id="master1",
                module_completed=True,
                teaching_trial_passed=True,
            )

    def test_raises_when_caller_is_not_master(self) -> None:
        """Only master can promote to Module Curator."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)

        use_case = PromoteToModuleCuratorUseCase(uow=uow)

        with pytest.raises(PermissionError, match="Only the cohort master"):
            use_case.execute(
                curator_id="cur1",
                learner_id="learner1",
                module_id="mod1",
                cohort_id="c1",
                master_id="learner2",  # Not the master
                module_completed=True,
                teaching_trial_passed=True,
            )

    def test_emits_curator_promoted_event(self) -> None:
        """When promotion succeeds, emits CuratorPromoted event."""
        spy_bus = _SpyEventBus()
        uow = FakeUnitOfWork(event_bus=spy_bus)
        cohort = make_active_cohort()
        save_cohort(uow, cohort)

        # Create qualifying helper metrics
        metrics = HelperMetrics(
            learner_id="learner1",
            cohort_id="c1",
            learners_helped=5,
            questions_answered=10,
            tasks_reviewed=10,
            average_satisfaction=Decimal("4.5"),
            updated_at=datetime.now(timezone.utc),
        )
        with uow:
            uow.helper_metrics.save(metrics)
            uow.commit()

        use_case = PromoteToModuleCuratorUseCase(uow=uow)

        use_case.execute(
            curator_id="cur1",
            learner_id="learner1",
            module_id="mod1",
            cohort_id="c1",
            master_id="master1",
            module_completed=True,
            teaching_trial_passed=True,
        )

        events = [e for e in spy_bus.published if isinstance(e, CuratorPromoted)]
        assert len(events) == 1
        assert events[0].learner_id == "learner1"
        assert events[0].module_id == "mod1"

    def test_commits_transaction(self) -> None:
        """Use case commits the transaction after promotion."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)

        # Create qualifying helper metrics
        metrics = HelperMetrics(
            learner_id="learner1",
            cohort_id="c1",
            learners_helped=5,
            questions_answered=10,
            tasks_reviewed=10,
            average_satisfaction=Decimal("4.5"),
            updated_at=datetime.now(timezone.utc),
        )
        with uow:
            uow.helper_metrics.save(metrics)
            uow.commit()

        use_case = PromoteToModuleCuratorUseCase(uow=uow)

        use_case.execute(
            curator_id="cur1",
            learner_id="learner1",
            module_id="mod1",
            cohort_id="c1",
            master_id="master1",
            module_completed=True,
            teaching_trial_passed=True,
        )

        assert uow.committed is True
