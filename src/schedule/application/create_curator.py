"""Use case: Create a new curator."""

import uuid

from schedule.domain.curator import Curator
from schedule.domain.ports import ScheduleUnitOfWork


class CreateCuratorUseCase:
    """Register a new curator with optional initial skills."""

    def __init__(self, uow: ScheduleUnitOfWork) -> None:
        self._uow = uow

    def execute(self, name: str, skills: list[str] | None = None) -> str:
        """Create a curator and return their curator_id."""
        with self._uow as uow:
            curator = Curator(
                curator_id=str(uuid.uuid4()),
                name=name,
                skills=skills or [],
            )
            uow.curators.save(curator)
            uow.commit()
            return curator.curator_id
