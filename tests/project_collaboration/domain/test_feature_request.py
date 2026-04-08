"""Tests for FeatureRequest entity."""

import pytest

from project_collaboration.domain.feature_status import FeatureStatus


class TestFeatureRequestCreation:
    """FeatureRequest creation and validation."""

    def test_creates_with_valid_data(self) -> None:
        from project_collaboration.domain.feature_request import FeatureRequest

        fr = FeatureRequest(
            request_id="fr1",
            author_id="user1",
            title="Add dark mode",
            description="Please add dark mode to the app",
        )

        assert fr.request_id == "fr1"
        assert fr.author_id == "user1"
        assert fr.title == "Add dark mode"
        assert fr.description == "Please add dark mode to the app"
        assert fr.status == FeatureStatus.SUBMITTED
        assert fr.category is None
        assert fr.priority is None
        assert fr.admin_notes == ""
        assert fr.metadata == {}

    def test_creates_with_optional_fields(self) -> None:
        from project_collaboration.domain.feature_request import FeatureRequest

        fr = FeatureRequest(
            request_id="fr1",
            author_id="user1",
            title="Add dark mode",
            description="Please add dark mode",
            category="ui",
            priority="high",
        )

        assert fr.category == "ui"
        assert fr.priority == "high"

    def test_sets_created_at_timestamp(self) -> None:
        from project_collaboration.domain.feature_request import FeatureRequest

        fr = FeatureRequest(
            request_id="fr1",
            author_id="user1",
            title="Add dark mode",
            description="Description",
        )

        assert fr.created_at is not None
        assert fr.updated_at is not None

    def test_rejects_title_shorter_than_minimum(self) -> None:
        from project_collaboration.domain.feature_request import FeatureRequest

        with pytest.raises(ValueError, match="Title must be between"):
            FeatureRequest(
                request_id="fr1",
                author_id="user1",
                title="Ab",
                description="Description",
            )

    def test_rejects_title_longer_than_maximum(self) -> None:
        from project_collaboration.domain.feature_request import FeatureRequest

        with pytest.raises(ValueError, match="Title must be between"):
            FeatureRequest(
                request_id="fr1",
                author_id="user1",
                title="A" * 501,
                description="Description",
            )

    def test_rejects_description_longer_than_maximum(self) -> None:
        from project_collaboration.domain.feature_request import FeatureRequest

        with pytest.raises(ValueError, match="Description must not exceed"):
            FeatureRequest(
                request_id="fr1",
                author_id="user1",
                title="Valid title",
                description="A" * 10001,
            )

    def test_rejects_empty_title(self) -> None:
        from project_collaboration.domain.feature_request import FeatureRequest

        with pytest.raises(ValueError, match="Title must be between"):
            FeatureRequest(
                request_id="fr1",
                author_id="user1",
                title="",
                description="Description",
            )


class TestFeatureRequestEvents:
    """Domain events emitted by FeatureRequest."""

    def test_emits_created_event_on_creation(self) -> None:
        from project_collaboration.domain.events import FeatureRequestSubmitted
        from project_collaboration.domain.feature_request import FeatureRequest

        fr = FeatureRequest(
            request_id="fr1",
            author_id="user1",
            title="Add dark mode",
            description="Description",
        )

        events = fr.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], FeatureRequestSubmitted)
        assert events[0].request_id == "fr1"
        assert events[0].author_id == "user1"
        assert events[0].title == "Add dark mode"

    def test_collect_events_clears_list(self) -> None:
        from project_collaboration.domain.feature_request import FeatureRequest

        fr = FeatureRequest(
            request_id="fr1",
            author_id="user1",
            title="Add dark mode",
            description="Description",
        )

        fr.collect_events()
        assert fr.collect_events() == []


class TestFeatureRequestStatusTransition:
    """Status transitions on FeatureRequest entity."""

    def test_transition_submitted_to_planned(self) -> None:
        from project_collaboration.domain.events import FeatureRequestStatusChanged
        from project_collaboration.domain.feature_request import FeatureRequest

        fr = FeatureRequest(
            request_id="fr1",
            author_id="user1",
            title="Add dark mode",
            description="Description",
        )
        fr.collect_events()  # clear creation event

        fr.change_status(FeatureStatus.PLANNED)

        assert fr.status == FeatureStatus.PLANNED
        events = fr.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], FeatureRequestStatusChanged)
        assert events[0].request_id == "fr1"
        assert events[0].old_status == "submitted"
        assert events[0].new_status == "planned"

    def test_transition_planned_to_in_progress(self) -> None:
        from project_collaboration.domain.feature_request import FeatureRequest

        fr = FeatureRequest(
            request_id="fr1",
            author_id="user1",
            title="Add dark mode",
            description="Description",
        )
        fr.change_status(FeatureStatus.PLANNED)
        fr.collect_events()

        fr.change_status(FeatureStatus.IN_PROGRESS)

        assert fr.status == FeatureStatus.IN_PROGRESS

    def test_transition_in_progress_to_done(self) -> None:
        from project_collaboration.domain.feature_request import FeatureRequest

        fr = FeatureRequest(
            request_id="fr1",
            author_id="user1",
            title="Add dark mode",
            description="Description",
        )
        fr.change_status(FeatureStatus.PLANNED)
        fr.change_status(FeatureStatus.IN_PROGRESS)
        fr.collect_events()

        fr.change_status(FeatureStatus.DONE)

        assert fr.status == FeatureStatus.DONE

    def test_transition_submitted_to_rejected(self) -> None:
        from project_collaboration.domain.feature_request import FeatureRequest

        fr = FeatureRequest(
            request_id="fr1",
            author_id="user1",
            title="Add dark mode",
            description="Description",
        )
        fr.collect_events()

        fr.change_status(FeatureStatus.REJECTED)

        assert fr.status == FeatureStatus.REJECTED

    def test_rejects_invalid_transition(self) -> None:
        from project_collaboration.domain.feature_request import FeatureRequest

        fr = FeatureRequest(
            request_id="fr1",
            author_id="user1",
            title="Add dark mode",
            description="Description",
        )

        with pytest.raises(ValueError, match="Cannot transition"):
            fr.change_status(FeatureStatus.DONE)

    def test_updates_updated_at_on_transition(self) -> None:
        from project_collaboration.domain.feature_request import FeatureRequest

        fr = FeatureRequest(
            request_id="fr1",
            author_id="user1",
            title="Add dark mode",
            description="Description",
        )
        original_updated_at = fr.updated_at

        fr.change_status(FeatureStatus.PLANNED)

        assert fr.updated_at >= original_updated_at


class TestFeatureRequestAdminNotes:
    """Admin notes management."""

    def test_set_admin_notes(self) -> None:
        from project_collaboration.domain.feature_request import FeatureRequest

        fr = FeatureRequest(
            request_id="fr1",
            author_id="user1",
            title="Add dark mode",
            description="Description",
        )

        fr.set_admin_notes("Will implement in Q3")

        assert fr.admin_notes == "Will implement in Q3"

    def test_updates_updated_at_on_admin_notes_change(self) -> None:
        from project_collaboration.domain.feature_request import FeatureRequest

        fr = FeatureRequest(
            request_id="fr1",
            author_id="user1",
            title="Add dark mode",
            description="Description",
        )
        original = fr.updated_at

        fr.set_admin_notes("Notes")

        assert fr.updated_at >= original
