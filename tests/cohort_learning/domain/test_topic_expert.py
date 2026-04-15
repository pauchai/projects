"""Tests for TopicExpert entity."""

import pytest
from datetime import datetime, UTC

from cohort_learning.domain.topic_expert import TopicExpert


class TestTopicExpertCreation:
    def test_create_topic_expert_with_valid_data(self) -> None:
        # Arrange & Act
        expert = TopicExpert(
            expert_id="exp-1",
            learner_id="learner-1",
            topic_id="topic-react-hooks",
            cohort_id="cohort-1",
            validated_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
            validator_id="master-1",
        )

        # Assert
        assert expert.expert_id == "exp-1"
        assert expert.learner_id == "learner-1"
        assert expert.topic_id == "topic-react-hooks"
        assert expert.cohort_id == "cohort-1"
        assert expert.validated_at == datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC)
        assert expert.validator_id == "master-1"

    def test_topic_expert_is_immutable_after_creation(self) -> None:
        # Arrange
        expert = TopicExpert(
            expert_id="exp-1",
            learner_id="learner-1",
            topic_id="topic-react-hooks",
            cohort_id="cohort-1",
            validated_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
            validator_id="master-1",
        )

        # Act & Assert — expert status is permanent, cannot be revoked
        with pytest.raises(AttributeError):
            expert.learner_id = "learner-2"  # type: ignore


class TestTopicExpertEquality:
    def test_topic_experts_equal_by_expert_id(self) -> None:
        # Arrange
        expert1 = TopicExpert(
            expert_id="exp-1",
            learner_id="learner-1",
            topic_id="topic-react-hooks",
            cohort_id="cohort-1",
            validated_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
            validator_id="master-1",
        )
        expert2 = TopicExpert(
            expert_id="exp-1",
            learner_id="learner-999",  # different learner
            topic_id="topic-other",  # different topic
            cohort_id="cohort-999",
            validated_at=datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC),
            validator_id="other",
        )

        # Act & Assert — identity by expert_id
        assert expert1 == expert2

    def test_different_expert_ids_not_equal(self) -> None:
        # Arrange
        expert1 = TopicExpert(
            expert_id="exp-1",
            learner_id="learner-1",
            topic_id="topic-react-hooks",
            cohort_id="cohort-1",
            validated_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
            validator_id="master-1",
        )
        expert2 = TopicExpert(
            expert_id="exp-2",
            learner_id="learner-1",  # same learner
            topic_id="topic-react-hooks",  # same topic
            cohort_id="cohort-1",
            validated_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
            validator_id="master-1",
        )

        # Act & Assert
        assert expert1 != expert2


class TestTopicExpertBusinessRules:
    def test_same_learner_can_be_expert_in_multiple_topics(self) -> None:
        # Arrange
        expert_react = TopicExpert(
            expert_id="exp-1",
            learner_id="learner-1",
            topic_id="topic-react-hooks",
            cohort_id="cohort-1",
            validated_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
            validator_id="master-1",
        )
        expert_state = TopicExpert(
            expert_id="exp-2",
            learner_id="learner-1",  # same learner
            topic_id="topic-state-management",  # different topic
            cohort_id="cohort-1",
            validated_at=datetime(2026, 4, 16, 10, 0, 0, tzinfo=UTC),
            validator_id="master-1",
        )

        # Act & Assert — learner can be expert in multiple topics
        assert expert_react.learner_id == expert_state.learner_id
        assert expert_react.topic_id != expert_state.topic_id
        assert expert_react != expert_state

    def test_expert_status_persists_across_cohorts(self) -> None:
        # Arrange — expert from cohort-1 can help in cohort-2
        expert_cohort1 = TopicExpert(
            expert_id="exp-1",
            learner_id="learner-1",
            topic_id="topic-react-hooks",
            cohort_id="cohort-1",  # earned in cohort 1
            validated_at=datetime(2026, 4, 15, 10, 0, 0, tzinfo=UTC),
            validator_id="master-1",
        )

        # Act & Assert — cohort_id indicates where status was earned,
        # not where it can be used (cross-cohort helping allowed)
        assert expert_cohort1.cohort_id == "cohort-1"
        # Expert can help in cohort-2 with same topic (validated by application layer)
