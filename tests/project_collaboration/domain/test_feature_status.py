"""Tests for FeatureStatus enum and state transitions."""


class TestFeatureStatusValues:
    """FeatureStatus enum should have exactly 5 values."""

    def test_has_submitted_status(self) -> None:
        from project_collaboration.domain.feature_status import FeatureStatus

        assert FeatureStatus.SUBMITTED.value == "submitted"

    def test_has_planned_status(self) -> None:
        from project_collaboration.domain.feature_status import FeatureStatus

        assert FeatureStatus.PLANNED.value == "planned"

    def test_has_in_progress_status(self) -> None:
        from project_collaboration.domain.feature_status import FeatureStatus

        assert FeatureStatus.IN_PROGRESS.value == "in_progress"

    def test_has_done_status(self) -> None:
        from project_collaboration.domain.feature_status import FeatureStatus

        assert FeatureStatus.DONE.value == "done"

    def test_has_rejected_status(self) -> None:
        from project_collaboration.domain.feature_status import FeatureStatus

        assert FeatureStatus.REJECTED.value == "rejected"

    def test_has_exactly_five_values(self) -> None:
        from project_collaboration.domain.feature_status import FeatureStatus

        assert len(FeatureStatus) == 5


class TestFeatureStatusTransitions:
    """Allowed and forbidden state transitions."""

    def test_submitted_can_transition_to_planned(self) -> None:
        from project_collaboration.domain.feature_status import FeatureStatus

        assert FeatureStatus.SUBMITTED.can_transition_to(FeatureStatus.PLANNED)

    def test_submitted_can_transition_to_rejected(self) -> None:
        from project_collaboration.domain.feature_status import FeatureStatus

        assert FeatureStatus.SUBMITTED.can_transition_to(FeatureStatus.REJECTED)

    def test_submitted_cannot_transition_to_done(self) -> None:
        from project_collaboration.domain.feature_status import FeatureStatus

        assert not FeatureStatus.SUBMITTED.can_transition_to(FeatureStatus.DONE)

    def test_submitted_cannot_transition_to_in_progress(self) -> None:
        from project_collaboration.domain.feature_status import FeatureStatus

        assert not FeatureStatus.SUBMITTED.can_transition_to(FeatureStatus.IN_PROGRESS)

    def test_planned_can_transition_to_in_progress(self) -> None:
        from project_collaboration.domain.feature_status import FeatureStatus

        assert FeatureStatus.PLANNED.can_transition_to(FeatureStatus.IN_PROGRESS)

    def test_planned_can_transition_to_rejected(self) -> None:
        from project_collaboration.domain.feature_status import FeatureStatus

        assert FeatureStatus.PLANNED.can_transition_to(FeatureStatus.REJECTED)

    def test_planned_cannot_transition_to_done(self) -> None:
        from project_collaboration.domain.feature_status import FeatureStatus

        assert not FeatureStatus.PLANNED.can_transition_to(FeatureStatus.DONE)

    def test_in_progress_can_transition_to_done(self) -> None:
        from project_collaboration.domain.feature_status import FeatureStatus

        assert FeatureStatus.IN_PROGRESS.can_transition_to(FeatureStatus.DONE)

    def test_in_progress_can_transition_to_rejected(self) -> None:
        from project_collaboration.domain.feature_status import FeatureStatus

        assert FeatureStatus.IN_PROGRESS.can_transition_to(FeatureStatus.REJECTED)

    def test_in_progress_can_transition_to_planned(self) -> None:
        from project_collaboration.domain.feature_status import FeatureStatus

        assert FeatureStatus.IN_PROGRESS.can_transition_to(FeatureStatus.PLANNED)

    def test_done_is_terminal(self) -> None:
        from project_collaboration.domain.feature_status import FeatureStatus

        for status in FeatureStatus:
            assert not FeatureStatus.DONE.can_transition_to(status)

    def test_rejected_is_terminal(self) -> None:
        from project_collaboration.domain.feature_status import FeatureStatus

        for status in FeatureStatus:
            assert not FeatureStatus.REJECTED.can_transition_to(status)

    def test_cannot_transition_to_self(self) -> None:
        from project_collaboration.domain.feature_status import FeatureStatus

        for status in FeatureStatus:
            assert not status.can_transition_to(status)
