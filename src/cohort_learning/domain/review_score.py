"""ReviewScore value object — a score for a single review criterion."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewScore:
    """Immutable score for a single review criterion on a 1-5 scale.

    Used within PeerReview to record per-criterion assessments.
    """

    criterion: str
    score: int
    comment: str = ""

    def __post_init__(self) -> None:
        if not self.criterion.strip():
            raise ValueError("Review criterion must not be empty")
        if not 1 <= self.score <= 5:
            raise ValueError("Review score must be between 1 and 5")
