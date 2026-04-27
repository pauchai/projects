"""Rewards routes: REST endpoints for learner reward balances and cohort leaderboard."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from cohort_learning.api.dependencies import get_cohort_uow, get_current_user_id
from cohort_learning.api.schemas import (
    LeaderboardEntryResponse,
    RewardBalanceResponse,
    RewardEntryResponse,
)
from cohort_learning.domain.reward_entry import RewardEntry
from cohort_learning.domain.reward_ledger import RewardBalance
from cohort_learning.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork,
)

router = APIRouter(tags=["rewards"])


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def _balance_to_response(balance: RewardBalance) -> RewardBalanceResponse:
    return RewardBalanceResponse(
        learner_id=balance.learner_id,
        total_xp=balance.total_xp,
        total_credits=balance.total_credits,
        badges=balance.badges,
        reputation_score=balance.reputation_score,
    )


def _entry_to_response(entry: RewardEntry) -> RewardEntryResponse:
    return RewardEntryResponse(
        entry_id=entry.entry_id,
        learner_id=entry.learner_id,
        reward_type=entry.reward_type,
        amount=entry.amount,
        metadata=entry.metadata,
        granted_at=entry.granted_at,
        triggering_event=entry.triggering_event,
        cohort_id=entry.cohort_id,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/me/rewards", response_model=RewardBalanceResponse)
def get_my_reward_balance(
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> RewardBalanceResponse:
    """
    Get the current authenticated learner's accumulated reward balance.

    Returns XP total, credits (capped at 50%), earned badge topic IDs,
    and the most recent reputation score.

    Authorization: any authenticated user (own data only).
    """
    with uow:
        ledger = uow.reward_ledgers.find_by_learner(caller_id)
        if ledger is None:
            # Return empty balance — ledger is created on first reward grant
            from cohort_learning.domain.reward_ledger import RewardBalance

            balance = RewardBalance(
                learner_id=caller_id,
                total_xp=0,
                total_credits=0,
                badges=[],
                reputation_score=None,
            )
        else:
            balance = ledger.get_balance()
        return _balance_to_response(balance)


@router.get("/me/rewards/history", response_model=list[RewardEntryResponse])
def get_my_reward_history(
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> list[RewardEntryResponse]:
    """
    Get the current authenticated learner's full reward history.

    Returns all ledger entries in the order they were granted, covering all
    reward types: XP, badges, credits, and reputation.

    Authorization: any authenticated user (own data only).
    """
    with uow:
        ledger = uow.reward_ledgers.find_by_learner(caller_id)
        if ledger is None:
            return []
        return [_entry_to_response(e) for e in ledger.entries]


@router.get(
    "/cohorts/{cohort_id}/leaderboard",
    response_model=list[LeaderboardEntryResponse],
)
def get_cohort_xp_leaderboard(
    cohort_id: str,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> list[LeaderboardEntryResponse]:
    """
    Get the XP leaderboard for all active members of a cohort.

    Ranks learners by total accumulated XP, highest first.  Learners with no
    rewards yet appear at the bottom with 0 XP.

    Authorization: cohort member (Master, Curator, or Learner in the cohort).
    """
    with uow:
        cohort = uow.cohorts.find_by_id(cohort_id)
        if cohort is None:
            raise HTTPException(status_code=404, detail=f"Cohort {cohort_id} not found")

        # Authorisation: caller must be master or active member
        is_master = cohort.master_id == caller_id
        is_member = any(
            m.learner_id == caller_id and m.is_active for m in cohort.memberships
        )
        if not (is_master or is_member):
            raise HTTPException(
                status_code=403,
                detail=f"User {caller_id} is not a member of cohort {cohort_id}",
            )

        # Collect all active member learner IDs (including the master)
        learner_ids: list[str] = [cohort.master_id]
        learner_ids.extend(m.learner_id for m in cohort.memberships if m.is_active)
        # De-duplicate while preserving insertion order
        seen: set[str] = set()
        unique_learner_ids: list[str] = []
        for lid in learner_ids:
            if lid not in seen:
                seen.add(lid)
                unique_learner_ids.append(lid)

        # Load each learner's ledger and compute XP
        xp_by_learner: list[tuple[str, int]] = []
        for learner_id in unique_learner_ids:
            ledger = uow.reward_ledgers.find_by_learner(learner_id)
            xp = ledger.get_balance().total_xp if ledger is not None else 0
            xp_by_learner.append((learner_id, xp))

        # Sort descending by XP, then ascending by learner_id for stable ordering
        xp_by_learner.sort(key=lambda t: (-t[1], t[0]))

        return [
            LeaderboardEntryResponse(learner_id=lid, total_xp=xp, rank=rank + 1)
            for rank, (lid, xp) in enumerate(xp_by_learner)
        ]
