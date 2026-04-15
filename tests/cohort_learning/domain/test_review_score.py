"""Tests for ReviewScore value object."""

import pytest
from dataclasses import FrozenInstanceError

from cohort_learning.domain.review_score import ReviewScore


class TestReviewScoreCreation:
    """ReviewScore is a frozen value object holding a criterion score (1-5)."""

    def test_stores_criterion_name(self) -> None:
        score = ReviewScore(criterion="clarity", score=4)
        assert score.criterion == "clarity"

    def test_stores_score(self) -> None:
        score = ReviewScore(criterion="clarity", score=4)
        assert score.score == 4

    def test_comment_defaults_to_empty(self) -> None:
        score = ReviewScore(criterion="clarity", score=4)
        assert score.comment == ""

    def test_stores_comment(self) -> None:
        score = ReviewScore(criterion="clarity", score=4, comment="Good work")
        assert score.comment == "Good work"

    def test_is_frozen(self) -> None:
        score = ReviewScore(criterion="clarity", score=4)
        with pytest.raises(FrozenInstanceError):
            score.score = 5  # type: ignore[misc]


class TestReviewScoreValidation:
    """ReviewScore rejects invalid scores outside 1-5 range."""

    def test_score_of_1_is_valid(self) -> None:
        score = ReviewScore(criterion="clarity", score=1)
        assert score.score == 1

    def test_score_of_5_is_valid(self) -> None:
        score = ReviewScore(criterion="clarity", score=5)
        assert score.score == 5

    def test_score_of_0_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="between 1 and 5"):
            ReviewScore(criterion="clarity", score=0)

    def test_score_of_6_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="between 1 and 5"):
            ReviewScore(criterion="clarity", score=6)

    def test_negative_score_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="between 1 and 5"):
            ReviewScore(criterion="clarity", score=-1)

    def test_empty_criterion_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="criterion"):
            ReviewScore(criterion="", score=3)

    def test_whitespace_criterion_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="criterion"):
            ReviewScore(criterion="   ", score=3)


class TestReviewScoreEquality:
    """Two ReviewScores with the same fields are equal (value object semantics)."""

    def test_equal_scores(self) -> None:
        a = ReviewScore(criterion="clarity", score=4, comment="Good")
        b = ReviewScore(criterion="clarity", score=4, comment="Good")
        assert a == b

    def test_different_scores_are_not_equal(self) -> None:
        a = ReviewScore(criterion="clarity", score=4)
        b = ReviewScore(criterion="clarity", score=3)
        assert a != b
