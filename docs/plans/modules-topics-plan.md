# Modules & Topics Feature Implementation Plan

## Context

`ModuleProgression` (module → topics hierarchy) domain entity and ORM tables
(`module_progressions`, `topics`) already exist but nothing is wired up:

- No `ModuleProgressionRepository` port in `domain/ports.py`
- No use cases, no API routes, no frontend pages
- `module_id` on `POST /cohorts` is a free-text field with no way to pick an
  existing module from the UI

The hierarchy is: **Module (`ModuleProgression`) → Topics (`Topic`)**. There is
no "lesson" concept — topics are the atomic learning units.

---

## Design Decisions

| Decision | Choice |
|---|---|
| Who can create a module | Any authenticated user; becomes the module's `master_id` |
| `GET /modules` scope | Public catalog — returns all modules in the system |
| Topic fields | `title`, `position`, `description` (matches existing ORM schema) |
| Module picker on create-cohort | Searchable `<select>` dropdown only (no manual text fallback) |

---

## Backend

### B1 — `src/cohort_learning/domain/ports.py`

Add `ModuleProgressionRepository` Protocol:

```python
class ModuleProgressionRepository(Protocol):
    def find_by_id(self, module_id: str) -> ModuleProgression | None: ...
    def save(self, module: ModuleProgression) -> None: ...
    def find_by_master(self, master_id: str) -> list[ModuleProgression]: ...
    def find_all(self) -> list[ModuleProgression]: ...
```

Add `modules: ModuleProgressionRepository` attribute to `UnitOfWork`.

### B2 — `src/cohort_learning/infrastructure/sqlalchemy_repository.py`

Implement `SqlAlchemyModuleProgressionRepository`:
- `find_by_id`: `session.get(ModuleProgression, module_id)` with
  `selectinload(ModuleProgression._topics)`
- `save`: `session.merge(module)`
- `find_by_master`: `select(ModuleProgression).where(master_id=...)` with
  `selectinload`
- `find_all`: `select(ModuleProgression)` with `selectinload`

Note: `ModuleProgression._topics` is an ORM-managed list — no `_init_transient`
needed (no domain events on this entity).

### B3 — `src/cohort_learning/infrastructure/unit_of_work.py`

Wire `self.modules = SqlAlchemyModuleProgressionRepository(self._session)` in
`__enter__`.

### B4 — `tests/cohort_learning/fakes/fake_unit_of_work.py`

Add `_FakeModuleProgressionRepository` (in-memory dict, fully implements the
Protocol) and expose as `self.modules` on `FakeUnitOfWork`.

### B5 — `src/cohort_learning/application/create_module.py`

```
CreateModuleUseCase.execute(module_id, title, caller_id)
  → ModuleProgression(module_id, title, master_id=caller_id)
  → uow.modules.save(module)
  → uow.commit()
```

### B6 — `src/cohort_learning/application/add_topic_to_module.py`

```
AddTopicToModuleUseCase.execute(module_id, topic_id, title, position, description, caller_id)
  → load module or raise 404
  → module.add_topic(Topic(...))
  → uow.modules.save(module)
  → uow.commit()
```

No role guard for now — any authenticated user who knows the module_id can add
topics (matches "any user can create a module and own it").

### B7 — `src/cohort_learning/application/list_modules.py`

```
ListModulesUseCase.execute() → list[ModuleProgression]
  → uow.modules.find_all()
```

### B8 — `src/cohort_learning/application/get_module.py`

```
GetModuleUseCase.execute(module_id) → ModuleProgression
  → uow.modules.find_by_id(module_id) or raise 404
```

### B9 — `src/cohort_learning/api/routes/modules.py`

New `APIRouter(prefix="/modules", tags=["modules"])`:

| Method | Path | Use case |
|---|---|---|
| `POST` | `/modules` | `CreateModuleUseCase` (201) |
| `GET` | `/modules` | `ListModulesUseCase` |
| `GET` | `/modules/{module_id}` | `GetModuleUseCase` |
| `POST` | `/modules/{module_id}/topics` | `AddTopicToModuleUseCase` (201) |
| `DELETE` | `/modules/{module_id}/topics/{topic_id}` | inline — remove topic from module (204) |

### B10 — `src/project_collaboration/api/app.py`

```python
from cohort_learning.api.routes.modules import router as modules_router
app.include_router(modules_router)
```

---

## Frontend

### F1 — `frontend/src/api/types.ts`

Add under `// Modules` section:

```ts
TopicResponse       { topic_id, title, position, description }
ModuleResponse      { module_id, title, master_id, topics: TopicResponse[], topic_count }
CreateModuleRequest { module_id, title }
AddTopicRequest     { topic_id, title, position, description }
```

### F2 — `frontend/src/api/modules.ts`

New file. Functions: `createModule`, `listModules`, `getModule`, `addTopic`,
`removeTopic`.

### F3 — `frontend/src/hooks/use-modules.ts`

New file. `moduleKeys` factory + hooks: `useModules`, `useModule`,
`useCreateModule`, `useAddTopic`, `useRemoveTopic`.

### F4 — `frontend/src/pages/modules-list.tsx`

Page: grid of module cards (title, topic count, master badge). "New Module"
button → `/modules/new`. Each card links to `/modules/:moduleId`.

### F5 — `frontend/src/pages/create-module.tsx`

Form: title input; `module_id` auto-generated with `crypto.randomUUID()` (shown
read-only with "Regenerate" button). On success navigate to `/modules/:moduleId`.

### F6 — `frontend/src/pages/module-detail.tsx`

Two sections:
1. Topics table (position, title, description) — ordered by `position`
2. "Add Topic" inline form (title, position, description; `topic_id`
   auto-generated)

### F7 — `frontend/src/pages/create-cohort.tsx`

Replace free-text `module_id` `<Input>` with a `<select>` (or shadcn
`<Select>`) dropdown populated from `useModules()`. Shows module title; value is
`module_id`. Loading / empty states handled inline.

### F8 — `frontend/src/components/layout/header.tsx`

Add "Modules" nav link between "Projects" and "Cohorts" (desktop nav + mobile
menu).

### F9 — `frontend/src/App.tsx`

Add three `ProtectedRoute` entries:
- `/modules` → `ModulesListPage`
- `/modules/new` → `CreateModulePage`
- `/modules/:moduleId` → `ModuleDetailPage`

---

## Status

- [x] B1 — ports.py
- [x] B2 — SqlAlchemyModuleProgressionRepository
- [x] B3 — unit_of_work.py
- [x] B4 — fake_unit_of_work.py
- [x] B5 — create_module.py
- [x] B6 — add_topic_to_module.py
- [x] B7 — list_modules.py
- [x] B8 — get_module.py
- [x] B9 — modules API router
- [x] B10 — register router in app.py
- [x] F1 — types.ts
- [x] F2 — modules.ts API client
- [x] F3 — use-modules.ts
- [x] F4 — modules-list.tsx
- [x] F5 — create-module.tsx
- [x] F6 — module-detail.tsx
- [x] F7 — create-cohort.tsx (dropdown)
- [x] F8 — header.tsx
- [x] F9 — App.tsx
