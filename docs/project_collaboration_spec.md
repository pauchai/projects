---
title: Project Collaboration Spec
---

# Project Collaboration — Design Specification

## 1. Bounded Context

**Name:** Project Collaboration

**Scope:** Users create projects, describe goals and required skills, publish them for recruiting, and manage a team of participants. The context covers the full project lifecycle from draft to completion/cancellation, including application review and role-based team management.

**Out of scope:** Authentication, billing, chat/messaging, task management, file storage. These belong to separate bounded contexts.

---

## 2. Ubiquitous Language

| Term | Definition |
|------|-----------|
| **Project** | A collaborative initiative created by a user. Aggregate root. Has a title, description, required skills, status, and a team of members. |
| **Owner** | The user who created the project. Has full control: edit, publish, manage members, change status. Exactly one per project. |
| **Admin** | A trusted member appointed by the Owner. Can accept/reject applications and manage members (except Owner). |
| **Mentor** | An experienced member who guides others. Same access as Member, distinct role for discoverability. |
| **Member** | A full participant. Works on the project, participates in discussions. |
| **Observer** | A passive participant. Can view the project but does not contribute actively. |
| **Membership** | The relationship between a user and a project. Carries a role and a status (active/removed). |
| **Application Form** | A request from a user to join a project. Contains desired role, motivation text, applicant skills. Can be pending, accepted, or rejected. |
| **Skill Tag** | A keyword describing a competency (e.g., "python", "design", "marketing"). Used for project requirements and participant profiles. |
| **Project Status** | Lifecycle phase: Draft, Recruiting, Active, Completed, Suspended, Cancelled. |

---

## 3. Entities and Value Objects

### 3.1 Project (Aggregate Root)

**Identity:** `project_id: str` (UUID)

**Attributes:**
- `title: str` — project name (3-200 chars)
- `description: str` — detailed description (up to 5000 chars)
- `owner_id: str` — identity of the creator
- `required_skills: list[SkillTag]` — skills the project is looking for
- `status: ProjectStatus` — current lifecycle phase
- `max_members: int | None` — optional cap on team size
- `created_at: datetime`
- `memberships: list[Membership]` — current team
- `applications: list[ApplicationForm]` — pending/resolved applications
- `events: list[DomainEvent]` — uncommitted domain events

**Invariants:**
- Status transitions follow the state machine (see section 4).
- Exactly one membership with role Owner exists at all times.
- A user cannot have more than one active membership per project.
- A user cannot submit a new application if they already have a pending application or active membership.
- Owner cannot be removed from the project.
- Only Owner and Admin can accept/reject applications and manage members.

### 3.2 Membership (Entity)

**Identity:** `membership_id: str` (UUID)

**Attributes:**
- `user_id: str`
- `project_id: str`
- `role: ProjectRole`
- `is_active: bool`
- `joined_at: datetime`

### 3.3 ApplicationForm (Entity)

**Identity:** `application_id: str` (UUID)

**Attributes:**
- `applicant_id: str`
- `project_id: str`
- `desired_role: ProjectRole`
- `motivation: str` (up to 2000 chars)
- `applicant_skills: list[SkillTag]`
- `status: ApplicationStatus` — Pending, Accepted, Rejected
- `reviewed_by: str | None` — who made the decision
- `submitted_at: datetime`

**Invariants:**
- Desired role cannot be Owner (only one Owner, assigned at creation).
- Status transitions: Pending -> Accepted, Pending -> Rejected. Terminal states.

### 3.4 ProjectStatus (Enum / Value Object)

```
Draft -> Recruiting -> Active -> Completed
                   \        \-> Suspended -> Active
                    \        \-> Cancelled
                     \-> Suspended -> Recruiting
                      \-> Cancelled
```

| From | To | Trigger |
|------|-----|---------|
| Draft | Recruiting | Owner publishes the project |
| Recruiting | Active | Owner activates (team assembled) |
| Recruiting | Suspended | Owner suspends recruiting |
| Recruiting | Cancelled | Owner cancels the project |
| Active | Completed | Owner marks as completed |
| Active | Suspended | Owner suspends work |
| Active | Cancelled | Owner cancels the project |
| Suspended | Active | Owner resumes (if was Active before) |
| Suspended | Recruiting | Owner resumes (if was Recruiting before) |

**Terminal states:** Completed, Cancelled — no transitions out.

### 3.5 ProjectRole (Enum)

Ordered by privilege level (descending):

1. `Owner` — full control, one per project
2. `Admin` — manage members, accept/reject applications
3. `Mentor` — experienced participant, advisory role
4. `Member` — active contributor
5. `Observer` — view-only access

### 3.6 SkillTag (Value Object)

- Immutable, lowercase, alphanumeric + hyphens.
- Max 50 chars.
- Compared by value.

### 3.7 ApplicationStatus (Enum)

- `Pending` — awaiting review
- `Accepted` — applicant joined the project
- `Rejected` — application declined

---

## 4. State Machine — Project Lifecycle

```
                    +-----------+
                    |   Draft   |
                    +-----+-----+
                          |
                       publish()
                          |
                    +-----v-------+
              +---->| Recruiting  |<----+
              |     +--+----+--+--+     |
              |        |    |  |        |
              |  activate() |  |    resume()
              |        |    |  |        |
              |   +----v-+  |  |  +-----+-----+
              |   |Active|  |  +->| Suspended  |
              |   +--+---+  |     +-----+------+
              |      |      |           ^
              |  complete() |  suspend() |
              |  suspend()  |           |
              |  cancel()   +-----------+
              |      |      cancel()
              |      v
              | +-----------+    +-----------+
              | | Completed |    | Cancelled |
              | +-----------+    +-----------+
              |                        ^
              +------------------------+
```

---

## 5. Use Cases

### 5.1 CreateProject
- **Actor:** Any authenticated user
- **Input:** title, description, required_skills, max_members (optional)
- **Result:** Project created in Draft status. Creator becomes Owner.
- **Event:** `ProjectCreated`

### 5.2 PublishProject
- **Actor:** Owner
- **Input:** project_id
- **Precondition:** Project is in Draft status
- **Result:** Status changes to Recruiting. Project becomes discoverable.
- **Event:** `ProjectPublished`

### 5.3 ApplyToProject
- **Actor:** Any authenticated user (not already a member or applicant)
- **Input:** project_id, desired_role, motivation, applicant_skills
- **Precondition:** Project is in Recruiting status. User has no active membership or pending application.
- **Result:** ApplicationForm created with Pending status.
- **Event:** `ApplicationSubmitted`

### 5.4 ReviewApplication (Accept)
- **Actor:** Owner or Admin
- **Input:** application_id
- **Precondition:** Application is Pending. Project not at max_members.
- **Result:** Application status -> Accepted. New Membership created with desired_role.
- **Events:** `ApplicationAccepted`, `MemberJoined`

### 5.5 ReviewApplication (Reject)
- **Actor:** Owner or Admin
- **Input:** application_id, reason (optional)
- **Precondition:** Application is Pending.
- **Result:** Application status -> Rejected.
- **Event:** `ApplicationRejected`

### 5.6 ChangeMemberRole
- **Actor:** Owner or Admin
- **Input:** membership_id, new_role
- **Precondition:** Target is not Owner. New role is not Owner. Actor has sufficient privilege.
- **Result:** Membership role updated.
- **Event:** `MemberRoleChanged`

### 5.7 RemoveMember
- **Actor:** Owner or Admin
- **Input:** membership_id
- **Precondition:** Target is not Owner. Actor has sufficient privilege.
- **Result:** Membership deactivated (is_active = False).
- **Event:** `MemberRemoved`

### 5.8 ActivateProject
- **Actor:** Owner
- **Input:** project_id
- **Precondition:** Project is in Recruiting status.
- **Result:** Status changes to Active.
- **Event:** `ProjectActivated`

### 5.9 SuspendProject
- **Actor:** Owner
- **Input:** project_id
- **Precondition:** Project is in Recruiting or Active status.
- **Result:** Status changes to Suspended. Previous status is remembered for resume.
- **Event:** `ProjectSuspended`

### 5.10 ResumeProject
- **Actor:** Owner
- **Input:** project_id
- **Precondition:** Project is in Suspended status.
- **Result:** Status reverts to the status before suspension (Recruiting or Active).
- **Event:** `ProjectResumed`

### 5.11 CompleteProject
- **Actor:** Owner
- **Input:** project_id
- **Precondition:** Project is in Active status.
- **Result:** Status changes to Completed (terminal).
- **Event:** `ProjectCompleted`

### 5.12 CancelProject
- **Actor:** Owner
- **Input:** project_id
- **Precondition:** Project is in Recruiting, Active, or Suspended status.
- **Result:** Status changes to Cancelled (terminal).
- **Event:** `ProjectCancelled`

### 5.13 SearchProjects
- **Actor:** Any authenticated user
- **Input:** skill_tags (optional), keyword (optional), status filter (default: Recruiting)
- **Result:** List of matching projects.
- **Note:** Read-only query. No domain events. Implementation via a read model or repository query method.

---

## 6. Ports (Driven Interfaces)

### ProjectRepository (Protocol)
- `find_by_id(project_id: str) -> Project | None`
- `save(project: Project) -> None`
- `search(skills: list[SkillTag] | None, keyword: str | None, status: ProjectStatus | None) -> list[Project]`

### UnitOfWork (Protocol)
Coordinates atomic persistence of domain changes. Application Services manage the UoW lifecycle.

- `projects: ProjectRepository`
- `__enter__() -> UnitOfWork`
- `__exit__(*args) -> None`
- `commit() -> None`
- `rollback() -> None`

**Usage:**
```python
with uow:
    project = uow.projects.find_by_id("p1")
    project.publish()
    uow.projects.save(project)
    uow.commit()
```

**Note:** `MembershipRepository` and `ApplicationRepository` are not needed as separate ports — all operations go through the Project aggregate root, which manages its own memberships and applications internally.

---

## 7. Domain Events

| Event | Emitted by | Payload |
|-------|-----------|---------|
| `ProjectCreated` | CreateProject | project_id, owner_id, title |
| `ProjectPublished` | PublishProject | project_id |
| `ProjectActivated` | ActivateProject | project_id |
| `ProjectSuspended` | SuspendProject | project_id |
| `ProjectResumed` | ResumeProject | project_id |
| `ProjectCompleted` | CompleteProject | project_id |
| `ProjectCancelled` | CancelProject | project_id |
| `ApplicationSubmitted` | ApplyToProject | application_id, project_id, applicant_id |
| `ApplicationAccepted` | ReviewApplication | application_id, project_id, applicant_id |
| `ApplicationRejected` | ReviewApplication | application_id, project_id, applicant_id |
| `MemberJoined` | ReviewApplication | membership_id, project_id, user_id, role |
| `MemberRoleChanged` | ChangeMemberRole | membership_id, project_id, new_role |
| `MemberRemoved` | RemoveMember | membership_id, project_id, user_id |

---

## 8. Authorization

Authorization is enforced at the **Application Layer** (use case level). Each use case verifies the caller's identity against the project before performing the operation.

**Design decisions:**
- Inline checks in `execute()` — no decorators, no separate domain service.
- Three query methods on the Project aggregate support authorization: `is_owner(user_id)`, `find_membership_by_user_id(user_id)`, `has_management_rights(user_id)`.
- `PermissionError` (Python built-in) is raised for authorization failures, distinct from `ValueError` (business rule violations) and `LookupError` (entity not found).
- `caller_id: str` parameter is added to use cases that need it. Where an existing parameter already carries the caller's identity (e.g., `reviewed_by`), it is reused.

| Use Case | Required Role | Parameter | Check |
|----------|--------------|-----------|-------|
| CreateProject | Any authenticated user | `owner_id` | No project-level auth (project doesn't exist yet) |
| PublishProject | Owner | `caller_id` | `project.is_owner(caller_id)` |
| ApplyToProject | Any authenticated user | `applicant_id` | No project-level auth |
| AcceptApplication | Owner or Admin | `reviewed_by` | `project.has_management_rights(reviewed_by)` |
| RejectApplication | Owner or Admin | `reviewed_by` | `project.has_management_rights(reviewed_by)` |
| ChangeMemberRole | Owner or Admin | `caller_id` | `project.has_management_rights(caller_id)` |
| RemoveMember | Owner or Admin | `caller_id` | `project.has_management_rights(caller_id)` |
| ActivateProject | Owner | `caller_id` | `project.is_owner(caller_id)` |
| SuspendProject | Owner | `caller_id` | `project.is_owner(caller_id)` |
| ResumeProject | Owner | `caller_id` | `project.is_owner(caller_id)` |
| CompleteProject | Owner | `caller_id` | `project.is_owner(caller_id)` |
| CancelProject | Owner | `caller_id` | `project.is_owner(caller_id)` |
| SearchProjects | Any authenticated user | — | No auth needed |

---

## 9. Directory Structure

```
src/project_collaboration/
    __init__.py
    domain/
        __init__.py
        project.py              # Project aggregate root
        project_status.py       # ProjectStatus enum + transitions
        membership.py           # Membership entity
        application_form.py     # ApplicationForm entity + ApplicationStatus
        role.py                 # ProjectRole enum
        skill_tag.py            # SkillTag value object
        events.py               # Domain event dataclasses
        ports.py                # ProjectRepository, UnitOfWork Protocols
    application/
        __init__.py
        create_project.py       # CreateProjectUseCase
        publish_project.py      # PublishProjectUseCase
        apply_to_project.py     # ApplyToProjectUseCase
        review_application.py   # AcceptApplicationUseCase, RejectApplicationUseCase
        manage_member.py        # ChangeMemberRoleUseCase, RemoveMemberUseCase
        change_project_status.py # Activate, Suspend, Resume, Complete, Cancel
        search_projects.py      # SearchProjectsUseCase

tests/project_collaboration/
    __init__.py
    domain/
        __init__.py
        test_project.py
        test_project_status.py
        test_membership.py
        test_application_form.py
        test_role.py
        test_skill_tag.py
        test_events.py
    application/
        __init__.py
        test_create_project.py
        test_publish_project.py
        test_apply_to_project.py
        test_review_application.py
        test_manage_member.py
        test_change_project_status.py
        test_search_projects.py
    fakes/
        __init__.py
        fake_unit_of_work.py    # FakeUnitOfWork with in-memory repos
        test_unit_of_work.py
```
