"""JoinZeroCircleUseCase — user joins an existing open zero-guarantee circle."""

from __future__ import annotations

from dataclasses import dataclass

from guarantorship.domain.ports import GuarantorshipUnitOfWork


@dataclass
class JoinZeroCircleCommand:
    circle_id: str
    user_id: str


class JoinZeroCircleUseCase:
    def __init__(self, uow: GuarantorshipUnitOfWork) -> None:
        self._uow = uow

    def execute(self, cmd: JoinZeroCircleCommand) -> None:
        with self._uow as uow:
            existing = uow.circles.find_active_circle_for_user(cmd.user_id)
            if existing is not None:
                raise ValueError(
                    "You are already a member of an active zero circle. "
                    "A user can only belong to one active circle at a time."
                )
            circle = uow.circles.find_by_id(cmd.circle_id)
            if circle is None:
                raise LookupError(f"Zero circle '{cmd.circle_id}' not found")
            circle.add_member(cmd.user_id)
            uow.circles.save(circle)
            uow.commit()
