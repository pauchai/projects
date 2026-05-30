from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Verdict(str, Enum):
    COMPENSATE_INITIATOR = "compensate_initiator"
    COMPENSATE_COUNTERPARTY = "compensate_counterparty"
    DISMISS = "dismiss"


class ComplaintStatus(str, Enum):
    OPEN = "open"
    VOTING = "voting"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


@dataclass
class CompensationVote:
    vote_id: str
    complaint_id: str
    voter_id: str
    vote: Verdict
    created_at: datetime


@dataclass
class Complaint:
    """A complaint filed by one deal participant against the other.

    Guarantors of both sides vote; consensus determines the verdict.
    If no consensus before deadline the complaint is escalated to
    guarantors-of-guarantors (one level by default, configurable).
    """

    complaint_id: str
    deal_id: str
    filed_by_id: str
    against_id: str
    description: str
    status: ComplaintStatus
    verdict: Verdict | None
    voting_deadline: datetime | None
    escalation_level: int
    created_at: datetime
    votes: list[CompensationVote] = field(default_factory=list)

    # ── business logic ───────────────────────────────────────────────────────

    def open_voting(self, deadline: datetime) -> None:
        if self.status != ComplaintStatus.OPEN:
            raise ValueError("Can only start voting on an open complaint.")
        self.status = ComplaintStatus.VOTING
        self.voting_deadline = deadline

    def cast_vote(self, vote: CompensationVote) -> None:
        if self.status not in (ComplaintStatus.VOTING, ComplaintStatus.ESCALATED):
            raise ValueError("Voting is not active for this complaint.")
        already = [v for v in self.votes if v.voter_id == vote.voter_id]
        if already:
            raise ValueError("Voter has already cast a vote for this complaint.")
        self.votes.append(vote)

    def try_resolve(self, expected_voter_ids: list[str]) -> bool:
        """Attempt to reach consensus.

        Returns True and sets verdict+status if all expected voters have
        voted and their votes are unanimous.
        """
        voted_ids = {v.voter_id for v in self.votes}
        if not set(expected_voter_ids).issubset(voted_ids):
            return False  # not everyone has voted yet

        tally: dict[str, int] = {}
        for v in self.votes:
            tally[v.vote] = tally.get(v.vote, 0) + 1

        if len(tally) == 1:
            # unanimous
            self.verdict = Verdict(next(iter(tally)))
            self.status = ComplaintStatus.RESOLVED
            return True

        return False  # no consensus

    def escalate(self) -> None:
        """Move to escalated state so guarantors-of-guarantors are invited."""
        if self.status != ComplaintStatus.VOTING:
            raise ValueError("Can only escalate a complaint in voting state.")
        self.status = ComplaintStatus.ESCALATED
        self.escalation_level += 1
        self.votes.clear()  # fresh vote round at escalated level
