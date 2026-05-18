"""EscalateComplaintUseCase — escalate when voting deadline is exceeded."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from guarantorship.domain.complaint import Complaint
from guarantorship.domain.ports import GuarantorshipUnitOfWork

ESCALATED_VOTING_PERIOD_DAYS = 7


@dataclass
class EscalateComplaintCommand:
    complaint_id: str


class EscalateComplaintUseCase:
    def __init__(self, uow: GuarantorshipUnitOfWork) -> None:
        self._uow = uow

    def execute(self, cmd: EscalateComplaintCommand) -> Complaint:
        with self._uow as uow:
            complaint = uow.complaints.find_by_id(cmd.complaint_id)
            if complaint is None:
                raise LookupError(f"Complaint '{cmd.complaint_id}' not found")

            settings = uow.settings.get()
            if complaint.escalation_level >= settings.escalation_levels:
                raise ValueError(
                    f"Maximum escalation level ({settings.escalation_levels}) reached"
                )

            now = datetime.now(timezone.utc)
            if complaint.voting_deadline and complaint.voting_deadline > now:
                raise ValueError("Voting deadline has not passed yet")

            complaint.escalate()
            complaint.voting_deadline = now + timedelta(days=ESCALATED_VOTING_PERIOD_DAYS)
            uow.complaints.save(complaint)
            uow.commit()
            return complaint
