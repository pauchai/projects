"""Integration tests for SqlAlchemyFeatureRequestRepository and UoW.

These tests verify the real PostgreSQL persistence layer for feature requests:
- Round-trip save/load of FeatureRequest entities
- Persistence of all fields (category, priority, admin_notes, metadata)
- Status transitions survive DB round-trip
- find_all with filters (status, author_id)
- UoW commit/rollback semantics for feature requests
- Reconstituted entities have clean transient state (_events)
- Domain event publishing through EventBus after commit

Requires ``docker compose up -d postgres-test`` (port 5433).
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session, sessionmaker

from shared_kernel.events import DomainEvent
from shared_kernel.in_process_event_bus import InProcessEventBus

from project_collaboration.domain.events import FeatureRequestSubmitted
from project_collaboration.domain.feature_request import FeatureRequest
from project_collaboration.domain.feature_status import FeatureStatus
from project_collaboration.infrastructure.sqlalchemy_repository import (
    SqlAlchemyFeatureRequestRepository,
)
from project_collaboration.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_feature_request(**overrides: object) -> FeatureRequest:
    """Create a FeatureRequest with defaults (avoids FakeUoW import)."""
    defaults: dict = dict(
        request_id="fr1",
        author_id="user1",
        title="Dark mode support",
        description="Add a dark mode toggle to the application settings.",
    )
    defaults.update(overrides)
    fr = FeatureRequest(**defaults)
    fr.collect_events()  # clear creation events
    return fr


# ---------------------------------------------------------------------------
# Repository: find_by_id
# ---------------------------------------------------------------------------


class TestFindById:
    """Tests for SqlAlchemyFeatureRequestRepository.find_by_id."""

    def test_returns_none_for_nonexistent_request(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyFeatureRequestRepository(integration_session)

        result = repo.find_by_id("nonexistent")

        assert result is None

    def test_round_trip_saves_and_loads_feature_request(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyFeatureRequestRepository(integration_session)
        fr = _make_feature_request()

        repo.save(fr)
        loaded = repo.find_by_id("fr1")

        assert loaded is not None
        assert loaded.request_id == "fr1"
        assert loaded.author_id == "user1"
        assert loaded.title == "Dark mode support"
        assert (
            loaded.description == "Add a dark mode toggle to the application settings."
        )
        assert loaded.status == FeatureStatus.SUBMITTED
        assert loaded.created_at is not None
        assert loaded.updated_at is not None

    def test_persists_category_and_priority(self, integration_session: Session) -> None:
        repo = SqlAlchemyFeatureRequestRepository(integration_session)
        fr = _make_feature_request(category="ui", priority="high")

        repo.save(fr)
        loaded = repo.find_by_id("fr1")

        assert loaded is not None
        assert loaded.category == "ui"
        assert loaded.priority == "high"

    def test_persists_null_category_and_priority(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyFeatureRequestRepository(integration_session)
        fr = _make_feature_request()

        repo.save(fr)
        loaded = repo.find_by_id("fr1")

        assert loaded is not None
        assert loaded.category is None
        assert loaded.priority is None

    def test_persists_admin_notes(self, integration_session: Session) -> None:
        repo = SqlAlchemyFeatureRequestRepository(integration_session)
        fr = _make_feature_request()
        fr.set_admin_notes("Scheduled for Q3")

        repo.save(fr)
        loaded = repo.find_by_id("fr1")

        assert loaded is not None
        assert loaded.admin_notes == "Scheduled for Q3"

    def test_persists_metadata(self, integration_session: Session) -> None:
        repo = SqlAlchemyFeatureRequestRepository(integration_session)
        fr = _make_feature_request()
        fr.metadata = {"source": "slack", "channel": "#product"}

        repo.save(fr)
        loaded = repo.find_by_id("fr1")

        assert loaded is not None
        assert loaded.metadata == {"source": "slack", "channel": "#product"}

    def test_persists_status_after_transition(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyFeatureRequestRepository(integration_session)
        fr = _make_feature_request()
        fr.change_status(FeatureStatus.PLANNED)
        fr.collect_events()

        repo.save(fr)
        loaded = repo.find_by_id("fr1")

        assert loaded is not None
        assert loaded.status == FeatureStatus.PLANNED


# ---------------------------------------------------------------------------
# Repository: find_all
# ---------------------------------------------------------------------------


class TestFindAll:
    """Tests for SqlAlchemyFeatureRequestRepository.find_all."""

    def test_returns_all_when_no_filters(self, integration_session: Session) -> None:
        repo = SqlAlchemyFeatureRequestRepository(integration_session)
        repo.save(_make_feature_request(request_id="fr1", title="Feature One"))
        repo.save(_make_feature_request(request_id="fr2", title="Feature Two"))

        results = repo.find_all()

        assert len(results) == 2
        ids = {r.request_id for r in results}
        assert ids == {"fr1", "fr2"}

    def test_filter_by_status(self, integration_session: Session) -> None:
        repo = SqlAlchemyFeatureRequestRepository(integration_session)
        submitted = _make_feature_request(request_id="fr1", title="Submitted Feature")
        planned = _make_feature_request(request_id="fr2", title="Planned Feature")
        planned.change_status(FeatureStatus.PLANNED)
        planned.collect_events()

        repo.save(submitted)
        repo.save(planned)

        results = repo.find_all(status=FeatureStatus.PLANNED)

        assert len(results) == 1
        assert results[0].request_id == "fr2"

    def test_filter_by_author_id(self, integration_session: Session) -> None:
        repo = SqlAlchemyFeatureRequestRepository(integration_session)
        repo.save(
            _make_feature_request(
                request_id="fr1", author_id="alice", title="Alice Feat"
            )
        )
        repo.save(
            _make_feature_request(request_id="fr2", author_id="bob", title="Bob Feat")
        )

        results = repo.find_all(author_id="alice")

        assert len(results) == 1
        assert results[0].request_id == "fr1"

    def test_combined_filters(self, integration_session: Session) -> None:
        repo = SqlAlchemyFeatureRequestRepository(integration_session)
        # alice: submitted
        repo.save(
            _make_feature_request(
                request_id="fr1", author_id="alice", title="Alice Submitted"
            )
        )
        # alice: planned
        planned = _make_feature_request(
            request_id="fr2", author_id="alice", title="Alice Planned"
        )
        planned.change_status(FeatureStatus.PLANNED)
        planned.collect_events()
        repo.save(planned)
        # bob: planned
        bob_planned = _make_feature_request(
            request_id="fr3", author_id="bob", title="Bob Planned"
        )
        bob_planned.change_status(FeatureStatus.PLANNED)
        bob_planned.collect_events()
        repo.save(bob_planned)

        results = repo.find_all(status=FeatureStatus.PLANNED, author_id="alice")

        assert len(results) == 1
        assert results[0].request_id == "fr2"

    def test_returns_empty_when_no_matches(self, integration_session: Session) -> None:
        repo = SqlAlchemyFeatureRequestRepository(integration_session)
        repo.save(_make_feature_request(request_id="fr1"))

        results = repo.find_all(author_id="nonexistent")

        assert results == []


# ---------------------------------------------------------------------------
# Repository: upsert (save twice)
# ---------------------------------------------------------------------------


class TestUpsertBehavior:
    """Verify that save() is idempotent (upsert semantics)."""

    def test_save_twice_updates_existing_feature_request(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyFeatureRequestRepository(integration_session)
        fr = _make_feature_request()

        repo.save(fr)

        # Mutate and save again
        fr.change_status(FeatureStatus.PLANNED)
        fr.collect_events()
        repo.save(fr)

        loaded = repo.find_by_id("fr1")
        assert loaded is not None
        assert loaded.status == FeatureStatus.PLANNED


# ---------------------------------------------------------------------------
# Repository: reconstituted entity has empty _events
# ---------------------------------------------------------------------------


class TestReconstitution:
    """Verify reconstituted feature requests have clean transient state."""

    def test_reconstituted_feature_request_has_empty_events(
        self, integration_session: Session
    ) -> None:
        repo = SqlAlchemyFeatureRequestRepository(integration_session)
        fr = _make_feature_request()

        repo.save(fr)
        loaded = repo.find_by_id("fr1")

        assert loaded is not None
        assert loaded._events == []


# ---------------------------------------------------------------------------
# Unit of Work: commit/rollback semantics
# ---------------------------------------------------------------------------


class TestUnitOfWork:
    """Tests for SqlAlchemyUnitOfWork commit and rollback with feature requests."""

    def test_uow_commit_persists_feature_request(
        self,
        integration_session_factory: sessionmaker[Session],
    ) -> None:
        uow = SqlAlchemyUnitOfWork(integration_session_factory)
        fr = _make_feature_request()

        with uow:
            uow.feature_requests.save(fr)
            uow.commit()

        # Read back via a fresh UoW
        with uow:
            loaded = uow.feature_requests.find_by_id("fr1")
            assert loaded is not None
            assert loaded.request_id == "fr1"

    def test_uow_rollback_discards_feature_request(
        self,
        integration_session_factory: sessionmaker[Session],
    ) -> None:
        uow = SqlAlchemyUnitOfWork(integration_session_factory)
        fr = _make_feature_request()

        with uow:
            uow.feature_requests.save(fr)
            uow.rollback()

        # Should not find the feature request
        with uow:
            loaded = uow.feature_requests.find_by_id("fr1")
            assert loaded is None

    def test_uow_exit_without_commit_rolls_back(
        self,
        integration_session_factory: sessionmaker[Session],
    ) -> None:
        uow = SqlAlchemyUnitOfWork(integration_session_factory)
        fr = _make_feature_request()

        with uow:
            uow.feature_requests.save(fr)
            # no commit, __exit__ should rollback

        with uow:
            loaded = uow.feature_requests.find_by_id("fr1")
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
    - Events are NOT published when __exit__ fires without commit (exception path).
    """

    def test_events_published_after_commit(
        self,
        integration_session_factory: sessionmaker[Session],
    ) -> None:
        """Domain events collected during save() are published after commit()."""
        bus = InProcessEventBus()
        handler = _SpyHandler()
        bus.subscribe(FeatureRequestSubmitted, handler)

        # Create a fresh feature request (don't clear events)
        fr = FeatureRequest(
            request_id="evt1",
            author_id="user1",
            title="Event Test Feature",
            description="Testing event publishing for feature requests",
        )
        uow = SqlAlchemyUnitOfWork(integration_session_factory, event_bus=bus)

        with uow:
            uow.feature_requests.save(fr)
            # Before commit — handler should NOT have received anything
            assert handler.handled == []

            uow.commit()

        # After commit — handler should have the FeatureRequestSubmitted event
        assert len(handler.handled) == 1
        event = handler.handled[0]
        assert isinstance(event, FeatureRequestSubmitted)
        assert event.request_id == "evt1"
        assert event.author_id == "user1"
        assert event.title == "Event Test Feature"

    def test_events_not_published_after_rollback(
        self,
        integration_session_factory: sessionmaker[Session],
    ) -> None:
        """Events collected during save() are discarded on rollback()."""
        bus = InProcessEventBus()
        handler = _SpyHandler()
        bus.subscribe(FeatureRequestSubmitted, handler)

        fr = FeatureRequest(
            request_id="evt2",
            author_id="user1",
            title="Rollback Test Feature",
            description="Testing rollback discards events",
        )
        uow = SqlAlchemyUnitOfWork(integration_session_factory, event_bus=bus)

        with uow:
            uow.feature_requests.save(fr)
            uow.rollback()

        assert handler.handled == []

    def test_events_not_published_on_exception_exit(
        self,
        integration_session_factory: sessionmaker[Session],
    ) -> None:
        """Events are discarded when __exit__ fires due to an exception."""
        bus = InProcessEventBus()
        handler = _SpyHandler()
        bus.subscribe(FeatureRequestSubmitted, handler)

        fr = FeatureRequest(
            request_id="evt3",
            author_id="user1",
            title="Exception Test Feature",
            description="Testing exception path",
        )
        uow = SqlAlchemyUnitOfWork(integration_session_factory, event_bus=bus)

        with pytest.raises(RuntimeError, match="forced"):
            with uow:
                uow.feature_requests.save(fr)
                raise RuntimeError("forced")

        assert handler.handled == []
