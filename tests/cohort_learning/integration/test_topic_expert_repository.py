"""Integration tests for SqlAlchemyTopicExpertRepository.

Tests verify that TopicExpert entities can be saved to and loaded from
a real PostgreSQL database through the SQLAlchemy repository.
"""

from datetime import datetime, timezone

import pytest

from cohort_learning.domain.topic_expert import TopicExpert
from cohort_learning.infrastructure.sqlalchemy_repository import (
    SqlAlchemyTopicExpertRepository,
)


@pytest.fixture
def repo(integration_session):
    """Provide a TopicExpert repository backed by a real database session."""
    return SqlAlchemyTopicExpertRepository(integration_session)


class TestSqlAlchemyTopicExpertRepository:
    """Integration tests for TopicExpert persistence."""

    def test_save_and_find_by_id_round_trip(self, repo):
        """Saving and retrieving a TopicExpert by ID preserves all fields."""
        # Arrange
        expert = TopicExpert(
            expert_id="exp-1",
            learner_id="learner-1",
            topic_id="topic-1",
            cohort_id="cohort-1",
            validated_at=datetime(2026, 4, 15, 12, 0, 0, tzinfo=timezone.utc),
            validator_id="master-1",
        )

        # Act
        repo.save(expert)
        found = repo.find_by_id("exp-1")

        # Assert
        assert found is not None
        assert found.expert_id == "exp-1"
        assert found.learner_id == "learner-1"
        assert found.topic_id == "topic-1"
        assert found.cohort_id == "cohort-1"
        assert found.validated_at == datetime(
            2026, 4, 15, 12, 0, 0, tzinfo=timezone.utc
        )
        assert found.validator_id == "master-1"

    def test_find_by_id_returns_none_when_not_found(self, repo):
        """Finding a non-existent TopicExpert returns None."""
        # Act
        found = repo.find_by_id("nonexistent")

        # Assert
        assert found is None

    def test_find_by_learner_and_topic(self, repo):
        """Can find TopicExpert by learner, topic, and cohort."""
        # Arrange
        expert = TopicExpert(
            expert_id="exp-2",
            learner_id="learner-2",
            topic_id="topic-2",
            cohort_id="cohort-2",
            validated_at=datetime(2026, 4, 15, 12, 0, 0, tzinfo=timezone.utc),
            validator_id="master-2",
        )
        repo.save(expert)

        # Act
        found = repo.find_by_learner_and_topic("learner-2", "topic-2", "cohort-2")

        # Assert
        assert found is not None
        assert found.expert_id == "exp-2"

    def test_find_by_learner_and_topic_returns_none_when_not_found(self, repo):
        """Finding non-existent combination returns None."""
        # Act
        found = repo.find_by_learner_and_topic("learner-99", "topic-99", "cohort-99")

        # Assert
        assert found is None

    def test_find_by_cohort(self, repo):
        """Can find all TopicExperts in a cohort."""
        # Arrange
        expert1 = TopicExpert(
            expert_id="exp-3",
            learner_id="learner-3",
            topic_id="topic-1",
            cohort_id="cohort-3",
            validated_at=datetime(2026, 4, 15, 12, 0, 0, tzinfo=timezone.utc),
            validator_id="master-3",
        )
        expert2 = TopicExpert(
            expert_id="exp-4",
            learner_id="learner-4",
            topic_id="topic-2",
            cohort_id="cohort-3",
            validated_at=datetime(2026, 4, 15, 13, 0, 0, tzinfo=timezone.utc),
            validator_id="master-3",
        )
        expert3 = TopicExpert(
            expert_id="exp-5",
            learner_id="learner-5",
            topic_id="topic-3",
            cohort_id="cohort-999",  # different cohort
            validated_at=datetime(2026, 4, 15, 14, 0, 0, tzinfo=timezone.utc),
            validator_id="master-3",
        )
        repo.save(expert1)
        repo.save(expert2)
        repo.save(expert3)

        # Act
        experts = repo.find_by_cohort("cohort-3")

        # Assert
        assert len(experts) == 2
        expert_ids = {e.expert_id for e in experts}
        assert expert_ids == {"exp-3", "exp-4"}
