"""PromoteToTopicExpert use case."""

from datetime import datetime, timezone

from cohort_learning.application._helpers import (
    get_cohort_or_raise,
    require_master_or_curator,
)
from cohort_learning.domain.events import TopicExpertPromoted
from cohort_learning.domain.ports import UnitOfWork
from cohort_learning.domain.topic_expert import TopicExpert


class PromoteToTopicExpertUseCase:
    """Promote a learner to Topic Expert status after competency validation.

    Prerequisite: Learner must have passed Topic Competency validation for
    this topic (via ValidateTopicCompetencyUseCase).

    Only Master or Module Curator can promote to Topic Expert.

    Business rules:
    - One learner can only be Topic Expert once per topic
    - Same learner can be expert in multiple topics
    - Status is permanent (cannot be revoked under normal circumstances)
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        expert_id: str,
        learner_id: str,
        topic_id: str,
        cohort_id: str,
        validator_id: str,
    ) -> TopicExpert:
        with self._uow as uow:
            cohort = get_cohort_or_raise(uow, cohort_id)
            require_master_or_curator(cohort, validator_id)

            # Check if learner is already a Topic Expert for this topic
            existing_expert = uow.topic_experts.find_by_learner_and_topic(
                learner_id, topic_id
            )
            if existing_expert is not None:
                raise ValueError(
                    f"Learner '{learner_id}' is already a Topic Expert for topic '{topic_id}'"
                )

            # Create TopicExpert entity
            expert = TopicExpert(
                expert_id=expert_id,
                learner_id=learner_id,
                topic_id=topic_id,
                cohort_id=cohort_id,
                validated_at=datetime.now(timezone.utc),
                validator_id=validator_id,
            )

            # Emit domain event
            event = TopicExpertPromoted(
                learner_id=learner_id,
                topic_id=topic_id,
                cohort_id=cohort_id,
            )
            uow.collect_events([event])

            uow.topic_experts.save(expert)
            uow.commit()
            return expert
