"""Integration tests for SqlAlchemyCohortRepository and SqlAlchemyUnitOfWork.

These tests verify the real PostgreSQL persistence layer:
- Round-trip save/load of full LearningCohort aggregates
- Persistence of child entities (CohortMembership)
- Persistence of enum columns (CohortStatus, CohortRole)
- Persistence of boolean and datetime columns
- Upsert semantics (save twice updates)
- UoW commit/rollback semantics
- Nonexistent cohort returns None
- Domain event publishing through EventBus after commit

Requires ``docker compose up -d postgres-test`` (port 5433).
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session, sessionmaker

from shared_kernel.events import DomainEvent
from shared_kernel.in_process_event_bus import InProcessEventBus

from cohort_learning.domain.cohort_role import CohortRole
from cohort_learning.domain.cohort_status import CohortStatus
from cohort_learning.domain.events import CohortFormed
from cohort_learning.domain.learning_cohort import LearningCohort
from cohort_learning.infrastructure.sqlalchemy_repository import (
    SqlAlchemyCohortRepository,
)
from cohort_learning.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cohort(**overrides: object) -> LearningCohort:
    """Create a LearningCohort with defaults (avoids FakeUoW import)."""
    defaults: dict = dict(
        cohort_id="c1",
        master_id="master1",
        module_id="mod1",
    )
    defaults.update(overrides)
    cohort = LearningCohort(**defaults)
    cohort.collect_events()  # clear creation events
    return cohort


def _make_active_cohort(learner_count: int = 5, **overrides: object) -> LearningCohort:
    """Create an active cohort with enrolled learners."""
    cohort = _make_cohort(**overrides)
    for i in range(learner_count):
        cohort.enrol_learner(
            membership_id=f"m{i}",
            learner_id=f"learner{i}",
        )
    cohort.activate()
    cohort.collect_events()
    return cohort


# ---------------------------------------------------------------------------
# Repository: find_by_id
# ---------------------------------------------------------------------------


class TestFindById:
    """Tests for SqlAlchemyCohortRepository.find_by_id."""

    def test_returns_none_for_nonexistent_cohort(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyCohortRepository(integration_session)

        result = repo.find_by_id("nonexistent")

        assert result is None

    def test_round_trip_saves_and_loads_cohort(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyCohortRepository(integration_session)
        cohort = _make_cohort()

        repo.save(cohort)
        loaded = repo.find_by_id("c1")

        assert loaded is not None
        assert loaded.cohort_id == "c1"
        assert loaded.master_id == "master1"
        assert loaded.module_id == "mod1"
        assert loaded.status == CohortStatus.FORMING
        assert loaded.formed_at is not None

    def test_persists_status_after_activation(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyCohortRepository(integration_session)
        cohort = _make_active_cohort()

        repo.save(cohort)
        loaded = repo.find_by_id("c1")

        assert loaded is not None
        assert loaded.status == CohortStatus.ACTIVE


# ---------------------------------------------------------------------------
# Repository: membership persistence
# ---------------------------------------------------------------------------


class TestMembershipPersistence:
    """Tests for persistence of CohortMembership entities."""

    def test_persists_memberships(self, integration_session: Session) -> None:
        repo = SqlAlchemyCohortRepository(integration_session)
        cohort = _make_cohort()
        cohort.enrol_learner(membership_id="m1", learner_id="learner1")
        cohort.enrol_learner(membership_id="m2", learner_id="learner2")
        cohort.collect_events()

        repo.save(cohort)
        loaded = repo.find_by_id("c1")

        assert loaded is not None
        assert len(loaded.memberships) == 2
        learner_ids = {m.learner_id for m in loaded.memberships}
        assert learner_ids == {"learner1", "learner2"}

    def test_persists_membership_role(self, integration_session: Session) -> None:
        repo = SqlAlchemyCohortRepository(integration_session)
        cohort = _make_cohort()
        cohort.enrol_learner(membership_id="m1", learner_id="learner1")
        cohort.collect_events()

        repo.save(cohort)
        loaded = repo.find_by_id("c1")

        assert loaded is not None
        membership = loaded.memberships[0]
        assert membership.role == CohortRole.LEARNER
        assert membership.is_active is True

    def test_persists_membership_deactivation(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyCohortRepository(integration_session)
        cohort = _make_cohort()
        cohort.enrol_learner(membership_id="m1", learner_id="learner1")
        cohort.remove_learner("m1")
        cohort.collect_events()

        repo.save(cohort)
        loaded = repo.find_by_id("c1")

        assert loaded is not None
        membership = loaded.memberships[0]
        assert membership.is_active is False

    def test_persists_membership_promotion(self, integration_session: Session) -> None:
        repo = SqlAlchemyCohortRepository(integration_session)
        cohort = _make_cohort()
        cohort.enrol_learner(membership_id="m1", learner_id="learner1")
        # Promote directly on the membership entity
        m = cohort.memberships[0]
        m.promote_to(CohortRole.TOPIC_EXPERT)
        cohort.collect_events()

        repo.save(cohort)
        loaded = repo.find_by_id("c1")

        assert loaded is not None
        membership = loaded.memberships[0]
        assert membership.role == CohortRole.TOPIC_EXPERT

    def test_persists_joined_at(self, integration_session: Session) -> None:
        repo = SqlAlchemyCohortRepository(integration_session)
        cohort = _make_cohort()
        cohort.enrol_learner(membership_id="m1", learner_id="learner1")
        original_joined = cohort.memberships[0].joined_at
        cohort.collect_events()

        repo.save(cohort)
        loaded = repo.find_by_id("c1")

        assert loaded is not None
        membership = loaded.memberships[0]
        assert membership.joined_at is not None
        # Compare with truncated microseconds (DB may round)
        assert membership.joined_at.replace(microsecond=0) == original_joined.replace(
            microsecond=0
        )


# ---------------------------------------------------------------------------
# Repository: upsert (save twice)
# ---------------------------------------------------------------------------


class TestUpsertBehavior:
    """Verify that save() is idempotent (upsert semantics)."""

    def test_save_twice_updates_existing_cohort(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyCohortRepository(integration_session)
        cohort = _make_active_cohort()

        repo.save(cohort)

        # Mutate and save again
        cohort.begin_completing()
        cohort.collect_events()
        repo.save(cohort)

        loaded = repo.find_by_id("c1")
        assert loaded is not None
        assert loaded.status == CohortStatus.COMPLETING


# ---------------------------------------------------------------------------
# Repository: reconstitution
# ---------------------------------------------------------------------------


class TestReconstitution:
    """Verify reconstituted cohorts have clean transient state."""

    def test_reconstituted_cohort_has_empty_events(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyCohortRepository(integration_session)
        cohort = _make_cohort()

        repo.save(cohort)
        loaded = repo.find_by_id("c1")

        assert loaded is not None
        assert loaded._events == []


# ---------------------------------------------------------------------------
# Unit of Work: commit/rollback semantics
# ---------------------------------------------------------------------------


class TestUnitOfWork:
    """Tests for SqlAlchemyUnitOfWork commit and rollback semantics."""

    def test_uow_commit_persists_changes(
        self,
        integration_session_factory: sessionmaker[Session],
    ) -> None:
        uow = SqlAlchemyUnitOfWork(integration_session_factory)
        cohort = _make_cohort()

        with uow:
            uow.cohorts.save(cohort)
            uow.commit()

        # Read back via a fresh UoW
        with uow:
            loaded = uow.cohorts.find_by_id("c1")
            assert loaded is not None
            assert loaded.cohort_id == "c1"

    def test_uow_rollback_discards_changes(
        self,
        integration_session_factory: sessionmaker[Session],
    ) -> None:
        uow = SqlAlchemyUnitOfWork(integration_session_factory)
        cohort = _make_cohort()

        with uow:
            uow.cohorts.save(cohort)
            uow.rollback()

        # Should not find the cohort
        with uow:
            loaded = uow.cohorts.find_by_id("c1")
            assert loaded is None

    def test_uow_exit_without_commit_rolls_back(
        self,
        integration_session_factory: sessionmaker[Session],
    ) -> None:
        uow = SqlAlchemyUnitOfWork(integration_session_factory)
        cohort = _make_cohort()

        with uow:
            uow.cohorts.save(cohort)
            # no commit, __exit__ should rollback

        with uow:
            loaded = uow.cohorts.find_by_id("c1")
            assert loaded is None


# ---------------------------------------------------------------------------
# Unit of Work: domain event publishing
# ---------------------------------------------------------------------------


class _SpyHandler:
    """Spy handler that records all events for assertion."""

    def __init__(self) -> None:
        self.handled: list[DomainEvent] = []

    def handle(self, event: DomainEvent) -> None:
        self.handled.append(event)


class TestUnitOfWorkEventPublishing:
    """Integration tests for domain event publishing through UoW + EventBus.

    Verifies:
    - Events ARE published after a successful commit().
    - Events are NOT published after rollback().
    - Events are NOT published when __exit__ fires due to an exception.
    - Without event bus, commit works normally (backward compatibility).
    - Events are cleared after commit (no double publishing on second commit).
    """

    def test_events_published_after_commit(
        self,
        integration_session_factory: sessionmaker[Session],
    ) -> None:
        """Domain events collected during save() are published after commit()."""
        bus = InProcessEventBus()
        handler = _SpyHandler()
        bus.subscribe(CohortFormed, handler)

        # Create a fresh cohort with events (don't clear them)
        cohort = LearningCohort(
            cohort_id="evt1",
            master_id="master1",
            module_id="mod1",
        )
        uow = SqlAlchemyUnitOfWork(integration_session_factory, event_bus=bus)

        with uow:
            uow.cohorts.save(cohort)
            # Before commit — handler should NOT have received anything
            assert handler.handled == []

            uow.commit()

        # After commit — handler should have the CohortFormed event
        assert len(handler.handled) == 1
        event = handler.handled[0]
        assert isinstance(event, CohortFormed)
        assert event.cohort_id == "evt1"
        assert event.master_id == "master1"
        assert event.module_id == "mod1"

    def test_events_not_published_after_rollback(
        self,
        integration_session_factory: sessionmaker[Session],
    ) -> None:
        """Events collected during save() are discarded on rollback()."""
        bus = InProcessEventBus()
        handler = _SpyHandler()
        bus.subscribe(CohortFormed, handler)

        cohort = LearningCohort(
            cohort_id="evt2",
            master_id="master1",
            module_id="mod1",
        )
        uow = SqlAlchemyUnitOfWork(integration_session_factory, event_bus=bus)

        with uow:
            uow.cohorts.save(cohort)
            uow.rollback()

        assert handler.handled == []

    def test_events_not_published_on_exception_exit(
        self,
        integration_session_factory: sessionmaker[Session],
    ) -> None:
        """Events are discarded when __exit__ fires due to an exception."""
        bus = InProcessEventBus()
        handler = _SpyHandler()
        bus.subscribe(CohortFormed, handler)

        cohort = LearningCohort(
            cohort_id="evt3",
            master_id="master1",
            module_id="mod1",
        )
        uow = SqlAlchemyUnitOfWork(integration_session_factory, event_bus=bus)

        with pytest.raises(RuntimeError, match="forced"):
            with uow:
                uow.cohorts.save(cohort)
                raise RuntimeError("forced")

        assert handler.handled == []

    def test_commit_without_event_bus_works(
        self,
        integration_session_factory: sessionmaker[Session],
    ) -> None:
        """Backward compatibility: UoW without event_bus commits normally."""
        cohort = LearningCohort(
            cohort_id="evt4",
            master_id="master1",
            module_id="mod1",
        )
        uow = SqlAlchemyUnitOfWork(integration_session_factory)  # no event_bus

        with uow:
            uow.cohorts.save(cohort)
            uow.commit()

        # Data should be persisted
        with uow:
            loaded = uow.cohorts.find_by_id("evt4")
            assert loaded is not None
            assert loaded.cohort_id == "evt4"

    def test_events_cleared_after_commit_no_double_publish(
        self,
        integration_session_factory: sessionmaker[Session],
    ) -> None:
        """After commit, pending events are cleared — second commit does not re-publish."""
        bus = InProcessEventBus()
        handler = _SpyHandler()
        bus.subscribe(CohortFormed, handler)

        cohort = LearningCohort(
            cohort_id="evt5",
            master_id="master1",
            module_id="mod1",
        )
        uow = SqlAlchemyUnitOfWork(integration_session_factory, event_bus=bus)

        with uow:
            uow.cohorts.save(cohort)
            uow.commit()
            # Second commit with no new changes — should not re-publish
            uow.commit()

        assert len(handler.handled) == 1
