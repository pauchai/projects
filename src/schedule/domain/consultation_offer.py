"""Schedule domain entity: ConsultationOffer."""

from datetime import datetime, timezone
from typing import Literal


ConsultationOfferStatus = Literal["pending", "accepted", "declined"]


class ConsultationOffer:
    """An offer sent to a specific curator to handle a consultation request.

    Coordinator broadcasts offers to recommended curators.
    The first curator to accept claims the request; others are declined.
    """

    def __init__(
        self,
        offer_id: str,
        request_id: str,
        curator_id: str,
    ) -> None:
        self.offer_id = offer_id
        self.request_id = request_id
        self.curator_id = curator_id
        self.status: ConsultationOfferStatus = "pending"
        self.offered_at: datetime = datetime.now(timezone.utc)
        self.responded_at: datetime | None = None

    def accept(self) -> None:
        """Curator accepts the offer."""
        if self.status != "pending":
            raise ValueError(
                f"Cannot accept offer with status '{self.status}'"
            )
        self.status = "accepted"
        self.responded_at = datetime.now(timezone.utc)

    def decline(self) -> None:
        """Curator declines the offer."""
        if self.status != "pending":
            raise ValueError(
                f"Cannot decline offer with status '{self.status}'"
            )
        self.status = "declined"
        self.responded_at = datetime.now(timezone.utc)

    def cancel(self) -> None:
        """Coordinator cancels a pending offer (e.g. another curator accepted)."""
        if self.status != "pending":
            raise ValueError(
                f"Cannot cancel offer with status '{self.status}'"
            )
        self.status = "declined"
        self.responded_at = datetime.now(timezone.utc)
