"""Use case: Curator responds to a consultation offer."""

from schedule.domain.ports import ScheduleUnitOfWork


class RespondToOfferUseCase:
    """Curator accepts or declines a consultation offer.

    On accept: all other pending offers for the same request are cancelled.
    On decline: offer is marked declined; if no pending offers remain,
    the request stays negotiating (coordinator must re-trigger or cancel).
    """

    def __init__(self, uow: ScheduleUnitOfWork) -> None:
        self._uow = uow

    def accept(self, offer_id: str) -> None:
        """Curator accepts the offer. Cancels all other pending offers."""
        with self._uow as uow:
            offer = uow.offers.find_by_id(offer_id)
            if offer is None:
                raise LookupError(f"Offer '{offer_id}' not found")

            offer.accept()

            # Cancel all other pending offers for the same request
            sibling_offers = uow.offers.find_by_request_id(offer.request_id)
            for sibling in sibling_offers:
                if sibling.offer_id != offer_id and sibling.status == "pending":
                    sibling.cancel()
                    uow.offers.save(sibling)

            uow.offers.save(offer)
            uow.commit()

    def decline(self, offer_id: str) -> None:
        """Curator declines the offer."""
        with self._uow as uow:
            offer = uow.offers.find_by_id(offer_id)
            if offer is None:
                raise LookupError(f"Offer '{offer_id}' not found")

            offer.decline()
            uow.offers.save(offer)
            uow.commit()
