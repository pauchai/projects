"""RequestGuarantorUseCase — ward submits a guarantorship request."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from guarantorship.domain.guarantee_request import GuaranteeRequest
from guarantorship.domain.ports import GuarantorshipUnitOfWork


@dataclass
class RequestGuarantorCommand:
    ward_id: str
    guarantor_id: str
    message: str | None = None


class RequestGuarantorUseCase:
    def __init__(self, uow: GuarantorshipUnitOfWork) -> None:
        self._uow = uow

    def execute(self, cmd: RequestGuarantorCommand) -> GuaranteeRequest:
        with self._uow as uow:
            request = GuaranteeRequest(
                request_id=str(uuid.uuid4()),
                ward_id=cmd.ward_id,
                guarantor_id=cmd.guarantor_id,
                message=cmd.message,
            )
            uow.requests.save(request)
            uow.commit()
            return request
