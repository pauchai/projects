"""Use case: Coordinator starts a negotiation session."""

import uuid

from schedule.domain.consultation_offer import ConsultationOffer
from schedule.domain.ports import ScheduleUnitOfWork


class StartNegotiationUseCase:
    """Coordinator broadcasts offers to all recommended curators.

    The request transitions to 'negotiating'. One ConsultationOffer
    is created per recommended curator.
    """

    def __init__(self, uow: ScheduleUnitOfWork) -> None:
        self._uow = uow

    def execute(self, request_id: str) -> list[str]:
        """Start negotiation and return list of created offer_ids."""
        with self._uow as uow:
            request = uow.requests.find_by_id(request_id)
            if request is None:
                raise LookupError(f"Request '{request_id}' not found")

            request.start_negotiation()

            offers = [
                ConsultationOffer(
                    offer_id=str(uuid.uuid4()),
                    request_id=request_id,
                    curator_id=curator_id,
                )
                for curator_id in request.recommended_curator_ids
            ]
            uow.offers.save_many(offers)
            uow.requests.save(request)
            uow.commit()
            return [o.offer_id for o in offers]
