"""FileComplaintUseCase — file a complaint against a deal participant."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from guarantorship.domain.complaint import Complaint, ComplaintStatus
from guarantorship.domain.ports import GuarantorshipUnitOfWork

VOTING_PERIOD_DAYS = 7


@dataclass
class FileComplaintCommand:
    deal_id: str
    filed_by_id: str
    against_id: str
    description: str


class FileComplaintUseCase:
    def __init__(self, uow: GuarantorshipUnitOfWork) -> None:
        self._uow = uow

    def execute(self, cmd: FileComplaintCommand) -> Complaint:
        with self._uow as uow:
            deal = uow.deals.find_by_id(cmd.deal_id)
            if deal is None:
                raise LookupError(f"Deal '{cmd.deal_id}' not found")

            participants = {deal.initiator_id, deal.counterparty_id}
            if cmd.filed_by_id not in participants:
                raise PermissionError("Only deal participants can file a complaint")
            if cmd.against_id not in participants:
                raise ValueError("Complaint must be against the other deal participant")
            if cmd.filed_by_id == cmd.against_id:
                raise ValueError("Cannot file a complaint against yourself")

            now = datetime.now(timezone.utc)
            deadline = now + timedelta(days=VOTING_PERIOD_DAYS)

            complaint = Complaint(
                complaint_id=str(uuid.uuid4()),
                deal_id=cmd.deal_id,
                filed_by_id=cmd.filed_by_id,
                against_id=cmd.against_id,
                description=cmd.description,
                status=ComplaintStatus.VOTING,
                verdict=None,
                voting_deadline=deadline,
                escalation_level=0,
                created_at=now,
            )
            uow.complaints.save(complaint)
            uow.commit()
            return complaint
