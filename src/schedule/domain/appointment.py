"""Schedule domain entity: Appointment."""

from datetime import datetime, timezone
from typing import Literal


AppointmentStatus = Literal["scheduled", "completed", "cancelled"]


class Appointment:
    """A confirmed consultation appointment between a student and curator.

    Created by the coordinator after a curator accepts an offer and a
    specific date/time is agreed upon.
    """

    def __init__(
        self,
        appointment_id: str,
        request_id: str,
        curator_id: str,
        scheduled_at: datetime,
    ) -> None:
        if scheduled_at.tzinfo is None:
            raise ValueError("scheduled_at must be timezone-aware")

        self.appointment_id = appointment_id
        self.request_id = request_id
        self.curator_id = curator_id
        self.scheduled_at = scheduled_at
        self.status: AppointmentStatus = "scheduled"
        self.created_at: datetime = datetime.now(timezone.utc)

    def complete(self) -> None:
        """Mark the appointment as completed."""
        if self.status != "scheduled":
            raise ValueError(
                f"Cannot complete appointment with status '{self.status}'"
            )
        self.status = "completed"

    def cancel(self) -> None:
        """Cancel the appointment. Triggers re-negotiation in the use case."""
        if self.status != "scheduled":
            raise ValueError(
                f"Cannot cancel appointment with status '{self.status}'"
            )
        self.status = "cancelled"
