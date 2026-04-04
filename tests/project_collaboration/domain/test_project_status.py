"""Tests for ProjectStatus enum and state transitions."""

import pytest


class TestProjectStatusValues:
    """ProjectStatus enum should have exactly 6 values."""

    def test_has_draft_status(self) -> None:
        from project_collaboration.domain.project_status import ProjectStatus

        assert ProjectStatus.DRAFT.value == "draft"

    def test_has_recruiting_status(self) -> None:
        from project_collaboration.domain.project_status import ProjectStatus

        assert ProjectStatus.RECRUITING.value == "recruiting"

    def test_has_active_status(self) -> None:
        from project_collaboration.domain.project_status import ProjectStatus

        assert ProjectStatus.ACTIVE.value == "active"

    def test_has_completed_status(self) -> None:
        from project_collaboration.domain.project_status import ProjectStatus

        assert ProjectStatus.COMPLETED.value == "completed"

    def test_has_suspended_status(self) -> None:
        from project_collaboration.domain.project_status import ProjectStatus

        assert ProjectStatus.SUSPENDED.value == "suspended"

    def test_has_cancelled_status(self) -> None:
        from project_collaboration.domain.project_status import ProjectStatus

        assert ProjectStatus.CANCELLED.value == "cancelled"

    def test_has_exactly_six_values(self) -> None:
        from project_collaboration.domain.project_status import ProjectStatus

        assert len(ProjectStatus) == 6


class TestProjectStatusTransitions:
    """Allowed and forbidden state transitions."""

    def test_draft_can_transition_to_recruiting(self) -> None:
        from project_collaboration.domain.project_status import ProjectStatus

        assert ProjectStatus.DRAFT.can_transition_to(ProjectStatus.RECRUITING)

    def test_draft_cannot_transition_to_active(self) -> None:
        from project_collaboration.domain.project_status import ProjectStatus

        assert not ProjectStatus.DRAFT.can_transition_to(ProjectStatus.ACTIVE)

    def test_recruiting_can_transition_to_active(self) -> None:
        from project_collaboration.domain.project_status import ProjectStatus

        assert ProjectStatus.RECRUITING.can_transition_to(ProjectStatus.ACTIVE)

    def test_recruiting_can_transition_to_suspended(self) -> None:
        from project_collaboration.domain.project_status import ProjectStatus

        assert ProjectStatus.RECRUITING.can_transition_to(ProjectStatus.SUSPENDED)

    def test_recruiting_can_transition_to_cancelled(self) -> None:
        from project_collaboration.domain.project_status import ProjectStatus

        assert ProjectStatus.RECRUITING.can_transition_to(ProjectStatus.CANCELLED)

    def test_active_can_transition_to_completed(self) -> None:
        from project_collaboration.domain.project_status import ProjectStatus

        assert ProjectStatus.ACTIVE.can_transition_to(ProjectStatus.COMPLETED)

    def test_active_can_transition_to_suspended(self) -> None:
        from project_collaboration.domain.project_status import ProjectStatus

        assert ProjectStatus.ACTIVE.can_transition_to(ProjectStatus.SUSPENDED)

    def test_active_can_transition_to_cancelled(self) -> None:
        from project_collaboration.domain.project_status import ProjectStatus

        assert ProjectStatus.ACTIVE.can_transition_to(ProjectStatus.CANCELLED)

    def test_suspended_can_transition_to_active(self) -> None:
        from project_collaboration.domain.project_status import ProjectStatus

        assert ProjectStatus.SUSPENDED.can_transition_to(ProjectStatus.ACTIVE)

    def test_suspended_can_transition_to_recruiting(self) -> None:
        from project_collaboration.domain.project_status import ProjectStatus

        assert ProjectStatus.SUSPENDED.can_transition_to(ProjectStatus.RECRUITING)

    def test_completed_is_terminal(self) -> None:
        from project_collaboration.domain.project_status import ProjectStatus

        for status in ProjectStatus:
            assert not ProjectStatus.COMPLETED.can_transition_to(status)

    def test_cancelled_is_terminal(self) -> None:
        from project_collaboration.domain.project_status import ProjectStatus

        for status in ProjectStatus:
            assert not ProjectStatus.CANCELLED.can_transition_to(status)

    def test_draft_cannot_transition_to_completed(self) -> None:
        from project_collaboration.domain.project_status import ProjectStatus

        assert not ProjectStatus.DRAFT.can_transition_to(ProjectStatus.COMPLETED)

    def test_cannot_transition_to_self(self) -> None:
        from project_collaboration.domain.project_status import ProjectStatus

        for status in ProjectStatus:
            assert not status.can_transition_to(status)
