"""Tests for CohortStatus enum and state transitions."""


class TestCohortStatusValues:
    """CohortStatus enum should have exactly 5 values."""

    def test_has_forming_status(self) -> None:
        from cohort_learning.domain.cohort_status import CohortStatus

        assert CohortStatus.FORMING.value == "forming"

    def test_has_active_status(self) -> None:
        from cohort_learning.domain.cohort_status import CohortStatus

        assert CohortStatus.ACTIVE.value == "active"

    def test_has_completing_status(self) -> None:
        from cohort_learning.domain.cohort_status import CohortStatus

        assert CohortStatus.COMPLETING.value == "completing"

    def test_has_graduated_status(self) -> None:
        from cohort_learning.domain.cohort_status import CohortStatus

        assert CohortStatus.GRADUATED.value == "graduated"

    def test_has_cancelled_status(self) -> None:
        from cohort_learning.domain.cohort_status import CohortStatus

        assert CohortStatus.CANCELLED.value == "cancelled"

    def test_has_exactly_five_values(self) -> None:
        from cohort_learning.domain.cohort_status import CohortStatus

        assert len(CohortStatus) == 5


class TestCohortStatusTransitions:
    """Allowed and forbidden state transitions."""

    def test_forming_can_transition_to_active(self) -> None:
        from cohort_learning.domain.cohort_status import CohortStatus

        assert CohortStatus.FORMING.can_transition_to(CohortStatus.ACTIVE)

    def test_forming_can_transition_to_cancelled(self) -> None:
        from cohort_learning.domain.cohort_status import CohortStatus

        assert CohortStatus.FORMING.can_transition_to(CohortStatus.CANCELLED)

    def test_forming_cannot_transition_to_completing(self) -> None:
        from cohort_learning.domain.cohort_status import CohortStatus

        assert not CohortStatus.FORMING.can_transition_to(CohortStatus.COMPLETING)

    def test_forming_cannot_transition_to_graduated(self) -> None:
        from cohort_learning.domain.cohort_status import CohortStatus

        assert not CohortStatus.FORMING.can_transition_to(CohortStatus.GRADUATED)

    def test_active_can_transition_to_completing(self) -> None:
        from cohort_learning.domain.cohort_status import CohortStatus

        assert CohortStatus.ACTIVE.can_transition_to(CohortStatus.COMPLETING)

    def test_active_can_transition_to_cancelled(self) -> None:
        from cohort_learning.domain.cohort_status import CohortStatus

        assert CohortStatus.ACTIVE.can_transition_to(CohortStatus.CANCELLED)

    def test_active_cannot_transition_to_forming(self) -> None:
        from cohort_learning.domain.cohort_status import CohortStatus

        assert not CohortStatus.ACTIVE.can_transition_to(CohortStatus.FORMING)

    def test_active_cannot_transition_to_graduated(self) -> None:
        from cohort_learning.domain.cohort_status import CohortStatus

        assert not CohortStatus.ACTIVE.can_transition_to(CohortStatus.GRADUATED)

    def test_completing_can_transition_to_graduated(self) -> None:
        from cohort_learning.domain.cohort_status import CohortStatus

        assert CohortStatus.COMPLETING.can_transition_to(CohortStatus.GRADUATED)

    def test_completing_can_transition_to_cancelled(self) -> None:
        from cohort_learning.domain.cohort_status import CohortStatus

        assert CohortStatus.COMPLETING.can_transition_to(CohortStatus.CANCELLED)

    def test_completing_cannot_transition_to_forming(self) -> None:
        from cohort_learning.domain.cohort_status import CohortStatus

        assert not CohortStatus.COMPLETING.can_transition_to(CohortStatus.FORMING)

    def test_completing_cannot_transition_to_active(self) -> None:
        from cohort_learning.domain.cohort_status import CohortStatus

        assert not CohortStatus.COMPLETING.can_transition_to(CohortStatus.ACTIVE)

    def test_graduated_is_terminal(self) -> None:
        from cohort_learning.domain.cohort_status import CohortStatus

        for status in CohortStatus:
            assert not CohortStatus.GRADUATED.can_transition_to(status)

    def test_cancelled_is_terminal(self) -> None:
        from cohort_learning.domain.cohort_status import CohortStatus

        for status in CohortStatus:
            assert not CohortStatus.CANCELLED.can_transition_to(status)

    def test_cannot_transition_to_self(self) -> None:
        from cohort_learning.domain.cohort_status import CohortStatus

        for status in CohortStatus:
            assert not status.can_transition_to(status)
