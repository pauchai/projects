"""TopicCompetency entity — validated mastery of a topic by a learner."""

from datetime import datetime, timezone


class TopicCompetency:
    """Records that a learner has demonstrated competency in a specific topic."""

    def __init__(
        self,
        competency_id: str,
        learner_id: str,
        topic_id: str,
        cohort_id: str,
    ) -> None:
        self.competency_id = competency_id
        self.learner_id = learner_id
        self.topic_id = topic_id
        self.cohort_id = cohort_id
        self.achieved_at: datetime = datetime.now(timezone.utc)
