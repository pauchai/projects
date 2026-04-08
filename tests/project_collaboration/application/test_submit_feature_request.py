"""Tests for SubmitFeatureRequest use case."""

import pytest

from project_collaboration.domain.events import FeatureRequestSubmitted
from project_collaboration.domain.feature_status import FeatureStatus
from shared_kernel.events import DomainEvent
from tests.project_collaboration.fakes.fake_unit_of_work import FakeUnitOfWork


class _SpyEventBus:
    """Spy event bus that records all published events."""

    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    def publish(self, events: list[DomainEvent]) -> None:
        self.published.extend(events)


class TestSubmitFeatureRequestUseCase:
    """SubmitFeatureRequest creates a new feature request in Submitted status."""

    def test_creates_feature_request_in_submitted_status(self) -> None:
        from project_collaboration.application.submit_feature_request import (
            SubmitFeatureRequestUseCase,
        )

        uow = FakeUnitOfWork()
        use_case = SubmitFeatureRequestUseCase(uow=uow)

        result = use_case.execute(
            request_id="fr1",
            author_id="user1",
            title="Add dark mode",
            description="Please add dark mode to the app",
        )

        assert result.request_id == "fr1"
        assert result.author_id == "user1"
        assert result.title == "Add dark mode"
        assert result.description == "Please add dark mode to the app"
        assert result.status == FeatureStatus.SUBMITTED

    def test_saves_to_repository(self) -> None:
        from project_collaboration.application.submit_feature_request import (
            SubmitFeatureRequestUseCase,
        )

        uow = FakeUnitOfWork()
        use_case = SubmitFeatureRequestUseCase(uow=uow)

        use_case.execute(
            request_id="fr1",
            author_id="user1",
            title="Add dark mode",
            description="Description",
        )

        with uow:
            assert uow.feature_requests.find_by_id("fr1") is not None

    def test_commits_transaction(self) -> None:
        from project_collaboration.application.submit_feature_request import (
            SubmitFeatureRequestUseCase,
        )

        uow = FakeUnitOfWork()
        use_case = SubmitFeatureRequestUseCase(uow=uow)

        use_case.execute(
            request_id="fr1",
            author_id="user1",
            title="Add dark mode",
            description="Description",
        )

        assert uow.committed is True

    def test_emits_submitted_event(self) -> None:
        from project_collaboration.application.submit_feature_request import (
            SubmitFeatureRequestUseCase,
        )

        spy_bus = _SpyEventBus()
        uow = FakeUnitOfWork(event_bus=spy_bus)
        use_case = SubmitFeatureRequestUseCase(uow=uow)

        use_case.execute(
            request_id="fr1",
            author_id="user1",
            title="Add dark mode",
            description="Description",
        )

        assert len(spy_bus.published) == 1
        assert isinstance(spy_bus.published[0], FeatureRequestSubmitted)
        assert spy_bus.published[0].request_id == "fr1"

    def test_with_optional_category_and_priority(self) -> None:
        from project_collaboration.application.submit_feature_request import (
            SubmitFeatureRequestUseCase,
        )

        uow = FakeUnitOfWork()
        use_case = SubmitFeatureRequestUseCase(uow=uow)

        result = use_case.execute(
            request_id="fr1",
            author_id="user1",
            title="Add dark mode",
            description="Description",
            category="ui",
            priority="high",
        )

        assert result.category == "ui"
        assert result.priority == "high"

    def test_invalid_title_raises(self) -> None:
        from project_collaboration.application.submit_feature_request import (
            SubmitFeatureRequestUseCase,
        )

        uow = FakeUnitOfWork()
        use_case = SubmitFeatureRequestUseCase(uow=uow)

        with pytest.raises(ValueError, match="Title must be between"):
            use_case.execute(
                request_id="fr1",
                author_id="user1",
                title="Ab",
                description="Description",
            )
