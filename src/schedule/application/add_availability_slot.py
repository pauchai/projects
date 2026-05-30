"""Use case: Add an availability slot to a curator's schedule."""

import uuid
from datetime import time

from schedule.domain.curator import AvailabilitySlot
from schedule.domain.ports import ScheduleUnitOfWork


class AddAvailabilitySlotUseCase:
    """Add a weekly availability window to a curator's schedule."""

    def __init__(self, uow: ScheduleUnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        curator_id: str,
        weekday: int,
        start_time: time,
        end_time: time,
    ) -> str:
        """Add a slot and return its slot_id."""
        with self._uow as uow:
            curator = uow.curators.find_by_id(curator_id)
            if curator is None:
                raise LookupError(f"Curator '{curator_id}' not found")

            slot = AvailabilitySlot(
                slot_id=str(uuid.uuid4()),
                curator_id=curator_id,
                weekday=weekday,
                start_time=start_time,
                end_time=end_time,
            )
            curator.add_availability_slot(slot)
            uow.curators.save(curator)
            uow.commit()
            return slot.slot_id
