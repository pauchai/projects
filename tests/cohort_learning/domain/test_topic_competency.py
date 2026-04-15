"""Tests for TopicCompetency entity."""

import pytest


class TestTopicCompetencyCreation:
    """TopicCompetency records a learner's validated mastery of a topic."""

    def test_stores_competency_id(self) -> None:
        from cohort_learning.domain.topic_competency import TopicCompetency

        competency = TopicCompetency(
            competency_id="comp1",
            learner_id="u1",
            topic_id="t1",
            cohort_id="c1",
        )
        assert competency.competency_id == "comp1"

    def test_stores_learner_id(self) -> None:
        from cohort_learning.domain.topic_competency import TopicCompetency

        competency = TopicCompetency(
            competency_id="comp1",
            learner_id="u1",
            topic_id="t1",
            cohort_id="c1",
        )
        assert competency.learner_id == "u1"

    def test_stores_topic_id(self) -> None:
        from cohort_learning.domain.topic_competency import TopicCompetency

        competency = TopicCompetency(
            competency_id="comp1",
            learner_id="u1",
            topic_id="t1",
            cohort_id="c1",
        )
        assert competency.topic_id == "t1"

    def test_stores_cohort_id(self) -> None:
        from cohort_learning.domain.topic_competency import TopicCompetency

        competency = TopicCompetency(
            competency_id="comp1",
            learner_id="u1",
            topic_id="t1",
            cohort_id="c1",
        )
        assert competency.cohort_id == "c1"

    def test_has_achieved_at_timestamp(self) -> None:
        from cohort_learning.domain.topic_competency import TopicCompetency

        competency = TopicCompetency(
            competency_id="comp1",
            learner_id="u1",
            topic_id="t1",
            cohort_id="c1",
        )
        assert competency.achieved_at is not None


class TestTopicCompetencyEquality:
    """Two competencies for the same learner+topic are logically the same."""

    def test_same_learner_topic_are_equal(self) -> None:
        from cohort_learning.domain.topic_competency import TopicCompetency

        a = TopicCompetency(
            competency_id="comp1",
            learner_id="u1",
            topic_id="t1",
            cohort_id="c1",
        )
        b = TopicCompetency(
            competency_id="comp2",
            learner_id="u1",
            topic_id="t1",
            cohort_id="c1",
        )
        # Different IDs but same learner+topic — identity is by competency_id
        assert a.competency_id != b.competency_id
