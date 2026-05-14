"""Module routes: REST endpoints for ModuleProgression management."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse

from cohort_learning.api.dependencies import get_cohort_uow, get_current_user_id
from cohort_learning.api.schemas import (
    AddTopicRequest,
    CreateModuleRequest,
    LessonResponse,
    ModuleResponse,
    SetRepoUrlRequest,
    SyncResponse,
    TopicResponse,
)
from cohort_learning.application.add_topic_to_module import AddTopicToModuleUseCase
from cohort_learning.application.create_lessons_from_manifest import (
    CreateLessonsFromManifestUseCase,
)
from cohort_learning.application.create_module import CreateModuleUseCase
from cohort_learning.application.get_module import GetModuleUseCase
from cohort_learning.application.list_modules import ListModulesUseCase
from cohort_learning.application.sync_module_volume import SyncModuleVolumeUseCase
from cohort_learning.domain.lesson import Lesson
from cohort_learning.domain.module_progression import ModuleProgression
from cohort_learning.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork,
)

router = APIRouter(prefix="/modules", tags=["modules"])


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def _module_to_response(module: ModuleProgression) -> ModuleResponse:
    return ModuleResponse(
        module_id=module.module_id,
        title=module.title,
        master_id=module.master_id,
        repo_url=module.repo_url,
        topics=[
            TopicResponse(
                topic_id=t.topic_id,
                title=t.title,
                position=t.position,
                description=t.description,
            )
            for t in sorted(module.topics, key=lambda t: t.position)
        ],
        topic_count=module.topic_count,
    )


def _lesson_to_response(lesson: Lesson) -> LessonResponse:
    return LessonResponse(
        lesson_id=lesson.lesson_id,
        module_id=lesson.module_id,
        title=lesson.title,
        position=lesson.position,
        topic_id=lesson.topic_id,
        content_path=lesson.content_path,
        homework_path=lesson.homework_path,
        has_homework=lesson.has_homework(),
        created_at=lesson.created_at,
    )


def _volume_path(module_id: str) -> Path:
    base = Path(os.environ.get("VOLUMES_BASE_PATH", "./volumes"))
    return base / "modules" / module_id


def _safe_file(volume: Path, rel_path: str) -> Path:
    """Resolve a relative path inside a volume; raise 400 on path traversal."""
    target = (volume / rel_path).resolve()
    if not str(target).startswith(str(volume.resolve())):
        raise HTTPException(status_code=400, detail="Invalid file path")
    return target


# ---------------------------------------------------------------------------
# Endpoints — Module CRUD
# ---------------------------------------------------------------------------


@router.post("", status_code=201, response_model=ModuleResponse)
def create_module(
    body: CreateModuleRequest,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> ModuleResponse:
    """Create a new learning module. The caller becomes its master."""
    try:
        module = CreateModuleUseCase(uow).execute(
            module_id=body.module_id,
            title=body.title,
            caller_id=caller_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _module_to_response(module)


@router.get("", response_model=list[ModuleResponse])
def list_modules(
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> list[ModuleResponse]:
    """Return all modules (public catalog)."""
    modules = ListModulesUseCase(uow).execute()
    return [_module_to_response(m) for m in modules]


@router.get("/{module_id}", response_model=ModuleResponse)
def get_module(
    module_id: str,
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> ModuleResponse:
    """Return a single module with its topics."""
    try:
        module = GetModuleUseCase(uow).execute(module_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _module_to_response(module)


@router.post("/{module_id}/topics", status_code=201, response_model=ModuleResponse)
def add_topic(
    module_id: str,
    body: AddTopicRequest,
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> ModuleResponse:
    """Add a topic to an existing module."""
    try:
        module = AddTopicToModuleUseCase(uow).execute(
            module_id=module_id,
            topic_id=body.topic_id,
            title=body.title,
            position=body.position,
            description=body.description,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _module_to_response(module)


@router.delete("/{module_id}/topics/{topic_id}", status_code=204)
def remove_topic(
    module_id: str,
    topic_id: str,
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> None:
    """Remove a topic from a module."""
    with uow as u:
        module = u.modules.find_by_id(module_id)
        if module is None:
            raise HTTPException(
                status_code=404, detail=f"Module '{module_id}' not found"
            )
        topic = module.find_topic(topic_id)
        if topic is None:
            raise HTTPException(status_code=404, detail=f"Topic '{topic_id}' not found")
        module._topics = [t for t in module._topics if t.topic_id != topic_id]  # noqa: SLF001
        u.modules.save(module)
        u.commit()


# ---------------------------------------------------------------------------
# Endpoints — repo_url management
# ---------------------------------------------------------------------------


@router.patch("/{module_id}/repo-url", response_model=ModuleResponse)
def set_repo_url(
    module_id: str,
    body: SetRepoUrlRequest,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> ModuleResponse:
    """Set or update the git repo URL for a module's content volume.

    Only the module master may update this field.
    """
    with uow as u:
        module = u.modules.find_by_id(module_id)
        if module is None:
            raise HTTPException(status_code=404, detail=f"Module '{module_id}' not found")
        if module.master_id != caller_id:
            raise HTTPException(status_code=403, detail="Only the module master may set repo_url")
        module.repo_url = body.repo_url
        u.modules.save(module)
        u.commit()
        return _module_to_response(module)


# ---------------------------------------------------------------------------
# Endpoints — Git sync
# ---------------------------------------------------------------------------


@router.post("/{module_id}/sync", response_model=SyncResponse)
def sync_module_volume(
    module_id: str,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> SyncResponse:
    """Clone or pull the module's git content repo into the local volume."""
    try:
        volume_path = SyncModuleVolumeUseCase(uow).execute(
            module_id=module_id,
            caller_id=caller_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return SyncResponse(message="sync complete", path=str(volume_path))


# ---------------------------------------------------------------------------
# Endpoints — Lessons
# ---------------------------------------------------------------------------


@router.post("/{module_id}/sync-lessons", response_model=list[LessonResponse])
def sync_lessons_from_manifest(
    module_id: str,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> list[LessonResponse]:
    """Read lessons.json from the volume and upsert all lessons into the DB."""
    try:
        lessons = CreateLessonsFromManifestUseCase(uow).execute(
            module_id=module_id,
            caller_id=caller_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return [_lesson_to_response(l) for l in lessons]


@router.get("/{module_id}/lessons", response_model=list[LessonResponse])
def list_lessons(
    module_id: str,
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> list[LessonResponse]:
    """Return all lessons for a module, sorted by position."""
    with uow as u:
        module = u.modules.find_by_id(module_id)
        if module is None:
            raise HTTPException(status_code=404, detail=f"Module '{module_id}' not found")
        lessons = u.lessons.find_by_module(module_id)
    return [_lesson_to_response(l) for l in sorted(lessons, key=lambda l: l.position)]


@router.get("/{module_id}/lessons/{lesson_id}", response_model=LessonResponse)
def get_lesson(
    module_id: str,
    lesson_id: str,
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> LessonResponse:
    """Return a single lesson."""
    with uow as u:
        lesson = u.lessons.find_by_id(lesson_id)
        if lesson is None or lesson.module_id != module_id:
            raise HTTPException(status_code=404, detail=f"Lesson '{lesson_id}' not found")
    return _lesson_to_response(lesson)


# ---------------------------------------------------------------------------
# Endpoints — File serving (Markdown content from volume)
# ---------------------------------------------------------------------------


@router.get("/{module_id}/files/{file_path:path}", response_class=PlainTextResponse)
def get_lesson_file(
    module_id: str,
    file_path: str,
    uow: SqlAlchemyUnitOfWork = Depends(get_cohort_uow),
) -> str:
    """Return raw file content (Markdown) from the module's local volume.

    ``file_path`` is the path relative to the volume root, e.g.
    ``01-intro/content.md``.  Path traversal attempts are rejected.
    """
    with uow as u:
        module = u.modules.find_by_id(module_id)
        if module is None:
            raise HTTPException(status_code=404, detail=f"Module '{module_id}' not found")

    volume = _volume_path(module_id)
    if not volume.exists():
        raise HTTPException(
            status_code=404,
            detail="Volume not found — trigger a sync first",
        )

    target = _safe_file(volume, file_path)
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail=f"File '{file_path}' not found in volume")

    return target.read_text(encoding="utf-8")
