"""RejectGuaranteeRequestUseCase — guarantor rejects an incoming request."""

from __future__ import annotations

from dataclasses import dataclass

from guarantorship.domain.ports import GuarantorshipUnitOfWork


@dataclass
class RejectGuaranteeRequestCommand:
    request_id: str
    guarantor_id: str  # must match the request's guarantor_id


class RejectGuaranteeRequestUseCase:
    def __init__(self, uow: GuarantorshipUnitOfWork) -> None:
        self._uow = uow

    def execute(self, cmd: RejectGuaranteeRequestCommand) -> None:
        with self._uow as uow:
            request = uow.requests.find_by_id(cmd.request_id)
            if request is None:
                raise LookupError(f"Guarantee request '{cmd.request_id}' not found")
            if request.guarantor_id != cmd.guarantor_id:
                raise PermissionError("Only the intended guarantor can reject this request")
            request.reject()
            uow.requests.save(request)
            uow.commit()
