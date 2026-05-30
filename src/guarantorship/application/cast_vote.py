"""CastVoteUseCase — a guarantor casts a compensation vote on a complaint."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from guarantorship.domain.complaint import CompensationVote, Complaint, Verdict
from guarantorship.domain.ports import GuarantorshipUnitOfWork


@dataclass
class CastVoteCommand:
    complaint_id: str
    voter_id: str
    vote: Verdict


def _collect_expected_voters(
    uow: GuarantorshipUnitOfWork,
    complaint: Complaint,
) -> list[str]:
    """Return guarantor_ids of both deal parties (at current escalation level)."""
    deal = uow.deals.find_by_id(complaint.deal_id)
    if deal is None:
        raise LookupError(f"Deal '{complaint.deal_id}' not found")

    if complaint.escalation_level == 0:
        # direct guarantors of both sides
        initiator_guarantors = [
            g.guarantor_id for g in uow.guarantorships.find_by_ward(deal.initiator_id)
        ]
        counterparty_guarantors = [
            g.guarantor_id for g in uow.guarantorships.find_by_ward(deal.counterparty_id)
        ]
        return list(set(initiator_guarantors + counterparty_guarantors))
    else:
        # escalated: guarantors-of-guarantors
        initiator_guarantors = [
            g.guarantor_id for g in uow.guarantorships.find_by_ward(deal.initiator_id)
        ]
        counterparty_guarantors = [
            g.guarantor_id for g in uow.guarantorships.find_by_ward(deal.counterparty_id)
        ]
        level1_guarantors = set(initiator_guarantors + counterparty_guarantors)
        level2: list[str] = []
        for g_id in level1_guarantors:
            level2 += [g.guarantor_id for g in uow.guarantorships.find_by_ward(g_id)]
        return list(set(level2))


class CastVoteUseCase:
    def __init__(self, uow: GuarantorshipUnitOfWork) -> None:
        self._uow = uow

    def execute(self, cmd: CastVoteCommand) -> Complaint:
        with self._uow as uow:
            complaint = uow.complaints.find_by_id(cmd.complaint_id)
            if complaint is None:
                raise LookupError(f"Complaint '{cmd.complaint_id}' not found")

            expected_voters = _collect_expected_voters(uow, complaint)
            if cmd.voter_id not in expected_voters:
                raise PermissionError("You are not a guarantor for this complaint")

            vote = CompensationVote(
                vote_id=str(uuid.uuid4()),
                complaint_id=cmd.complaint_id,
                voter_id=cmd.voter_id,
                vote=cmd.vote,
                created_at=datetime.now(timezone.utc),
            )
            complaint.cast_vote(vote)
            complaint.try_resolve(expected_voters)

            uow.complaints.save(complaint)
            uow.commit()
            return complaint
