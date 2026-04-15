"""Tests for ModuleProgression entity."""

import pytest

from cohort_learning.domain.topic import Topic


class TestModuleProgressionCreation:
    """ModuleProgression is an ordered sequence of topics."""

    def test_stores_module_id(self) -> None:
        from cohort_learning.domain.module_progression import ModuleProgression

        module = ModuleProgression(
            module_id="mod1",
            title="Frontend Basics",
            master_id="m1",
        )
        assert module.module_id == "mod1"

    def test_stores_title(self) -> None:
        from cohort_learning.domain.module_progression import ModuleProgression

        module = ModuleProgression(
            module_id="mod1",
            title="Frontend Basics",
            master_id="m1",
        )
        assert module.title == "Frontend Basics"

    def test_stores_master_id(self) -> None:
        from cohort_learning.domain.module_progression import ModuleProgression

        module = ModuleProgression(
            module_id="mod1",
            title="Frontend Basics",
            master_id="m1",
        )
        assert module.master_id == "m1"

    def test_starts_with_no_topics(self) -> None:
        from cohort_learning.domain.module_progression import ModuleProgression

        module = ModuleProgression(
            module_id="mod1",
            title="Frontend Basics",
            master_id="m1",
        )
        assert module.topics == []


class TestModuleProgressionTopicManagement:
    """Topics can be added and retrieved in order."""

    def test_add_topic(self) -> None:
        from cohort_learning.domain.module_progression import ModuleProgression

        module = ModuleProgression(
            module_id="mod1",
            title="Frontend Basics",
            master_id="m1",
        )
        topic = Topic(topic_id="t1", title="React Hooks", position=0)
        module.add_topic(topic)
        assert len(module.topics) == 1
        assert module.topics[0].topic_id == "t1"

    def test_add_multiple_topics(self) -> None:
        from cohort_learning.domain.module_progression import ModuleProgression

        module = ModuleProgression(
            module_id="mod1",
            title="Frontend Basics",
            master_id="m1",
        )
        module.add_topic(Topic(topic_id="t1", title="HTML", position=0))
        module.add_topic(Topic(topic_id="t2", title="CSS", position=1))
        module.add_topic(Topic(topic_id="t3", title="JS", position=2))
        assert len(module.topics) == 3

    def test_cannot_add_topic_with_duplicate_id(self) -> None:
        from cohort_learning.domain.module_progression import ModuleProgression

        module = ModuleProgression(
            module_id="mod1",
            title="Frontend Basics",
            master_id="m1",
        )
        module.add_topic(Topic(topic_id="t1", title="HTML", position=0))
        with pytest.raises(ValueError, match="already exists"):
            module.add_topic(Topic(topic_id="t1", title="HTML v2", position=1))

    def test_cannot_add_topic_with_duplicate_position(self) -> None:
        from cohort_learning.domain.module_progression import ModuleProgression

        module = ModuleProgression(
            module_id="mod1",
            title="Frontend Basics",
            master_id="m1",
        )
        module.add_topic(Topic(topic_id="t1", title="HTML", position=0))
        with pytest.raises(ValueError, match="position"):
            module.add_topic(Topic(topic_id="t2", title="CSS", position=0))

    def test_topic_count(self) -> None:
        from cohort_learning.domain.module_progression import ModuleProgression

        module = ModuleProgression(
            module_id="mod1",
            title="Frontend Basics",
            master_id="m1",
        )
        assert module.topic_count == 0
        module.add_topic(Topic(topic_id="t1", title="HTML", position=0))
        assert module.topic_count == 1

    def test_find_topic_by_id(self) -> None:
        from cohort_learning.domain.module_progression import ModuleProgression

        module = ModuleProgression(
            module_id="mod1",
            title="Frontend Basics",
            master_id="m1",
        )
        module.add_topic(Topic(topic_id="t1", title="HTML", position=0))
        found = module.find_topic("t1")
        assert found is not None
        assert found.title == "HTML"

    def test_find_topic_returns_none_for_missing(self) -> None:
        from cohort_learning.domain.module_progression import ModuleProgression

        module = ModuleProgression(
            module_id="mod1",
            title="Frontend Basics",
            master_id="m1",
        )
        assert module.find_topic("nonexistent") is None


class TestModuleProgressionValidation:
    """Module requires non-empty title."""

    def test_raises_on_empty_title(self) -> None:
        from cohort_learning.domain.module_progression import ModuleProgression

        with pytest.raises(ValueError, match="title"):
            ModuleProgression(module_id="mod1", title="", master_id="m1")

    def test_raises_on_whitespace_title(self) -> None:
        from cohort_learning.domain.module_progression import ModuleProgression

        with pytest.raises(ValueError, match="title"):
            ModuleProgression(module_id="mod1", title="   ", master_id="m1")
