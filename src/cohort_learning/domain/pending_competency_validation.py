"""PendingCompetencyValidation entity — signals a learner is ready for validation.

Created by ``CompetencyPrerequisitesMetHandler`` when the
``CompetencyPrerequisitesMet`` event is received.  Allows Masters and
Curators to discover which learners have satisfied the automatic
prerequisites and are waiting for knowledge-check validation via
``ValidateTopicCompetencyUseCase``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class PendingCompetencyValidation:
    """Records that a learner's automatic competency prerequisites are met.

    This is a notification record only — it does NOT represent a validated
    competency.  The actual validation still requires a Master or Curator to
    call ``ValidateTopicCompetencyUseCase`` with ``knowledge_check_score``
    and ``mentor_approved``.
    """

    pending_id: str
    learner_id: str
    topic_id: str
    cohort_id: str
    created_at: datetime

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PendingCompetencyValidation):
            return NotImplemented
        return self.pending_id == other.pending_id

    def __hash__(self) -> int:
        return hash(self.pending_id)
