"""Tests for PromoteToTopicExpert use case."""

from datetime import datetime, timezone

import pytest

from cohort_learning.application.promote_to_topic_expert import (
    PromoteToTopicExpertUseCase,
)
from cohort_learning.domain.events import TopicExpertPromoted
from cohort_learning.domain.topic_competency import TopicCompetency
from shared_kernel.events import DomainEvent
from tests.cohort_learning.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.cohort_learning.factories import make_active_cohort, save_cohort


def _seed_competency(
    uow: FakeUnitOfWork, learner_id: str, topic_id: str, cohort_id: str
) -> None:
    """Persist a TopicCompetency so promote-to-expert can find it."""
    competency = TopicCompetency(
        competency_id=f"{learner_id}-{topic_id}-{cohort_id}",
        learner_id=learner_id,
        topic_id=topic_id,
        cohort_id=cohort_id,
    )
    with uow:
        uow.topic_competencies.save(competency)
        uow.commit()


class _SpyEventBus:
    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    def publish(self, events: list[DomainEvent]) -> None:
        self.published.extend(events)


class TestPromoteToTopicExpertUseCase:
    """Promote a learner to Topic Expert status after validation."""

    def test_creates_topic_expert_entity(self) -> None:
        """When promotion succeeds, creates TopicExpert entity."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)
        _seed_competency(uow, "learner1", "t1", "c1")

        use_case = PromoteToTopicExpertUseCase(uow=uow)

        use_case.execute(
            expert_id="exp1",
            learner_id="learner1",
            topic_id="t1",
            cohort_id="c1",
            validator_id="master1",
        )

        expert = uow.topic_experts.find_by_id("exp1")
        assert expert is not None
        assert expert.learner_id == "learner1"
        assert expert.topic_id == "t1"
        assert expert.validator_id == "master1"

    def test_raises_when_learner_already_topic_expert(self) -> None:
        """Cannot promote same learner to expert in the same topic twice."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)
        _seed_competency(uow, "learner1", "t1", "c1")

        use_case = PromoteToTopicExpertUseCase(uow=uow)

        # First promotion succeeds
        use_case.execute(
            expert_id="exp1",
            learner_id="learner1",
            topic_id="t1",
            cohort_id="c1",
            validator_id="master1",
        )

        # Second promotion should fail
        with pytest.raises(ValueError, match="already a Topic Expert"):
            use_case.execute(
                expert_id="exp2",
                learner_id="learner1",
                topic_id="t1",
                cohort_id="c1",
                validator_id="master1",
            )

    def test_allows_same_learner_as_expert_in_different_topics(self) -> None:
        """Learner can be promoted to expert in multiple topics."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)
        _seed_competency(uow, "learner1", "t1", "c1")
        _seed_competency(uow, "learner1", "t2", "c1")

        use_case = PromoteToTopicExpertUseCase(uow=uow)

        use_case.execute(
            expert_id="exp1",
            learner_id="learner1",
            topic_id="t1",
            cohort_id="c1",
            validator_id="master1",
        )

        use_case.execute(
            expert_id="exp2",
            learner_id="learner1",
            topic_id="t2",  # Different topic
            cohort_id="c1",
            validator_id="master1",
        )

        expert_t1 = uow.topic_experts.find_by_learner_and_topic("learner1", "t1", "c1")
        expert_t2 = uow.topic_experts.find_by_learner_and_topic("learner1", "t2", "c1")

        assert expert_t1 is not None
        assert expert_t2 is not None

    def test_raises_when_caller_is_not_master_or_curator(self) -> None:
        """Only master or module curator can promote to Topic Expert."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)

        use_case = PromoteToTopicExpertUseCase(uow=uow)

        with pytest.raises(
            PermissionError,
            match="Only the cohort master or module curator",
        ):
            use_case.execute(
                expert_id="exp1",
                learner_id="learner1",
                topic_id="t1",
                cohort_id="c1",
                validator_id="outsider",  # Not master or curator
            )

    def test_raises_when_cohort_not_found(self) -> None:
        """Promotion fails if cohort doesn't exist."""
        uow = FakeUnitOfWork()
        use_case = PromoteToTopicExpertUseCase(uow=uow)

        with pytest.raises(LookupError, match="Cohort.*not found"):
            use_case.execute(
                expert_id="exp1",
                learner_id="learner1",
                topic_id="t1",
                cohort_id="nonexistent",
                validator_id="master1",
            )

    def test_emits_topic_expert_promoted_event(self) -> None:
        """When promotion succeeds, emits TopicExpertPromoted event."""
        spy_bus = _SpyEventBus()
        uow = FakeUnitOfWork(event_bus=spy_bus)
        cohort = make_active_cohort()
        save_cohort(uow, cohort)
        _seed_competency(uow, "learner1", "t1", "c1")

        use_case = PromoteToTopicExpertUseCase(uow=uow)

        use_case.execute(
            expert_id="exp1",
            learner_id="learner1",
            topic_id="t1",
            cohort_id="c1",
            validator_id="master1",
        )

        events = [e for e in spy_bus.published if isinstance(e, TopicExpertPromoted)]
        assert len(events) == 1
        assert events[0].learner_id == "learner1"
        assert events[0].topic_id == "t1"

    def test_commits_transaction(self) -> None:
        """Use case commits the transaction after promotion."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        save_cohort(uow, cohort)
        _seed_competency(uow, "learner1", "t1", "c1")

        use_case = PromoteToTopicExpertUseCase(uow=uow)

        use_case.execute(
            expert_id="exp1",
            learner_id="learner1",
            topic_id="t1",
            cohort_id="c1",
            validator_id="master1",
        )

        assert uow.committed is True
