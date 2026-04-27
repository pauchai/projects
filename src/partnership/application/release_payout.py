"""ReleasePayoutUseCase — releases a curator's pending commission payout."""

from __future__ import annotations

from datetime import datetime, timezone

from partnership.domain.commission import Commission
from partnership.domain.ports import UnitOfWork


class ReleasePayoutUseCase:
    """Release a PENDING commission after hold period and threshold checks.

    Raises:
        LookupError: if the commission does not exist.
        PermissionError: if the requesting curator is not the commission owner.
        ValueError: propagated from Commission.release() — hold period not
            elapsed, total below minimum threshold, or already released.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        commission_id: str,
        curator_id: str,
        now: datetime | None = None,
    ) -> Commission:
        release_time = now or datetime.now(timezone.utc)

        with self._uow as uow:
            commission = uow.commissions.find_by_id(commission_id)
            if commission is None:
                raise LookupError(f"Commission '{commission_id}' not found.")
            if commission.curator_id != curator_id:
                raise PermissionError(
                    f"Curator '{curator_id}' is not the owner of commission "
                    f"'{commission_id}' (owned by '{commission.curator_id}')."
                )
            commission.release(now=release_time)
            uow.commissions.save(commission)
            uow.commit()
            return commission
