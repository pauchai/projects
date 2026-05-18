"""AcceptGuaranteeRequestUseCase — guarantor accepts an incoming request.

On acceptance:
- checks guarantor ward limit (platform settings)
- marks the GuaranteeRequest as accepted
- creates a Guarantorship record
- back-links the request to the new guarantorship
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from guarantorship.domain.guarantorship import Guarantorship
from guarantorship.domain.ports import GuarantorshipUnitOfWork


@dataclass
class AcceptGuaranteeRequestCommand:
    request_id: str
    guarantor_id: str  # must match the request's guarantor_id


class AcceptGuaranteeRequestUseCase:
    def __init__(self, uow: GuarantorshipUnitOfWork) -> None:
        self._uow = uow

    def execute(self, cmd: AcceptGuaranteeRequestCommand) -> Guarantorship:
        with self._uow as uow:
            request = uow.requests.find_by_id(cmd.request_id)
            if request is None:
                raise LookupError(f"Guarantee request '{cmd.request_id}' not found")
            if request.guarantor_id != cmd.guarantor_id:
                raise PermissionError("Only the intended guarantor can accept this request")

            # enforce ward limit
            settings = uow.settings.get()
            current_ward_count = uow.guarantorships.count_wards_for_guarantor(cmd.guarantor_id)
            if current_ward_count >= settings.guarantor_ward_limit:
                raise ValueError(
                    f"Guarantor has reached the ward limit ({settings.guarantor_ward_limit})"
                )

            request.accept()
            uow.requests.save(request)

            guarantorship = Guarantorship(
                guarantorship_id=str(uuid.uuid4()),
                guarantor_id=cmd.guarantor_id,
                ward_id=request.ward_id,
                request_id=cmd.request_id,
                created_at=datetime.now(timezone.utc),
            )
            uow.guarantorships.save(guarantorship)

            # back-link
            request.converted_to_guarantorship_id = guarantorship.guarantorship_id
            uow.requests.save(request)

            uow.commit()
            return guarantorship
