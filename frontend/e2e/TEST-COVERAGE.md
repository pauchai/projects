# E2E Test Coverage — Visual Overview

30 tests across 5 spec files covering the complete user journey from authentication
to cohort management, task execution, peer review, competency validation, and earnings.

## Test Personas

| Persona    | Email               | Password      | Role                          |
|------------|---------------------|---------------|-------------------------------|
| `master`   | `master@e2e.test`   | `e2epassword` | Cohort creator                |
| `learner1` | `learner1@e2e.test` | `e2epassword` | Active cohort member          |
| `learner2` | `learner2@e2e.test` | `e2epassword` | Active cohort member          |
| `outsider` | `outsider@e2e.test` | `e2epassword` | Authenticated, not in cohort  |

Authenticated sessions are stored in `e2e/.auth/` (git-ignored) and reused across
all tests in a run without going through the login UI.

## Test Summary

| Spec file                          | Tests | What it covers                                    |
|------------------------------------|------:|---------------------------------------------------|
| `access-control.spec.ts`           |     7 | Route guards, role-based UI visibility            |
| `cohort-lifecycle.spec.ts`         |     6 | Create → enrol → activate → cancel               |
| `task-flow.spec.ts`                |     5 | Create task → submit → peer review → master view  |
| `dashboard-validation.spec.ts`     |     4 | Pending competency card, validate, access denied  |
| `earnings.spec.ts`                 |     5 | Page structure, zero state, route protection      |
| **Total**                          |**30** |                                                   |

---

## Entity Relationship Diagram

```mermaid
erDiagram
    USER ||--o{ COHORT : "creates"
    USER }o--o{ COHORT : "enrolled_in"
    COHORT ||--o{ TASK : "contains"
    TASK ||--o{ SUBMISSION : "has"
    SUBMISSION ||--o{ REVIEW : "receives"
    USER ||--o{ SUBMISSION : "submits"
    USER ||--o{ REVIEW : "writes"

    USER {
        string user_id PK
        string email
        string role "master | learner | outsider"
    }

    COHORT {
        string cohort_id PK
        string module_id FK
        string master_id FK
        string status "forming | active | cancelled"
    }

    TASK {
        string task_id PK
        string cohort_id FK
        string topic_id FK
        string title
        string status "draft | active | closed"
    }

    SUBMISSION {
        string submission_id PK
        string task_id FK
        string user_id FK
        string content
        string status "pending | reviewed"
    }

    REVIEW {
        string review_id PK
        string submission_id FK
        string reviewer_id FK
        int score_correctness
        int score_clarity
        int score_completeness
    }

    PENDING_VALIDATION {
        string validation_id PK
        string cohort_id FK
        string learner_id FK
        int knowledge_score
        bool mentor_approved
        string status "pending | validated"
    }

    COMMISSION {
        string commission_id PK
        string user_id FK
        float amount
        string status "pending | released"
    }

    USER ||--o{ PENDING_VALIDATION : "subject_of"
    COHORT ||--o{ PENDING_VALIDATION : "scoped_to"
    USER ||--o{ COMMISSION : "earns"
```

---

## User Journey Flowchart

```mermaid
flowchart TB
    subgraph Auth["🔒 Access Control  ·  access-control.spec.ts  (7 tests)"]
        A1([Unauthenticated]) -->|GET /cohorts| A2[/Redirect → /login/]
        A1 -->|GET /cohorts/new| A2
        A1 -->|GET /me/earnings| A2

        A3([master]) -->|cohort page| A4[Dashboard link visible]
        A5([learner]) -->|cohort page| A6[Dashboard link hidden]
        A7([outsider]) -->|cohort page| A8[Page loads, no Enrol form]

        A3 -->|forming cohort| A9[Activate button visible]
        A3 -->|active cohort| A10[Begin Completing button visible]
        A3 -->|GET /cohorts/:id/dashboard| A11[Dashboard page loads]
    end

    subgraph Cohort["📋 Cohort Lifecycle  ·  cohort-lifecycle.spec.ts  (6 tests)"]
        C1([master]) -->|/cohorts/new form| C2[Cohort created]
        C2 --> C3[Status: forming]
        C3 -->|Enrol form| C4[learner1 added to members list]
        C3 -->|Activate button| C5[Status: active]
        C3 -->|Cancel button| C6[Status: cancelled — no action buttons]
        C4 --> C7([learner1])
        C7 -->|/cohorts list| C8[Cohort visible before activation]
        C5 --> C9([learner1])
        C9 -->|cohort page| C10[active badge visible]
    end

    subgraph Task["✅ Task Flow  ·  task-flow.spec.ts  (5 tests)"]
        T1([master]) -->|+ Create Task form| T2[Task created]
        T2 --> T3[Status: draft]
        T3 -->|learner1 on tasks tab| T4[No Submit Solution button]
        T3 -->|Activate button| T5[Status: active]
        T5 -->|learner1 Submit Solution| T6[Solution submitted]
        T6 --> T7[Status: submitted]
        T7 -->|learner2 Review button| T8[Peer review form opens]
        T8 -->|Submit Review| T9[Review recorded]
        T6 --> T10([master])
        T10 -->|tasks tab| T11[Sees learner1 + learner2 user IDs]
    end

    subgraph Dashboard["📊 Dashboard Validation  ·  dashboard-validation.spec.ts  (4 tests)"]
        D1([learner1]) -->|submits solution ×2| D2[2 submissions]
        D3([learner2]) -->|reviews both| D4[2 peer reviews]
        D2 & D4 --> D5[Pending Competency Validation created]
        D5 --> D6([master])
        D6 -->|/dashboard| D7[Sees pending validation card with learner1 ID]
        D7 -->|score 101| D8[Validate button disabled]
        D7 -->|score 80 + mentor ✓| D9[Click Validate]
        D9 --> D10[Competency validated ✓]
        D11([learner1]) -->|/dashboard| D12[Access denied message]
    end

    subgraph Earnings["💰 Earnings Page  ·  earnings.spec.ts  (5 tests)"]
        E1([master]) -->|/me/earnings| E2[My Earnings heading]
        E2 --> E3[Pending 0.00 · Released 0.00]
        E2 --> E4[No commissions yet.]
        E2 --> E5[No Release button]
        E6([learner1]) -->|/me/earnings| E7[My Earnings heading]
        E7 --> E8[No commissions yet.]
    end

    Auth ~~~ Cohort
    Cohort ~~~ Task
    Task ~~~ Dashboard
    Dashboard ~~~ Earnings
```
