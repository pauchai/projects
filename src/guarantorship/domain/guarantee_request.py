"""GuaranteeRequest entity — a ward's request to a potential guarantor.

A ward submits a request to a specific user (identified by guarantor_id).
The guarantor can accept or reject. Accepted requests are converted into
active Guarantee relationships by the application layer.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum


class GuaranteeRequestStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class GuaranteeRequest:
    """A pending or resolved request from a ward to a guarantor.

    Attributes:
        request_id:    Unique identifier.
        ward_id:       User ID of the person requesting guarantorship.
        guarantor_id:  User ID of the intended guarantor.
        status:        Current status (pending / accepted / rejected).
        message:       Optional message from the ward.
        created_at:    When the request was submitted.
        responded_at:  When the guarantor responded (if applicable).
    """

    def __init__(
        self,
        request_id: str,
        ward_id: str,
        guarantor_id: str,
        *,
        status: GuaranteeRequestStatus = GuaranteeRequestStatus.PENDING,
        message: str | None = None,
        created_at: datetime | None = None,
        responded_at: datetime | None = None,
    ) -> None:
        if ward_id == guarantor_id:
            raise ValueError("A user cannot request guarantorship from themselves")
        self.request_id = request_id
        self.ward_id = ward_id
        self.guarantor_id = guarantor_id
        self.status = status
        self.message = message
        self.created_at = created_at or datetime.now(timezone.utc)
        self.responded_at = responded_at

    def accept(self) -> None:
        """Accept the request. Raises if not pending."""
        if self.status != GuaranteeRequestStatus.PENDING:
            raise ValueError(f"Cannot accept a request with status '{self.status}'")
        self.status = GuaranteeRequestStatus.ACCEPTED
        self.responded_at = datetime.now(timezone.utc)

    def reject(self) -> None:
        """Reject the request. Raises if not pending."""
        if self.status != GuaranteeRequestStatus.PENDING:
            raise ValueError(f"Cannot reject a request with status '{self.status}'")
        self.status = GuaranteeRequestStatus.REJECTED
        self.responded_at = datetime.now(timezone.utc)
