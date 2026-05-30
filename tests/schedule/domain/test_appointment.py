"""Unit tests for Appointment domain entity."""

import pytest
from datetime import datetime, timezone, timedelta

from src.schedule.domain.appointment import Appointment


def make_appointment(
    appointment_id: str = "a-1",
    request_id: str = "r-1",
    curator_id: str = "c-1",
    scheduled_at: datetime | None = None,
) -> Appointment:
    if scheduled_at is None:
        scheduled_at = datetime.now(timezone.utc) + timedelta(days=1)
    return Appointment(
        appointment_id=appointment_id,
        request_id=request_id,
        curator_id=curator_id,
        scheduled_at=scheduled_at,
    )


class TestAppointmentCreation:
    def test_creates_with_scheduled_status(self) -> None:
        appt = make_appointment()
        assert appt.status == "scheduled"

    def test_raises_when_scheduled_at_is_naive(self) -> None:
        naive_dt = datetime(2026, 6, 1, 10, 0, 0)
        with pytest.raises(ValueError, match="timezone-aware"):
            make_appointment(scheduled_at=naive_dt)


class TestComplete:
    def test_transitions_to_completed(self) -> None:
        appt = make_appointment()
        appt.complete()
        assert appt.status == "completed"

    def test_raises_when_already_completed(self) -> None:
        appt = make_appointment()
        appt.complete()
        with pytest.raises(ValueError, match="completed"):
            appt.complete()

    def test_raises_when_cancelled(self) -> None:
        appt = make_appointment()
        appt.cancel()
        with pytest.raises(ValueError, match="cancelled"):
            appt.complete()


class TestCancel:
    def test_transitions_to_cancelled(self) -> None:
        appt = make_appointment()
        appt.cancel()
        assert appt.status == "cancelled"

    def test_raises_when_already_cancelled(self) -> None:
        appt = make_appointment()
        appt.cancel()
        with pytest.raises(ValueError, match="cancelled"):
            appt.cancel()
