"""Lesson entity — a concrete learning unit within a module volume."""

from __future__ import annotations

from datetime import datetime, timezone


class Lesson:
    """A single lesson inside a module's content volume.

    A lesson corresponds to one or more files on disk (content + optional
    homework). The paths are relative to the module's volume root:
    ``$VOLUMES_BASE_PATH/modules/<module_id>/``.

    A lesson may optionally be linked to a Topic, which connects it to the
    competency tracking system (TopicCompetency, TopicExpert, etc.).
    """

    def __init__(
        self,
        lesson_id: str,
        module_id: str,
        title: str,
        position: int,
        topic_id: str | None = None,
        content_path: str | None = None,
        homework_path: str | None = None,
    ) -> None:
        if not title.strip():
            raise ValueError("Lesson title must not be empty")
        if position < 0:
            raise ValueError("Lesson position must be non-negative")

        self.lesson_id = lesson_id
        self.module_id = module_id
        self.title = title
        self.position = position
        self.topic_id = topic_id
        self.content_path = content_path
        self.homework_path = homework_path
        self.created_at: datetime = datetime.now(timezone.utc)

    def update(
        self,
        title: str | None = None,
        position: int | None = None,
        topic_id: str | None = None,
        content_path: str | None = None,
        homework_path: str | None = None,
    ) -> None:
        """Update mutable lesson fields."""
        if title is not None:
            if not title.strip():
                raise ValueError("Lesson title must not be empty")
            self.title = title
        if position is not None:
            if position < 0:
                raise ValueError("Lesson position must be non-negative")
            self.position = position
        if topic_id is not None:
            self.topic_id = topic_id
        if content_path is not None:
            self.content_path = content_path
        if homework_path is not None:
            self.homework_path = homework_path

    def has_homework(self) -> bool:
        """Return True if this lesson has an associated homework file."""
        return self.homework_path is not None
