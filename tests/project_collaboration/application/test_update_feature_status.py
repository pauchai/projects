"""Tests for UpdateFeatureStatus use case."""

import pytest

from project_collaboration.domain.events import FeatureRequestStatusChanged
from project_collaboration.domain.feature_status import FeatureStatus
from shared_kernel.events import DomainEvent
from tests.project_collaboration.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.project_collaboration.factories import (
    make_feature_request,
    make_planned_feature_request,
    save_feature_request,
)


class _SpyEventBus:
    """Spy event bus that records all published events."""

    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    def publish(self, events: list[DomainEvent]) -> None:
        self.published.extend(events)


class TestUpdateFeatureStatusUseCase:
    """UpdateFeatureStatus transitions a feature request to a new status."""

    def test_transitions_submitted_to_planned(self) -> None:
        from project_collaboration.application.update_feature_status import (
            UpdateFeatureStatusUseCase,
        )

        uow = FakeUnitOfWork()
        fr = make_feature_request()
        save_feature_request(uow, fr)
        use_case = UpdateFeatureStatusUseCase(uow=uow)

        use_case.execute(
            request_id="fr1",
            new_status=FeatureStatus.PLANNED,
            admin_notes="Scheduled for Q3",
        )

        with uow:
            updated = uow.feature_requests.find_by_id("fr1")
            assert updated is not None
            assert updated.status == FeatureStatus.PLANNED
            assert updated.admin_notes == "Scheduled for Q3"

    def test_transitions_planned_to_in_progress(self) -> None:
        from project_collaboration.application.update_feature_status import (
            UpdateFeatureStatusUseCase,
        )

        uow = FakeUnitOfWork()
        fr = make_planned_feature_request()
        save_feature_request(uow, fr)
        use_case = UpdateFeatureStatusUseCase(uow=uow)

        use_case.execute(
            request_id="fr1",
            new_status=FeatureStatus.IN_PROGRESS,
        )

        with uow:
            updated = uow.feature_requests.find_by_id("fr1")
            assert updated is not None
            assert updated.status == FeatureStatus.IN_PROGRESS

    def test_commits_transaction(self) -> None:
        from project_collaboration.application.update_feature_status import (
            UpdateFeatureStatusUseCase,
        )

        uow = FakeUnitOfWork()
        fr = make_feature_request()
        save_feature_request(uow, fr)
        use_case = UpdateFeatureStatusUseCase(uow=uow)

        use_case.execute(
            request_id="fr1",
            new_status=FeatureStatus.PLANNED,
        )

        assert uow.committed is True

    def test_emits_status_changed_event(self) -> None:
        from project_collaboration.application.update_feature_status import (
            UpdateFeatureStatusUseCase,
        )

        spy_bus = _SpyEventBus()
        uow = FakeUnitOfWork(event_bus=spy_bus)
        fr = make_feature_request()
        save_feature_request(uow, fr)
        use_case = UpdateFeatureStatusUseCase(uow=uow)

        use_case.execute(
            request_id="fr1",
            new_status=FeatureStatus.PLANNED,
        )

        status_events = [
            e for e in spy_bus.published if isinstance(e, FeatureRequestStatusChanged)
        ]
        assert len(status_events) == 1
        assert status_events[0].request_id == "fr1"
        assert status_events[0].old_status == "submitted"
        assert status_events[0].new_status == "planned"

    def test_raises_when_feature_request_not_found(self) -> None:
        from project_collaboration.application.update_feature_status import (
            UpdateFeatureStatusUseCase,
        )

        uow = FakeUnitOfWork()
        use_case = UpdateFeatureStatusUseCase(uow=uow)

        with pytest.raises(LookupError, match="Feature request .* not found"):
            use_case.execute(
                request_id="nonexistent",
                new_status=FeatureStatus.PLANNED,
            )

    def test_raises_on_invalid_transition(self) -> None:
        from project_collaboration.application.update_feature_status import (
            UpdateFeatureStatusUseCase,
        )

        uow = FakeUnitOfWork()
        fr = make_feature_request()
        save_feature_request(uow, fr)
        use_case = UpdateFeatureStatusUseCase(uow=uow)

        with pytest.raises(ValueError, match="Cannot transition"):
            use_case.execute(
                request_id="fr1",
                new_status=FeatureStatus.DONE,
            )

    def test_admin_notes_default_empty_when_not_provided(self) -> None:
        from project_collaboration.application.update_feature_status import (
            UpdateFeatureStatusUseCase,
        )

        uow = FakeUnitOfWork()
        fr = make_feature_request()
        save_feature_request(uow, fr)
        use_case = UpdateFeatureStatusUseCase(uow=uow)

        use_case.execute(
            request_id="fr1",
            new_status=FeatureStatus.PLANNED,
        )

        with uow:
            updated = uow.feature_requests.find_by_id("fr1")
            assert updated is not None
            # admin_notes should remain unchanged (empty string from creation)
            assert updated.admin_notes == ""
