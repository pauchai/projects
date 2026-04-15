"""Module Curator entity — graduated learner authorized to curate modules."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ModuleCurator:
    """
    A graduated learner who has completed an entire Module Progression,
    achieved Topic Competency across all topics, demonstrated effective
    Peer Helper activity, and been promoted by the Master to curate future
    Learning Cohorts.

    Module Curator is the second level of partner progression:
    Learner → Topic Expert → Module Curator → Master

    Business rules:
    - Curator status is module-specific (not cross-module in V1)
    - Promotion is irreversible under normal circumstances
    - Curators can create/modify practice tasks, validate competency,
      and lead cohorts under master supervision
    - Curator is the first level that earns Monetary Rewards (commission)
    """

    curator_id: str
    learner_id: str
    module_id: str
    cohort_id: str  # cohort where status was earned
    promoted_at: datetime
    promoted_by: str  # Master who approved promotion

    def __eq__(self, other: object) -> bool:
        """Module Curators are identified by curator_id."""
        if not isinstance(other, ModuleCurator):
            return NotImplemented
        return self.curator_id == other.curator_id

    def __hash__(self) -> int:
        return hash(self.curator_id)
