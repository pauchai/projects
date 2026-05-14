"""Guarantee entity — a trust relationship between two platform users.

Guarantorship is a platform-level concept, independent of any project.
All users who participate in the platform are connected into a trust network
through guarantor relationships. In the future this network will be anchored
to a blockchain for immutability and transparency.
"""

from __future__ import annotations

from datetime import datetime, timezone

from guarantorship.domain.guarantee_status import GuaranteeStatus


class Guarantee:
    """A unidirectional trust assertion: guarantor vouches for guaranteed_user.

    Attributes:
        guarantee_id:    Unique identifier for this relationship.
        guarantor_id:    User ID of the person who vouches.
        guaranteed_id:   User ID of the person being vouched for.
        status:          Current lifecycle status (active / revoked).
        created_at:      Timestamp when the guarantee was established.
        revoked_at:      Timestamp when the guarantee was revoked (if applicable).
        blockchain_tx:   Future: transaction hash on the blockchain ledger.
    """

    def __init__(
        self,
        guarantee_id: str,
        guarantor_id: str,
        guaranteed_id: str,
        *,
        status: GuaranteeStatus = GuaranteeStatus.ACTIVE,
        created_at: datetime | None = None,
        revoked_at: datetime | None = None,
        blockchain_tx: str | None = None,
    ) -> None:
        if guarantor_id == guaranteed_id:
            raise ValueError("A user cannot guarantee themselves")
        self.guarantee_id = guarantee_id
        self.guarantor_id = guarantor_id
        self.guaranteed_id = guaranteed_id
        self.status = status
        self.created_at = created_at or datetime.now(timezone.utc)
        self.revoked_at = revoked_at
        self.blockchain_tx = blockchain_tx

    def revoke(self) -> None:
        """Revoke this guarantee. Raises if already revoked."""
        if self.status == GuaranteeStatus.REVOKED:
            raise ValueError("Guarantee is already revoked")
        self.status = GuaranteeStatus.REVOKED
        self.revoked_at = datetime.now(timezone.utc)
