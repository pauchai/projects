# UI Scenarios & Business Processes

Полное описание всех UI-сценариев платформы: маршруты, доступ, формы, действия, переходы состояний.

---

## Содержание

1. [Маршруты и доступ](#1-маршруты-и-доступ)
2. [Аутентификация](#2-аутентификация)
3. [Проекты](#3-проекты)
4. [Feature Requests](#4-feature-requests)
5. [Модули и темы](#5-модули-и-темы)
6. [Когорты](#6-когорты)
7. [Дашборд мастера](#7-дашборд-мастера)
8. [Награды](#8-награды)
9. [Профиль и безопасность](#9-профиль-и-безопасность)
10. [Пробелы (backend готов, UI отсутствует)](#10-пробелы)

---

## 1. Маршруты и доступ

| Маршрут | Компонент | Доступ |
|---------|-----------|--------|
| `/` | `ProjectsListPage` | Публичный |
| `/login` | `LoginPage` | Анонимный |
| `/register` | `RegisterPage` | Анонимный |
| `/oauth/callback` | `OAuthCallbackPage` | — |
| `/projects/:projectId` | `ProjectDetailPage` | Публичный |
| `/projects/:projectId/edit` | `EditProjectPage` | Protected (владелец) |
| `/projects/new` | `CreateProjectPage` | Protected |
| `/projects/:projectId/applications` | `ManageApplicationsPage` | Protected (владелец) |
| `/features` | `FeaturesListPage` | Публичный |
| `/features/new` | `SubmitFeaturePage` | Protected |
| `/features/:requestId` | `FeatureDetailPage` | Публичный |
| `/cohorts` | `CohortsListPage` | Protected |
| `/cohorts/new` | `CreateCohortPage` | Protected |
| `/cohorts/:cohortId` | `CohortDetailPage` | Protected |
| `/cohorts/:cohortId/dashboard` | `CohortDashboardPage` | Protected (только master) |
| `/modules` | `ModulesListPage` | Protected |
| `/modules/new` | `CreateModulePage` | Protected |
| `/modules/:moduleId` | `ModuleDetailPage` | Protected |
| `/profile` | `ProfilePage` | Protected |
| `/me/rewards` | `RewardsPage` | Protected |
| `/settings/security` | `SecuritySettingsPage` | Protected |

---

## 2. Аутентификация

### 2.1 Регистрация — `/register`

**Форма:**

| Поле | Тип | Правила |
|------|-----|---------|
| Display Name | text | Обязательное, ≤ 100 символов |
| Email | email | Обязательное, должен содержать `@` |
| Password | password | Обязательное, ≥ 6 символов |
| Confirm Password | password | Должен совпадать с Password |

**Действия:**
- Кнопка **Sign Up** → `POST /auth/register` → `POST /auth/login` → redirect `/`
- Кнопки OAuth: **Sign in with Google**, **Sign in with Telegram** (показываются если доступны через API)
- Ссылка «Already have an account? Sign in»

---

### 2.2 Вход — `/login`

**Форма:**

| Поле | Тип | Правила |
|------|-----|---------|
| Email | email | Обязательное |
| Password | password | Обязательное |

**Действия:**
- Кнопка **Sign In** → `POST /auth/login` → redirect на `location.state.from` или `/`
- Кнопки OAuth: **Sign in with Google**, **Sign in with Telegram** (показываются если доступны)
- Ссылка «Don't have an account? Register»

---

### 2.3 OAuth Callback — `/oauth/callback`

Страница без UI. Три сценария:

| Сценарий | Поведение |
|----------|-----------|
| Google popup | Читает `code` + `state` из URL, завершает flow, закрывает popup |
| Telegram redirect (логин) | Завершает OAuth flow → redirect `/` |
| Telegram redirect (link account) | Завершает flow привязки → redirect `/settings/security` |

Ошибка: если `state` отсутствует (Telegram in-app browser), показывает сообщение о необходимости открыть в браузере.

---

## 3. Проекты

### 3.1 Список проектов — `/`

**Фильтры:**

| Элемент | Тип |
|---------|-----|
| Keyword | text input |
| Skills | text input (через запятую) |
| Status | кнопки: All / Recruiting / Active / Completed |

**Данные:** `GET /projects/search` с параметрами `keyword`, `status`, `skills`.

Аутентифицированным пользователям доступна ссылка **New Project**.

---

### 3.2 Создание проекта — `/projects/new`

**Форма:**

| Поле | Тип | Правила |
|------|-----|---------|
| Title | text | Обязательное, 3–200 символов |
| Description | textarea | Необязательное, ≤ 5000 символов |
| Required Skills | text | Необязательное, через запятую |
| Max Members | number | Необязательное, положительное целое |

**Действия:**
- `POST /projects` с `project_id = crypto.randomUUID()`
- Redirect `/projects/:id` при успехе

---

### 3.3 Детальная страница проекта — `/projects/:projectId`

**Отображает:** title, status badge, description, required skills, created date, max members, список активных участников.

**Блок Owner Actions** (только владелец):

| Статус проекта | Доступные переходы |
|---------------|--------------------|
| `draft` | Publish |
| `recruiting` | Activate, Cancel |
| `active` | Suspend, Complete, Cancel |
| `suspended` | Resume, Cancel |
| `completed` | — |
| `cancelled` | — |

Плюс кнопка **Edit** (→ `/projects/:id/edit`).

**Блок Apply** (аутентифицированный, не участник, статус `recruiting`):

| Поле | Тип | Правила |
|------|-----|---------|
| Desired Role | text | Обязательное |
| Motivation | textarea | Необязательное |
| Skills | text | Необязательное, через запятую |

`POST /projects/:id/applications` с `application_id = crypto.randomUUID()`.

**Ссылка «Manage project»**: видна владельцу, если есть заявки в статусе `pending`. Ведёт на `/projects/:id/applications`.

---

### 3.4 Редактирование проекта — `/projects/:projectId/edit`

Те же поля и валидации что и при создании. Только владелец. `PATCH /projects/:id`.

---

### 3.5 Управление заявками — `/projects/:projectId/applications`

Только владелец.

**Секция Pending Applications:**
- Карточка заявки: applicant_id, desired_role, motivation, skills
- Кнопка **Accept** → `POST /projects/:id/applications/:appId/accept`
- Кнопка **Reject** → `POST /projects/:id/applications/:appId/reject`

**Секция Reviewed Applications:** только просмотр (accepted / rejected).

**Секция Members:**
- `<MemberCard>` per member: role `<select>` + **Save** → `PATCH /projects/:id/members/:mid/role`; кнопка **Remove** → `DELETE /projects/:id/members/:mid`
- Member, являющийся owner-ом, нередактируем

---

## 4. Feature Requests

### 4.1 Список — `/features`

**Фильтры:**

| Элемент | Тип |
|---------|-----|
| Status | кнопки: All / Submitted / Planned / In Progress / Done / Rejected |
| My Requests | toggle (только аутентифицированные) |

**Данные:** `GET /features` с параметрами `status` и `author_id`.

---

### 4.2 Создание заявки — `/features/new`

**Форма:**

| Поле | Тип | Правила |
|------|-----|---------|
| Title | text | Обязательное, 3–500 символов (счётчик) |
| Description | textarea | Обязательное, 1–10 000 символов (счётчик) |
| Category | text | Необязательное |
| Priority | select | Необязательное (low / medium / high) |

`POST /features` с `request_id = crypto.randomUUID()`. Redirect `/features/:id`.

---

### 4.3 Детальная страница — `/features/:requestId`

**Отображает:** title, status badge, category, priority, created/updated, description, admin notes (если есть).

**Блок Status Management** (аутентифицированный + есть доступные переходы):

| Статус | Доступные переходы |
|--------|--------------------|
| `submitted` | Planned, Rejected |
| `planned` | In Progress, Rejected |
| `in_progress` | Done, Planned, Rejected |
| `done` | — |
| `rejected` | — |

Форма: textarea **Admin Notes** (необязательное) + кнопки переходов.
`PUT /admin/features/:id/status` с `{ status, admin_notes }`.

---

## 5. Модули и темы

### 5.1 Список модулей — `/modules`

Сетка карточек: title, master_id, количество тем.
Кнопка **New Module** в заголовке.

---

### 5.2 Создание модуля — `/modules/new`

| Поле | Тип | Правила |
|------|-----|---------|
| Module ID | text (read-only) | `crypto.randomUUID()`, кнопка Regenerate |
| Title | text | Обязательное |

`POST /modules`.

---

### 5.3 Детальная страница модуля — `/modules/:moduleId`

Список тем, отсортированных по `position`.

**Форма Add Topic** (только master модуля):

| Поле | Тип | Правила |
|------|-----|---------|
| Title | text | Обязательное |
| Position | number | ≥ 0, целое |
| Description | textarea | Необязательное |

`POST /modules/:id/topics` с `topic_id = crypto.randomUUID()`.

Кнопка **Remove** на каждой теме → `DELETE /modules/:id/topics/:tid` (только master).

---

## 6. Когорты

### 6.1 Список когорт — `/cohorts`

Сетка карточек: cohort_id, module_id, status badge, количество участников, дата формирования.

- Все: кнопка **View** → `/cohorts/:id`
- Master: дополнительно кнопка **Dashboard** → `/cohorts/:id/dashboard`

Кнопка **New Cohort** в заголовке.

---

### 6.2 Создание когорты — `/cohorts/new`

| Поле | Тип | Правила |
|------|-----|---------|
| Cohort ID | text (read-only) | `crypto.randomUUID()`, кнопка Regenerate |
| Module | select | Обязательное (список из `GET /modules`) |

`POST /cohorts`. Если модулей нет — ссылка «Create a module first».

---

### 6.3 Детальная страница когорты — `/cohorts/:cohortId`

4 таба: **Overview**, **Tasks**, **Progression**, **Leaderboard**.

**Кнопки управления статусом** (только master, вверху страницы):

| Статус когорты | Доступные переходы |
|---------------|--------------------|
| `forming` | Activate |
| `active` | Begin Completing, Cancel |
| `completing` | Graduate, Cancel |
| `graduated` | — |
| `cancelled` | — |

---

#### 6.3.1 Tab: Overview

**Список участников**: membership_id, learner_id, role badge.
- Кнопка **Remove** (master + статус `forming`) → `DELETE /cohorts/:id/learners/:lid`

**Форма Enrol Learner** (master + статус `forming`):

| Поле | Тип | Правила |
|------|-----|---------|
| Learner ID | text | Обязательное |

`POST /cohorts/:id/learners` с `membership_id = crypto.randomUUID()`.

---

#### 6.3.2 Tab: Tasks

**Форма Create Task** (master или curator):

| Поле | Тип | Правила |
|------|-----|---------|
| Title | text | Обязательное |
| Topic | select | Обязательное (темы из модуля когорты) |
| Description | textarea | Необязательное |

`POST /cohorts/:id/tasks` с `task_id = crypto.randomUUID()`.

**Карточка задачи:**

| Действие | Доступно | Эндпоинт |
|----------|----------|----------|
| **Activate** | master/curator, статус `pending` | `POST /cohorts/:id/tasks/:tid/activate` |
| **Close** | master/curator, статус `active` | `POST /cohorts/:id/tasks/:tid/close` |
| **Submit Solution** | learner, статус `active`, нет своей submission | textarea + `POST /cohorts/:id/tasks/:tid/submissions` |
| **Submit Peer Review** | learner, статус `active`, есть submission другого | форма с per-criterion оценками |

**Форма Peer Review:**

Критерии (захардкожено): `correctness`, `clarity`, `completeness`.

| Поле | Тип | Правила |
|------|-----|---------|
| Score per criterion | select (1–5) | Обязательное, default = 3 |
| Comment per criterion | textarea | Необязательное |
| Overall Feedback | textarea | Необязательное |

`POST /cohorts/:id/tasks/:tid/submissions/:sid/reviews` с `review_id = crypto.randomUUID()`.

---

#### 6.3.3 Tab: Progression

**Topic Experts:** таблица expert_id, learner_id, topic_id, validated_at.

**Helper Metrics:** таблица learner_id, learners_helped, questions_answered, tasks_reviewed, avg_satisfaction.

---

#### 6.3.4 Tab: Leaderboard

Ранжированный список: rank, learner_id, total_xp.

`GET /cohorts/:id/leaderboard`.

---

## 7. Дашборд мастера

### `/cohorts/:cohortId/dashboard`

Только master. Ссылка из `CohortsListPage`.

**Секция Pending Competency Validations:**

Список `GET /cohorts/:id/pending-validations`. На каждый элемент:

| Поле | Значение |
|------|---------|
| Learner | learner_id |
| Topic | topic_id |
| Requested | created_at |

Действия:

| Кнопка | Эндпоинт | Тело запроса |
|--------|----------|-------------|
| **Validate** | `POST /cohorts/:id/members/:lid/validate-competency` | `{ topic_id, knowledge_check_score: 80*, mentor_approved: true* }` |
| **Promote Expert** | `POST /cohorts/:id/members/:lid/promote-expert` | `{ expert_id: uuid, topic_id }` |

> ⚠️ **Известный пробел:** `knowledge_check_score` и `mentor_approved` захардкожены. Нужны input-поля для реального ввода мастером.

---

**Секция Pending Curator Promotions:**

Список `GET /cohorts/:id/pending-promotions`. На каждый элемент:

| Поле | Значение |
|------|---------|
| Learner | learner_id |
| Module | module_id |
| Requested | created_at |

Действие:

| Кнопка | Эндпоинт | Тело запроса |
|--------|----------|-------------|
| **Promote Curator** | `POST /cohorts/:id/members/:lid/promote-curator` | `{ curator_id: uuid, module_id }` |

---

## 8. Награды

### `/me/rewards`

**Баланс (4 тайла):**

| Тайл | Поле |
|------|------|
| Total XP | `total_xp` |
| Credits | `total_credits` |
| Reputation Score | `reputation_score` (`.toFixed(1)` или «—» если null) |
| Badges | `badges.length` |

`GET /me/rewards/balance`.

**Badges:** pill-список из `badges[]`.

**Reward History:**

Таблица: reward_type, amount, triggering_event, cohort_id, granted_at.

`GET /me/rewards/history`.

---

## 9. Профиль и безопасность

### 9.1 Профиль — `/profile`

**Отображает:** displayName, email, userId (monospace).

Ссылка **Security Settings** → `/settings/security`.

**My Projects:** карточки проектов, где `owner_id == currentUser`.

**Projects I'm a Member Of:** карточки проектов, где пользователь является участником, но не владельцем.

`GET /projects/search?owner_id=...` и `GET /projects/search?member_user_id=...`.

---

### 9.2 Настройки безопасности — `/settings/security`

**Connected Sign-in Methods:**

Список `CredentialCard` (provider icon, display name, бейдж «Primary» если `is_removable=false`).
Кнопка **Remove** → `DELETE /auth/credentials/:id` (если removable).

`GET /auth/credentials`.

**Add Sign-in Method** (если есть непривязанные провайдеры):

| Кнопка | Действие |
|--------|---------|
| **Link Google Account** | `GET /auth/oauth/google/authorize` → popup |
| **Link Telegram Account** | `GET /auth/oauth/telegram/authorize` → redirect |

Ошибка 409 (уже привязан к другому аккаунту) показывает конкретное сообщение.

---

## 10. Пробелы

Функции, реализованные на backend, но не имеющие UI.

### 10.1 Curator Earnings — `/me/earnings` (отсутствует)

**Backend эндпоинты:**

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/me/earnings` | Сводка: total_pending, total_released, список комиссий |
| `GET` | `/me/earnings/history` | Полная история комиссий |
| `POST` | `/me/earnings/:id/release` | Вывод комиссии (hold period + minimum threshold) |

**Тип `CommissionResponse`:**

```ts
{
  commission_id: string
  curator_id: string
  cohort_id: string
  module_id: string
  base_amount: number
  bonus_amount: number
  total_amount: number
  status: "pending" | "released"
  earned_at: string
  release_eligible_at: string
  released_at: string | null
}
```

**Предлагаемый UI:** страница `/me/earnings` с двумя секциями:
1. Summary card (total_pending, total_released)
2. Таблица комиссий с кнопкой **Release** (если `status=pending` и текущее время ≥ `release_eligible_at`)

---

### 10.2 Validate Competency — реальная форма

`CohortDashboardPage` захардкодила `knowledge_check_score: 80` и `mentor_approved: true`.

**Нужно добавить** per-row форму:

| Поле | Тип | Правила |
|------|-----|---------|
| Knowledge Check Score | number input | 0–100 |
| Mentor Approved | checkbox | — |

Только после заполнения активируется кнопка **Validate**.
