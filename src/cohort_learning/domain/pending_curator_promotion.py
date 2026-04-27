"""PendingCuratorPromotion entity — signals a learner is ready for curator promotion.

Created by ``CuratorPromotionEligibleHandler`` when the
``CuratorPromotionEligible`` event is received.  Allows Masters to
discover which learners have met all helper-metric thresholds and are
waiting for the final promotion via ``PromoteToModuleCuratorUseCase``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class PendingCuratorPromotion:
    """Records that a learner's helper metrics qualify them for curator promotion.

    This is a notification record only — it does NOT represent a completed
    promotion.  The actual promotion still requires a Master to call
    ``PromoteToModuleCuratorUseCase``.
    """

    pending_id: str
    learner_id: str
    module_id: str
    cohort_id: str
    created_at: datetime

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PendingCuratorPromotion):
            return NotImplemented
        return self.pending_id == other.pending_id

    def __hash__(self) -> int:
        return hash(self.pending_id)
