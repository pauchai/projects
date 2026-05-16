"""CreateZeroCircleUseCase — initiates a new zero-guarantee DAO circle."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from guarantorship.domain.ports import GuarantorshipUnitOfWork
from guarantorship.domain.zero_circle import ZeroCircle


@dataclass
class CreateZeroCircleCommand:
    initiated_by: str
    name: str
    deposit_stub: Decimal | None = None


class CreateZeroCircleUseCase:
    def __init__(self, uow: GuarantorshipUnitOfWork) -> None:
        self._uow = uow

    def execute(self, cmd: CreateZeroCircleCommand) -> ZeroCircle:
        with self._uow as uow:
            existing = uow.circles.find_active_circle_for_user(cmd.initiated_by)
            if existing is not None:
                raise ValueError(
                    "You are already a member of an active zero circle. "
                    "A user can only belong to one active circle at a time."
                )
            circle = ZeroCircle(
                circle_id=str(uuid.uuid4()),
                name=cmd.name,
                initiated_by=cmd.initiated_by,
                deposit_stub=cmd.deposit_stub,
            )
            uow.circles.save(circle)
            uow.commit()
            return circle
