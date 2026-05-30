"""ModuleProgression entity — an ordered sequence of topics that defines a learning path."""

from __future__ import annotations

from cohort_learning.domain.topic import Topic


class ModuleProgression:
    """A learning module consisting of an ordered sequence of topics.

    Owned by a master who curates the content and guides learners
    through the progression.
    """

    def __init__(
        self,
        module_id: str,
        title: str,
        master_id: str,
        repo_url: str | None = None,
    ) -> None:
        if not title.strip():
            raise ValueError("Module title must not be empty")

        self.module_id = module_id
        self.title = title
        self.master_id = master_id
        self.repo_url = repo_url
        self._topics: list[Topic] = []

    @property
    def topics(self) -> list[Topic]:
        return list(self._topics)

    @property
    def topic_count(self) -> int:
        return len(self._topics)

    def add_topic(self, topic: Topic) -> None:
        """Add a topic to the module progression.

        Raises ValueError if a topic with the same id or position already exists.
        """
        for existing in self._topics:
            if existing.topic_id == topic.topic_id:
                raise ValueError(
                    f"Topic with id '{topic.topic_id}' already exists in module"
                )
            if existing.position == topic.position:
                raise ValueError(
                    f"Topic at position {topic.position} already exists in module"
                )
        self._topics.append(topic)

    def find_topic(self, topic_id: str) -> Topic | None:
        """Find a topic by its id. Returns None if not found."""
        for topic in self._topics:
            if topic.topic_id == topic_id:
                return topic
        return None
