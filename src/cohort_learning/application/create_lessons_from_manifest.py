"""Use case: Create/update Lessons from a ``lessons.json`` manifest file.

After a volume is synced, this use case reads the manifest from the
volume root and upserts all lessons into the database.

Manifest format (``$VOLUMES_BASE_PATH/modules/<module_id>/lessons.json``)::

    [
        {
            "lesson_id": "l-01",
            "title": "Introduction to Python",
            "position": 0,
            "topic_id": "topic-python-basics",   // optional
            "content_path": "01-intro/content.md",  // optional, relative to volume root
            "homework_path": "01-intro/homework.md" // optional
        },
        ...
    ]

Rules:
- ``lesson_id`` and ``title`` and ``position`` are required.
- ``topic_id``, ``content_path``, ``homework_path`` are optional.
- Lessons not present in the manifest are left untouched (no deletion).
- Only the module master may invoke this use case.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from cohort_learning.domain.lesson import Lesson
from cohort_learning.domain.ports import UnitOfWork

_MANIFEST_FILENAME = "lessons.json"


def _get_volumes_base() -> Path:
    return Path(os.environ.get("VOLUMES_BASE_PATH", "./volumes"))


def _parse_manifest(manifest_path: Path) -> list[dict[str, Any]]:
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Manifest not found: {manifest_path}. "
            "Ensure the volume has been synced and contains a lessons.json file."
        )
    with manifest_path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("lessons.json must contain a JSON array")
    return data  # type: ignore[return-value]


class CreateLessonsFromManifestUseCase:
    """Read lessons.json from the module volume and upsert all lessons.

    This is idempotent: running it multiple times with the same manifest
    produces the same result.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, module_id: str, caller_id: str) -> list[Lesson]:
        """Upsert lessons from the module volume manifest.

        Args:
            module_id: ID of the target module.
            caller_id: ID of the authenticated user (must be master).

        Returns:
            List of Lesson objects that were created or updated.

        Raises:
            LookupError: Module not found.
            PermissionError: Caller is not the module master.
            FileNotFoundError: lessons.json not found in volume.
            ValueError: Manifest format is invalid.
        """
        with self._uow as uow:
            module = uow.modules.find_by_id(module_id)
            if module is None:
                raise LookupError(f"Module '{module_id}' not found")
            if module.master_id != caller_id:
                raise PermissionError("Only the module master may sync lessons")

            volume_path = _get_volumes_base() / "modules" / module_id
            manifest_path = volume_path / _MANIFEST_FILENAME
            entries = _parse_manifest(manifest_path)

            lessons: list[Lesson] = []
            for entry in entries:
                lesson_id = entry.get("lesson_id")
                title = entry.get("title")
                position = entry.get("position")

                if not lesson_id or not title or position is None:
                    raise ValueError(
                        f"Each lesson entry must have 'lesson_id', 'title', "
                        f"and 'position'. Got: {entry}"
                    )

                existing = uow.lessons.find_by_id(lesson_id)
                if existing is not None:
                    existing.update(
                        title=title,
                        position=int(position),
                        topic_id=entry.get("topic_id"),
                        content_path=entry.get("content_path"),
                        homework_path=entry.get("homework_path"),
                    )
                    lessons.append(existing)
                else:
                    lesson = Lesson(
                        lesson_id=lesson_id,
                        module_id=module_id,
                        title=title,
                        position=int(position),
                        topic_id=entry.get("topic_id"),
                        content_path=entry.get("content_path"),
                        homework_path=entry.get("homework_path"),
                    )
                    lessons.append(lesson)

            uow.lessons.save_all(lessons)
            uow.commit()
            return lessons
