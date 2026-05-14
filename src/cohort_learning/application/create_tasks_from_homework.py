"""Use case: Auto-create PracticeTasks from lesson homework files on cohort activation.

Called when a cohort is activated (Forming → Active). Reads all lessons
for the cohort's module, and for each lesson that has a ``homework_path``,
creates a PracticeTask in Draft status (to be manually activated later).

Design decisions:
- Tasks are created with the cohort master as ``creator_id``.
- The task ``description`` contains the relative path to the homework file
  so the frontend can load and render it as Markdown.
- If a task with the same ``task_id`` already exists, it is skipped
  (idempotent — safe to call multiple times).
- ``task_id`` is derived deterministically: ``{cohort_id}:{lesson_id}``.
"""

from __future__ import annotations

import uuid

from cohort_learning.domain.ports import UnitOfWork
from cohort_learning.domain.practice_task import PracticeTask


def _homework_task_id(cohort_id: str, lesson_id: str) -> str:
    """Deterministic task id: stable UUID5 from cohort + lesson."""
    namespace = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # UUID_URL namespace
    return str(uuid.uuid5(namespace, f"{cohort_id}:{lesson_id}"))


class CreateTasksFromHomeworkUseCase:
    """Create draft PracticeTasks for every lesson with a homework file.

    Intended to be invoked automatically when a cohort is activated,
    but can also be triggered manually by the master.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, cohort_id: str, caller_id: str) -> list[PracticeTask]:
        """Create homework tasks for all lessons in the cohort's module.

        Args:
            cohort_id: ID of the cohort being activated.
            caller_id: ID of the caller (must be cohort master).

        Returns:
            List of newly created PracticeTask objects (skips existing ones).

        Raises:
            LookupError: Cohort or module not found.
            PermissionError: Caller is not the cohort master.
        """
        with self._uow as uow:
            cohort = uow.cohorts.find_by_id(cohort_id)
            if cohort is None:
                raise LookupError(f"Cohort '{cohort_id}' not found")
            if cohort.master_id != caller_id:
                raise PermissionError(
                    "Only the cohort master may trigger homework task creation"
                )

            lessons = uow.lessons.find_by_module(cohort.module_id)
            homework_lessons = [l for l in lessons if l.has_homework()]

            created: list[PracticeTask] = []
            for lesson in homework_lessons:
                task_id = _homework_task_id(cohort_id, lesson.lesson_id)
                existing = uow.practice_tasks.find_by_id(task_id)
                if existing is not None:
                    continue  # idempotent — skip already-created tasks

                task = PracticeTask(
                    task_id=task_id,
                    cohort_id=cohort_id,
                    topic_id=lesson.topic_id or "",
                    creator_id=caller_id,
                    title=f"Homework: {lesson.title}",
                    description=lesson.homework_path or "",
                )
                uow.practice_tasks.save(task)
                created.append(task)

            uow.commit()
            return created
