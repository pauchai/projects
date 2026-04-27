"""GetCuratorEarningsUseCase — returns all commissions for a curator."""

from __future__ import annotations

from partnership.domain.commission import Commission
from partnership.domain.ports import UnitOfWork


class GetCuratorEarningsUseCase:
    """Return the full commission history for a curator.

    Returns an empty list if the curator has no commissions.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, curator_id: str) -> list[Commission]:
        with self._uow as uow:
            return uow.commissions.find_by_curator(curator_id)
