"""Use case: Coordinator assigns a confirmed appointment."""

import uuid
from datetime import datetime

from schedule.domain.appointment import Appointment
from schedule.domain.ports import ScheduleUnitOfWork


class AssignAppointmentUseCase:
    """Coordinator assigns a specific datetime to a consultation request.

    Preconditions:
    - Request must be in 'negotiating' status.
    - There must be exactly one accepted offer for the request.
    """

    def __init__(self, uow: ScheduleUnitOfWork) -> None:
        self._uow = uow

    def execute(self, request_id: str, scheduled_at: datetime) -> str:
        """Assign appointment and return appointment_id."""
        with self._uow as uow:
            request = uow.requests.find_by_id(request_id)
            if request is None:
                raise LookupError(f"Request '{request_id}' not found")

            if request.status != "negotiating":
                raise ValueError(
                    f"Cannot assign appointment to request with status '{request.status}'"
                )

            offers = uow.offers.find_by_request_id(request_id)
            accepted = [o for o in offers if o.status == "accepted"]
            if not accepted:
                raise ValueError(
                    "No accepted offer found for this request"
                )
            if len(accepted) > 1:
                raise ValueError(
                    "Multiple accepted offers found — data inconsistency"
                )

            curator_id = accepted[0].curator_id

            appointment = Appointment(
                appointment_id=str(uuid.uuid4()),
                request_id=request_id,
                curator_id=curator_id,
                scheduled_at=scheduled_at,
            )
            request.confirm()

            uow.appointments.save(appointment)
            uow.requests.save(request)
            uow.commit()
            return appointment.appointment_id
