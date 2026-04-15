"""Tests for Topic entity."""

import pytest


class TestTopicCreation:
    """Topic is a discrete unit of knowledge within a module."""

    def test_stores_topic_id(self) -> None:
        from cohort_learning.domain.topic import Topic

        topic = Topic(topic_id="t1", title="React Hooks", position=0)
        assert topic.topic_id == "t1"

    def test_stores_title(self) -> None:
        from cohort_learning.domain.topic import Topic

        topic = Topic(topic_id="t1", title="React Hooks", position=0)
        assert topic.title == "React Hooks"

    def test_stores_position(self) -> None:
        from cohort_learning.domain.topic import Topic

        topic = Topic(topic_id="t1", title="React Hooks", position=0)
        assert topic.position == 0

    def test_description_defaults_to_empty(self) -> None:
        from cohort_learning.domain.topic import Topic

        topic = Topic(topic_id="t1", title="React Hooks", position=0)
        assert topic.description == ""

    def test_stores_description(self) -> None:
        from cohort_learning.domain.topic import Topic

        topic = Topic(
            topic_id="t1",
            title="React Hooks",
            position=0,
            description="Learn hooks",
        )
        assert topic.description == "Learn hooks"


class TestTopicValidation:
    """Topic requires non-empty title and non-negative position."""

    def test_raises_on_empty_title(self) -> None:
        from cohort_learning.domain.topic import Topic

        with pytest.raises(ValueError, match="title"):
            Topic(topic_id="t1", title="", position=0)

    def test_raises_on_whitespace_title(self) -> None:
        from cohort_learning.domain.topic import Topic

        with pytest.raises(ValueError, match="title"):
            Topic(topic_id="t1", title="   ", position=0)

    def test_raises_on_negative_position(self) -> None:
        from cohort_learning.domain.topic import Topic

        with pytest.raises(ValueError, match="position"):
            Topic(topic_id="t1", title="React Hooks", position=-1)
