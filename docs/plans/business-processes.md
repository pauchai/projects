# Бизнес-процессы платформы

Каждый процесс описывает: кто выполняет, какова цель, и какие UI-сценарии (маршруты + API-эндпоинты) задействованы на каждом шаге.

Ссылки на детали UI-сценариев — в [ui-scenarios.md](./ui-scenarios.md).

---

## Содержание

**Аутентификация и идентификация**
1. [Регистрация нового пользователя](#1-регистрация-нового-пользователя)
2. [Вход по email и паролю](#2-вход-по-email-и-паролю)
3. [OAuth-вход (Google / Telegram)](#3-oauth-вход-google--telegram)
4. [Привязка дополнительного OAuth-метода](#4-привязка-дополнительного-oauth-метода)
5. [Отвязка OAuth-метода](#5-отвязка-oauth-метода)

**Проектная коллаборация**
6. [Создание и публикация проекта](#6-создание-и-публикация-проекта)
7. [Подача заявки на вступление в проект](#7-подача-заявки-на-вступление-в-проект)
8. [Проверка заявок и приём участников](#8-проверка-заявок-и-приём-участников)
9. [Управление ролями и составом команды](#9-управление-ролями-и-составом-команды)
10. [Управление жизненным циклом проекта](#10-управление-жизненным-циклом-проекта)

**Feature Requests**
11. [Подача feature request](#11-подача-feature-request)
12. [Прохождение feature request по статусам](#12-прохождение-feature-request-по-статусам)

**Модули и учебная программа**
13. [Создание модуля с темами](#13-создание-модуля-с-темами)

**Когортное обучение**
14. [Формирование когорты и зачисление учеников](#14-формирование-когорты-и-зачисление-учеников)
15. [Полный учебный цикл](#15-полный-учебный-цикл)
16. [Валидация компетенции и продвижение в Topic Expert](#16-валидация-компетенции-и-продвижение-в-topic-expert)
17. [Продвижение ученика в Curator](#17-продвижение-ученика-в-curator)
18. [Завершение и выпуск когорты](#18-завершение-и-выпуск-когорты)

**Награды**
19. [Просмотр баланса наград и истории](#19-просмотр-баланса-наград-и-истории)

**Пробел (backend есть, UI нет)**
20. [Получение и вывод комиссионных куратора](#20-получение-и-вывод-комиссионных-куратора)

---

## Аутентификация и идентификация

### 1. Регистрация нового пользователя

**Актор:** анонимный пользователь  
**Цель:** создать аккаунт и получить доступ к платформе

| Шаг | Действие | Маршрут | API |
|-----|---------|---------|-----|
| 1 | Открыть форму регистрации | `/register` | — |
| 2 | Заполнить display name, email, password, confirm password и нажать **Sign Up** | `/register` | `POST /auth/register` |
| 3 | Автоматический вход после успешной регистрации | `/register` | `POST /auth/login` |
| 4 | Редирект на главную страницу | `/` | — |

---

### 2. Вход по email и паролю

**Актор:** зарегистрированный пользователь  
**Цель:** войти в аккаунт

| Шаг | Действие | Маршрут | API |
|-----|---------|---------|-----|
| 1 | Открыть форму входа | `/login` | — |
| 2 | Ввести email и password, нажать **Sign In** | `/login` | `POST /auth/login` |
| 3 | Редирект на целевую страницу (или `/`) | — | — |

---

### 3. OAuth-вход (Google / Telegram)

**Актор:** анонимный пользователь  
**Цель:** войти или зарегистрироваться через внешний провайдер

#### Google

| Шаг | Действие | Маршрут | API |
|-----|---------|---------|-----|
| 1 | Нажать **Sign in with Google** | `/login` или `/register` | `GET /auth/oauth/google/available` |
| 2 | Получить ссылку авторизации | — | `GET /auth/oauth/google/authorize` |
| 3 | Пользователь проходит OAuth в Google (popup) | внешний | — |
| 4 | Google редиректит с кодом | `/oauth/callback` | — |
| 5 | Завершить OAuth flow | `/oauth/callback` | `POST /auth/oauth/google/callback` |
| 6 | Редирект на `/` | `/` | — |

#### Telegram

| Шаг | Действие | Маршрут | API |
|-----|---------|---------|-----|
| 1 | Нажать **Sign in with Telegram** | `/login` или `/register` | `GET /auth/oauth/telegram/authorize` |
| 2 | Редирект в Telegram (полная страница) | внешний | — |
| 3 | Telegram редиректит обратно с кодом | `/oauth/callback` | — |
| 4 | Завершить OAuth flow | `/oauth/callback` | `POST /auth/oauth/telegram/callback` |
| 5 | Редирект на `/` | `/` | — |

---

### 4. Привязка дополнительного OAuth-метода

**Актор:** авторизованный пользователь  
**Цель:** добавить ещё один способ входа к существующему аккаунту

| Шаг | Действие | Маршрут | API |
|-----|---------|---------|-----|
| 1 | Открыть настройки безопасности | `/settings/security` | `GET /auth/credentials` |
| 2 | Нажать **Link Google Account** или **Link Telegram Account** | `/settings/security` | `GET /auth/oauth/google/authorize` или `GET /auth/oauth/telegram/authorize` |
| 3 | Пройти OAuth у провайдера | внешний | — |
| 4 | Провайдер редиректит с кодом | `/oauth/callback` | — |
| 5 | Завершить привязку | `/oauth/callback` | `POST /auth/oauth/google/callback` или `POST /auth/oauth/telegram/callback` |
| 6 | Редирект на `/settings/security` с обновлённым списком | `/settings/security` | `GET /auth/credentials` |

> Если аккаунт провайдера уже привязан к другому пользователю — ошибка 409 с пояснением.

---

### 5. Отвязка OAuth-метода

**Актор:** авторизованный пользователь  
**Цель:** удалить один из способов входа

| Шаг | Действие | Маршрут | API |
|-----|---------|---------|-----|
| 1 | Открыть настройки безопасности | `/settings/security` | `GET /auth/credentials` |
| 2 | Нажать **Remove** рядом с нужным методом | `/settings/security` | `DELETE /auth/credentials/:credential_id` |
| 3 | Список обновляется (метод удалён) | `/settings/security` | `GET /auth/credentials` |

> Кнопка **Remove** недоступна для «Primary»-метода (`is_removable = false`).

---

## Проектная коллаборация

### 6. Создание и публикация проекта

**Актор:** авторизованный пользователь (становится владельцем)  
**Цель:** создать проект и открыть набор участников

| Шаг | Действие | Маршрут | API |
|-----|---------|---------|-----|
| 1 | Нажать **New Project** | `/` | — |
| 2 | Заполнить title, description, required skills, max members и нажать **Create** | `/projects/new` | `POST /projects` |
| 3 | Проект создан со статусом `draft`, редирект на страницу проекта | `/projects/:id` | — |
| 4 | Нажать **Publish** | `/projects/:id` | `POST /projects/:id/publish` |
| 5 | Статус переходит в `recruiting` — проект виден в поиске | `/projects/:id` | — |

---

### 7. Подача заявки на вступление в проект

**Актор:** авторизованный пользователь (не участник проекта)  
**Цель:** вступить в проект в желаемой роли

| Шаг | Действие | Маршрут | API |
|-----|---------|---------|-----|
| 1 | Найти проект в списке (фильтр по статусу, навыкам, ключевому слову) | `/` | `GET /projects/search` |
| 2 | Открыть страницу проекта | `/projects/:id` | `GET /projects/:id` |
| 3 | Раскрыть форму **Apply**, заполнить desired role, motivation, skills | `/projects/:id` | — |
| 4 | Нажать **Submit Application** | `/projects/:id` | `POST /projects/:id/applications` |
| 5 | Заявка отображается у владельца в разделе Pending | — | — |

> Блок Apply виден только при статусе `recruiting` и только не-участникам.

---

### 8. Проверка заявок и приём участников

**Актор:** владелец проекта  
**Цель:** рассмотреть заявки и сформировать команду

| Шаг | Действие | Маршрут | API |
|-----|---------|---------|-----|
| 1 | Перейти по ссылке «Manage project →» (появляется при наличии pending-заявок) | `/projects/:id` | — |
| 2 | Просмотреть карточки заявок в секции Pending Applications | `/projects/:id/applications` | `GET /projects/:id` |
| 3a | Нажать **Accept** на заявке | `/projects/:id/applications` | `POST /projects/:id/applications/:appId/accept` |
| 3b | Или нажать **Reject** | `/projects/:id/applications` | `POST /projects/:id/applications/:appId/reject` |
| 4 | Принятый заявитель появляется в секции Members | `/projects/:id/applications` | — |

---

### 9. Управление ролями и составом команды

**Актор:** владелец проекта  
**Цель:** изменить роль участника или удалить его из проекта

| Шаг | Действие | Маршрут | API |
|-----|---------|---------|-----|
| 1 | Открыть страницу управления заявками | `/projects/:id/applications` | `GET /projects/:id` |
| 2a | Выбрать новую роль в `<select>` и нажать **Save** | `/projects/:id/applications` | `PATCH /projects/:id/members/:mid/role` |
| 2b | Или нажать **Remove** для удаления участника | `/projects/:id/applications` | `DELETE /projects/:id/members/:mid` |

> Карточка владельца не редактируема и не удаляема.

---

### 10. Управление жизненным циклом проекта

**Актор:** владелец проекта  
**Цель:** провести проект через статусы от `draft` до финального состояния

| Переход | Кнопка | Маршрут | API |
|---------|--------|---------|-----|
| `draft` → `recruiting` | **Publish** | `/projects/:id` | `POST /projects/:id/publish` |
| `recruiting` → `active` | **Activate** | `/projects/:id` | `POST /projects/:id/activate` |
| `recruiting` → `cancelled` | **Cancel** | `/projects/:id` | `POST /projects/:id/cancel` |
| `active` → `suspended` | **Suspend** | `/projects/:id` | `POST /projects/:id/suspend` |
| `active` → `completed` | **Complete** | `/projects/:id` | `POST /projects/:id/complete` |
| `active` → `cancelled` | **Cancel** | `/projects/:id` | `POST /projects/:id/cancel` |
| `suspended` → `active` | **Resume** | `/projects/:id` | `POST /projects/:id/resume` |
| `suspended` → `cancelled` | **Cancel** | `/projects/:id` | `POST /projects/:id/cancel` |

Дополнительно: кнопка **Edit** ведёт на `/projects/:id/edit` → `PATCH /projects/:id`.

---

## Feature Requests

### 11. Подача feature request

**Актор:** авторизованный пользователь  
**Цель:** предложить улучшение или новую функцию платформы

| Шаг | Действие | Маршрут | API |
|-----|---------|---------|-----|
| 1 | Перейти в список Feature Requests | `/features` | `GET /features` |
| 2 | Нажать **Submit Request** | `/features` | — |
| 3 | Заполнить title, description, category (опц.), priority (опц.) и нажать **Submit** | `/features/new` | `POST /features` |
| 4 | Заявка создана со статусом `submitted`, редирект на её страницу | `/features/:id` | — |

---

### 12. Прохождение feature request по статусам

**Актор:** администратор  
**Цель:** провести заявку по рабочему процессу до завершения

| Шаг | Действие | Маршрут | API |
|-----|---------|---------|-----|
| 1 | Открыть страницу заявки | `/features/:id` | `GET /features/:id` |
| 2 | (Опционально) Написать admin notes | `/features/:id` | — |
| 3 | Нажать нужную кнопку перехода | `/features/:id` | `PUT /admin/features/:id/status` |

**Допустимые переходы:**

| Текущий статус | Возможные переходы |
|---------------|--------------------|
| `submitted` | → `planned`, → `rejected` |
| `planned` | → `in_progress`, → `rejected` |
| `in_progress` | → `done`, → `planned`, → `rejected` |
| `done` | — |
| `rejected` | — |

---

## Модули и учебная программа

### 13. Создание модуля с темами

**Актор:** master  
**Цель:** сформировать учебный модуль, который можно использовать в когортах

| Шаг | Действие | Маршрут | API |
|-----|---------|---------|-----|
| 1 | Открыть список модулей | `/modules` | `GET /modules` |
| 2 | Нажать **New Module** | `/modules` | — |
| 3 | Ввести title (module_id генерируется автоматически), нажать **Create** | `/modules/new` | `POST /modules` |
| 4 | Редирект на страницу модуля | `/modules/:id` | `GET /modules/:id` |
| 5 | Заполнить форму Add Topic (title, position, description) и нажать **Add Topic** | `/modules/:id` | `POST /modules/:id/topics` |
| 6 | Повторить шаг 5 для каждой темы | `/modules/:id` | `POST /modules/:id/topics` |
| 7 | (Опционально) Удалить тему кнопкой **Remove** | `/modules/:id` | `DELETE /modules/:id/topics/:tid` |

---

## Когортное обучение

### 14. Формирование когорты и зачисление учеников

**Актор:** master  
**Цель:** создать группу учеников для прохождения конкретного модуля

| Шаг | Действие | Маршрут | API |
|-----|---------|---------|-----|
| 1 | Открыть список когорт | `/cohorts` | `GET /cohorts` |
| 2 | Нажать **New Cohort** | `/cohorts` | — |
| 3 | Выбрать модуль из списка, нажать **Create** | `/cohorts/new` | `POST /cohorts` |
| 4 | Редирект на страницу когорты (статус `forming`) | `/cohorts/:id` | `GET /cohorts/:id` |
| 5 | Вкладка Overview: ввести Learner ID, нажать **Enrol** | `/cohorts/:id` | `POST /cohorts/:id/learners` |
| 6 | Повторить шаг 5 для каждого ученика | `/cohorts/:id` | `POST /cohorts/:id/learners` |
| 7 | (Опционально) Убрать ученика кнопкой **Remove** | `/cohorts/:id` | `DELETE /cohorts/:id/learners/:lid` |

---

### 15. Полный учебный цикл

**Акторы:** master / curator (создают и управляют задачами), learner (сдаёт решения и проверяет работы)  
**Цель:** провести учеников через практические задачи с peer review

#### 15.1 Активация когорты

| Шаг | Действие | Маршрут | API |
|-----|---------|---------|-----|
| 1 | Master нажимает **Activate** | `/cohorts/:id` | `POST /cohorts/:id/activate` |
| 2 | Статус когорты переходит в `active` | `/cohorts/:id` | — |

#### 15.2 Создание и активация задачи

| Шаг | Действие | Маршрут | API |
|-----|---------|---------|-----|
| 1 | Перейти на вкладку Tasks | `/cohorts/:id` | — |
| 2 | Заполнить форму Create Task (title, topic, description), нажать **Create Task** | `/cohorts/:id` | `POST /cohorts/:id/tasks` |
| 3 | Задача создана со статусом `pending` | `/cohorts/:id` | — |
| 4 | Нажать **Activate** на карточке задачи | `/cohorts/:id` | `POST /cohorts/:id/tasks/:tid/activate` |
| 5 | Задача переходит в статус `active` — доступна ученикам | `/cohorts/:id` | — |

#### 15.3 Сдача решения учеником

| Шаг | Действие | Маршрут | API |
|-----|---------|---------|-----|
| 1 | Learner открывает вкладку Tasks | `/cohorts/:id` | `GET /cohorts/:id/tasks` |
| 2 | В карточке активной задачи вводит решение в textarea и нажимает **Submit Solution** | `/cohorts/:id` | `POST /cohorts/:id/tasks/:tid/submissions` |
| 3 | Решение отображается как submitted | `/cohorts/:id` | — |

#### 15.4 Peer review чужого решения

| Шаг | Действие | Маршрут | API |
|-----|---------|---------|-----|
| 1 | Learner видит submission другого ученика на вкладке Tasks | `/cohorts/:id` | — |
| 2 | Выставить оценки (1–5) и комментарии по критериям: correctness, clarity, completeness | `/cohorts/:id` | — |
| 3 | Написать overall feedback (опционально) | `/cohorts/:id` | — |
| 4 | Нажать **Submit Review** | `/cohorts/:id` | `POST /cohorts/:id/tasks/:tid/submissions/:sid/reviews` |

#### 15.5 Закрытие задачи

| Шаг | Действие | Маршрут | API |
|-----|---------|---------|-----|
| 1 | Master/curator нажимает **Close** на карточке задачи | `/cohorts/:id` | `POST /cohorts/:id/tasks/:tid/close` |
| 2 | Задача переходит в статус `closed` | `/cohorts/:id` | — |

---

### 16. Валидация компетенции и продвижение в Topic Expert

**Актор:** master  
**Цель:** подтвердить, что ученик освоил тему, и присвоить статус эксперта

| Шаг | Действие | Маршрут | API |
|-----|---------|---------|-----|
| 1 | Открыть дашборд когорты | `/cohorts/:id/dashboard` | `GET /cohorts/:id/pending-validations` |
| 2 | В секции Pending Competency Validations найти запись ученика | `/cohorts/:id/dashboard` | — |
| 3 | Нажать **Validate** (отправляет knowledge_check_score и mentor_approved) | `/cohorts/:id/dashboard` | `POST /cohorts/:id/members/:lid/validate-competency` |
| 4 | Нажать **Promote Expert** | `/cohorts/:id/dashboard` | `POST /cohorts/:id/members/:lid/promote-expert` |
| 5 | Ученик появляется в списке Topic Experts на вкладке Progression | `/cohorts/:id` | `GET /cohorts/:id/topic-experts` |

> ⚠️ Шаг 3 сейчас отправляет захардкоженные значения (score=80, approved=true). Требуется форма ввода.

---

### 17. Продвижение ученика в Curator

**Актор:** master  
**Цель:** назначить опытного ученика куратором модуля

| Шаг | Действие | Маршрут | API |
|-----|---------|---------|-----|
| 1 | Открыть дашборд когорты | `/cohorts/:id/dashboard` | `GET /cohorts/:id/pending-promotions` |
| 2 | В секции Pending Curator Promotions найти запись ученика | `/cohorts/:id/dashboard` | — |
| 3 | Нажать **Promote Curator** | `/cohorts/:id/dashboard` | `POST /cohorts/:id/members/:lid/promote-curator` |
| 4 | Ученик получает роль curator и может создавать задачи в когортах этого модуля | — | — |

---

### 18. Завершение и выпуск когорты

**Актор:** master  
**Цель:** закрыть учебный цикл и выпустить учеников

| Шаг | Действие | Маршрут | API |
|-----|---------|---------|-----|
| 1 | Master нажимает **Begin Completing** | `/cohorts/:id` | `POST /cohorts/:id/begin-completing` |
| 2 | Статус переходит в `completing` — новые задачи не создаются | `/cohorts/:id` | — |
| 3 | Master нажимает **Graduate** | `/cohorts/:id` | `POST /cohorts/:id/graduate` |
| 4 | Статус переходит в `graduated` — ученики получают награды | `/cohorts/:id` | — |

Альтернативный исход:

| Шаг | Действие | Маршрут | API |
|-----|---------|---------|-----|
| 3 | Master нажимает **Cancel** (из статуса `active` или `completing`) | `/cohorts/:id` | `POST /cohorts/:id/cancel` |
| 4 | Статус переходит в `cancelled` | `/cohorts/:id` | — |

---

## Награды

### 19. Просмотр баланса наград и истории

**Актор:** learner  
**Цель:** узнать накопленные XP, кредиты, репутацию и посмотреть историю начислений

| Шаг | Действие | Маршрут | API |
|-----|---------|---------|-----|
| 1 | Нажать **Rewards** в навигации | `/me/rewards` | `GET /me/rewards/balance` |
| 2 | Просмотреть тайлы: Total XP, Credits, Reputation Score, Badges | `/me/rewards` | — |
| 3 | Просмотреть таблицу истории начислений | `/me/rewards` | `GET /me/rewards/history` |

---

## Пробел (backend есть, UI нет)

### 20. Получение и вывод комиссионных куратора

**Актор:** curator  
**Цель:** просмотреть начисленные комиссии и вывести доступные средства

> ⚠️ UI-страница `/me/earnings` отсутствует. Ниже описан целевой процесс на основе готовых backend-эндпоинтов.

| Шаг | Действие | Маршрут (цел.) | API |
|-----|---------|----------------|-----|
| 1 | Открыть страницу заработка | `/me/earnings` | `GET /me/earnings` |
| 2 | Просмотреть сводку: total_pending, total_released, список комиссий | `/me/earnings` | — |
| 3 | Для комиссии со статусом `pending` и истёкшим hold period нажать **Release** | `/me/earnings` | `POST /me/earnings/:commission_id/release` |
| 4 | Статус комиссии переходит в `released` | `/me/earnings` | `GET /me/earnings` |
| 5 | Просмотреть полную историю комиссий | `/me/earnings` | `GET /me/earnings/history` |

**Поля комиссии:** commission_id, cohort_id, module_id, base_amount, bonus_amount, total_amount, status, earned_at, release_eligible_at, released_at.
