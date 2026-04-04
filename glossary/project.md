# Projects & Members — Ubiquitous Language Glossary

This glossary defines the authoritative vocabulary for the **Projects & Members** bounded context. All code, documentation, API contracts, and team communication within this context MUST use these terms consistently.

**Bounded Context scope:** Project lifecycle management (creation, activation, completion, archival), member invitations (email, link, auto-join by domain), membership with role-based access (Owner / Member / Viewer), project-scoped permissions, and capacity management (seats, quotas).

**Collaborative workspace model:** A Project is a shared workspace where users collaborate on content. Users join projects through invitations, invite links, or auto-join rules. Each participant has a single role that determines their level of access.

**Code mapping convention:**

- Python: `project/domain/` for domain models, `project/application/` for use cases, `project/infrastructure/` for adapters
 `packages/project/src/domain/`, `packages/project/src/application/`, `packages/project/src/infrastructure/`

**Cross-context dependencies:** This context references identities from the [Auth bounded context](./auth.md). A [Member](#member) is always linked to an [AuthUser](./auth.md#authuser) via `IdentityId`, but the two models are separate — Auth owns credentials and sessions, Projects owns membership, roles, and project-scoped permissions.

---

## 1. Project Core

### Project

**Definition:** A collaborative workspace owned by a user, serving as the top-level organizational unit within this bounded context. A Project groups content, members, settings, and permissions into a single isolated scope.

**Context:** A Project is created by a user who automatically becomes its [Owner](#owner). Every Project has a unique [Project Id](#project-id), a human-readable [Project Slug](#project-slug), configurable [Project Settings](#project-settings), and a [Project Status](#project-status) that governs its lifecycle. A single [AuthUser](./auth.md#authuser) can own multiple Projects and be a [Member](#member) of many others simultaneously.

**Code mapping:**

- Python: `Project` aggregate root in `project/domain/project.py`
 `Project` class in `packages/project/src/domain/project.ts`

**Related terms:** [Project Id](#project-id), [Project Slug](#project-slug), [Project Status](#project-status), [Project Settings](#project-settings), [Member](#member), [Owner](#owner)

**Not to be confused with:** `Workspace` or `Organization` in multi-tenant SaaS systems — a Project is scoped to content collaboration, not to billing or identity management. Billing plans may be linked to a Project through the Billing context, but Project does not own subscription data.

---

### Project Id

**Definition:** A globally unique, immutable identifier assigned to a [Project](#project) at creation time. Typically a UUID v4 or ULID. Used as the primary key in storage and as the canonical reference in cross-context communication.

**Context:** Project Id never changes throughout the Project's lifecycle, even when the [Project Slug](#project-slug) or name is updated. All cross-context events and API contracts reference the Project by its Project Id, never by slug or name.

**Code mapping:**

- Python: `ProjectId` value object (branded `str`) in `project/domain/project_id.py`
 `ProjectId` branded type in `packages/project/src/domain/project-id.ts`

**Related terms:** [Project](#project), [Project Slug](#project-slug)

---

### Project Slug

**Definition:** A URL-friendly, human-readable identifier for a [Project](#project). Derived from the project name at creation time, unique within the system, and modifiable by the [Owner](#owner).

**Context:** Used in URLs (e.g., `/projects/my-awesome-project`) and in user-facing contexts where a UUID would be unwieldy. Slugs are lowercase, alphanumeric with hyphens, and have a maximum length (typically 64 characters). Changing a slug should set up a redirect from the old slug for a grace period.

**Code mapping:**

- Python: `ProjectSlug` value object in `project/domain/project_slug.py`
 `ProjectSlug` branded type in `packages/project/src/domain/project-slug.ts`

**Related terms:** [Project](#project), [Project Id](#project-id)

---

### Project Status

**Definition:** An enum representing the current lifecycle phase of a [Project](#project). Valid values: `Draft`, `Active`, `Completed`, `Archived`.

**Context:** Project Status governs which operations are permitted. See [Section 4: Project Lifecycle](#4-project-lifecycle) for detailed state definitions and transition rules. Status transitions emit [Project Events](#project-event) consumed by other bounded contexts.

**Code mapping:**

- Python: `ProjectStatus` enum in `project/domain/project_status.py`
 `ProjectStatus` union type in `packages/project/src/domain/project-status.ts`

**Related terms:** [Project](#project), [Draft State](#draft-state), [Active State](#active-state), [Completed State](#completed-state), [Archived State](#archived-state), [Project Transition](#project-transition)

---

### Project Settings

**Definition:** A configuration object attached to a [Project](#project) that controls its behavior: display name, description, [Project Visibility](#project-visibility), default role for new members, notification preferences, and [Member Limit](#member-limit) overrides.

**Context:** Project Settings are mutable by [Owner](#owner) and, depending on configuration, by members with the `manage_settings` [Project Permission](#project-permission). Changes to settings emit a `ProjectSettingsUpdated` [Project Event](#project-event). Settings do not include billing or authentication configuration — those belong to their respective bounded contexts.

**Code mapping:**

- Python: `ProjectSettings` dataclass in `project/domain/project_settings.py`
 `ProjectSettings` interface in `packages/project/src/domain/project-settings.ts`

**Related terms:** [Project](#project), [Project Visibility](#project-visibility), [Owner](#owner), [Member Limit](#member-limit)

---

### Project Visibility

**Definition:** A classification that determines who can discover and request access to a [Project](#project). Values: `Private` (visible only to current members), `Internal` (visible to all authenticated users within the platform), `Public` (visible to anyone, including unauthenticated users).

**Context:** Visibility controls discoverability, not access. Even a `Public` project requires [Membership](#membership) for write access — unauthenticated or non-member users can only view content if the project is `Public`. `Internal` visibility is useful for company-wide knowledge bases where any employee can find the project but must still join to contribute.

**Code mapping:**

- Python: `ProjectVisibility` enum in `project/domain/project_visibility.py`
 `ProjectVisibility` union type in `packages/project/src/domain/project-visibility.ts`

**Related terms:** [Project Settings](#project-settings), [Invite Link](#invite-link), [Auto-Join Rule](#auto-join-rule)

---

### Project Event

**Definition:** A domain event emitted when a significant action occurs within the Projects & Members bounded context. Project Events are the official contract for cross-context consumers.

**Context:** Examples: `ProjectCreated`, `ProjectActivated`, `ProjectCompleted`, `ProjectArchived`, `ProjectSettingsUpdated`, `MemberJoined`, `MemberRemoved`, `MemberRoleChanged`, `InvitationSent`, `InvitationAccepted`, `InviteLinkCreated`, `SeatLimitReached`. Events follow the Published Language pattern (see [AGENTS.md 4.3](../AGENTS.md#43-context-mapping-карта-контекстов)). Each event carries the `ProjectId`, a timestamp, the actor's `IdentityId`, and event-specific payload.

**Code mapping:**

- Python: `ProjectEvent` base dataclass in `project/domain/events.py` with specific subclasses (`ProjectCreatedEvent`, `MemberJoinedEvent`, etc.)
 `ProjectEvent` union type in `packages/project/src/domain/events.ts` with specific types (`ProjectCreatedEvent`, `MemberJoinedEvent`, etc.)

**Related terms:** [Project](#project), [Membership Event](#membership-event), [Invitation Event](#invitation-event), [Capacity Event](#capacity-event)

---

## 2. Membership & Roles

### Member

**Definition:** A user who has an active association with a [Project](#project). A Member is the core participant entity within this bounded context — it represents the user in the context of a specific project, carrying a [Project Role](#project-role) and a [Membership Status](#membership-status).

**Context:** Every Member is linked to an [AuthUser](./auth.md#authuser) via `IdentityId`, but `Member` is a separate domain model — it does not inherit from or extend `AuthUser`. A user becomes a Member by accepting an [Invitation](#invitation), joining via an [Invite Link](#invite-link), being added through an [Auto-Join Rule](#auto-join-rule), or by creating the project (automatic [Owner](#owner) assignment). A single `AuthUser` can be a Member of multiple projects with different roles in each.

**Code mapping:**

- Python: `Member` entity in `project/domain/member.py`
 `Member` class in `packages/project/src/domain/member.ts`

**Related terms:** [Membership](#membership), [Project Role](#project-role), [Membership Status](#membership-status), [Owner](#owner)

**Not to be confused with:** [AuthUser](./auth.md#authuser) in the Auth context (owns credentials, sessions, system-wide roles), [Partner](./partnership.md#partner) in the Partnership context (owns referral relationships, commissions), or `BillingCustomer` in Billing (owns payment methods, subscriptions). A single person may be all of these, but each context maintains its own model.

---

### Membership

**Definition:** The relationship entity that binds a [Member](#member) to a [Project](#project). Encapsulates the [Project Role](#project-role), [Membership Status](#membership-status), join date, and the method by which the user joined (invitation, invite link, auto-join, or project creation).

**Context:** Membership is a first-class domain concept, not just a join table. It has its own lifecycle: created when a user joins a project, updated when roles change, and terminated when a member is removed or leaves voluntarily. Each Membership is uniquely identified by the combination of `ProjectId` + `IdentityId`. A user can have at most one active Membership per Project.

**Code mapping:**

- Python: `Membership` entity in `project/domain/membership.py`
 `Membership` class in `packages/project/src/domain/membership.ts`

**Related terms:** [Member](#member), [Project](#project), [Project Role](#project-role), [Membership Status](#membership-status), [Membership Event](#membership-event)

---

### Project Role

**Definition:** An enum that classifies a [Member](#member)'s level of access within a [Project](#project). Valid values: `Owner`, `Member`, `Viewer`. Each role maps to a fixed set of [Project Permissions](#project-permission) via the [Permission Matrix](#permission-matrix).

**Context:** Roles are hierarchical: Owner > Member > Viewer. A higher role includes all permissions of lower roles plus additional ones. Roles are assigned at join time (based on [Invitation](#invitation) or [Invite Link Policy](#invite-link-policy) settings) and can be changed by anyone with the `manage_members` [Project Permission](#project-permission) (typically Owner). See individual role definitions below for details.

**Code mapping:**

- Python: `ProjectRole` enum in `project/domain/project_role.py`
 `ProjectRole` union type in `packages/project/src/domain/project-role.ts`

**Related terms:** [Owner](#owner), [Member Role](#member-role), [Viewer Role](#viewer-role), [Permission Matrix](#permission-matrix), [Project Permission](#project-permission)

---

### Owner

**Definition:** The highest-privilege [Project Role](#project-role). The Owner has full control over the [Project](#project): managing settings, members, invitations, lifecycle transitions, and the ability to [Transfer Ownership](#transfer-ownership) to another member.

**Context:** Every Project has exactly one Owner at any given time. The user who creates the project is automatically assigned the Owner role. Ownership can be transferred but not shared — there is no "co-owner" concept. If the Owner's [AuthUser](./auth.md#authuser) account is deactivated, the platform must have a policy for orphaned projects (e.g., auto-assign to next eligible member, or freeze the project).

**Code mapping:**

- Python: `ProjectRole.OWNER` enum member in `project/domain/project_role.py`
 `"owner"` literal in `ProjectRole` union type

**Related terms:** [Project Role](#project-role), [Transfer Ownership](#transfer-ownership), [Project](#project)

**Not to be confused with:** System-wide `Admin` [Role](./auth.md#role) in the Auth context — an Auth Admin has platform-wide privileges, while a Project Owner only has control within their specific project.

---

### Member Role

**Definition:** The standard-access [Project Role](#project-role). A Member can create and edit content, participate in collaboration, but cannot manage other members, change project settings, or perform lifecycle transitions.

**Context:** This is the default role assigned when a user joins via an [Invite Link](#invite-link) (unless the [Invite Link Policy](#invite-link-policy) specifies otherwise). Members form the majority of participants in most projects. They can view all project content and contribute, but administrative operations are reserved for the [Owner](#owner).

**Code mapping:**

- Python: `ProjectRole.MEMBER` enum member in `project/domain/project_role.py`
 `"member"` literal in `ProjectRole` union type

**Related terms:** [Project Role](#project-role), [Owner](#owner), [Viewer Role](#viewer-role), [Permission Matrix](#permission-matrix)

---

### Viewer Role

**Definition:** The read-only [Project Role](#project-role). A Viewer can see all project content but cannot create, edit, or delete anything. Viewers cannot manage members or settings.

**Context:** Useful for stakeholders, clients, or auditors who need visibility into project progress without the ability to modify content. Viewers still count as active [Members](#member) and occupy a [Seat](#seat) for billing purposes.

**Code mapping:**

- Python: `ProjectRole.VIEWER` enum member in `project/domain/project_role.py`
 `"viewer"` literal in `ProjectRole` union type

**Related terms:** [Project Role](#project-role), [Owner](#owner), [Member Role](#member-role), [Seat](#seat)

---

### Membership Status

**Definition:** The current state of a [Membership](#membership). Values: `Active` (normal operational state), `Suspended` (temporarily disabled — member cannot access the project but the relationship is preserved), `Removed` (membership terminated — soft delete).

**Context:** Only `Active` memberships grant access. `Suspended` is used for temporary restrictions (e.g., pending investigation, billing issues) — the member can be reactivated without a new invitation. `Removed` is the terminal state: to rejoin, the user must go through the invitation process again. Membership status changes emit [Membership Events](#membership-event).

**Code mapping:**

- Python: `MembershipStatus` enum in `project/domain/membership_status.py`
 `MembershipStatus` union type in `packages/project/src/domain/membership-status.ts`

**Related terms:** [Membership](#membership), [Membership Event](#membership-event), [Member](#member)

---

### Membership Event

**Definition:** A domain event emitted when the state of a [Membership](#membership) changes. A specialized subset of [Project Events](#project-event).

**Context:** Examples: `MemberJoined` (new member added, includes join method), `MemberRoleChanged` (role upgraded or downgraded), `MemberSuspended`, `MemberReactivated`, `MemberRemoved`, `MemberLeft` (voluntary departure), `OwnershipTransferred`. Each event carries `ProjectId`, `IdentityId` of the affected member, `IdentityId` of the actor (who initiated the change), and the relevant state change payload.

**Code mapping:**

- Python: `MembershipEvent` subclasses of `ProjectEvent` in `project/domain/events.py` (`MemberJoinedEvent`, `MemberRoleChangedEvent`, etc.)
 Membership-specific types within `ProjectEvent` union in `packages/project/src/domain/events.ts`

**Related terms:** [Membership](#membership), [Membership Status](#membership-status), [Project Event](#project-event)

---

## 3. Invitations

### Invitation

**Definition:** A personal, directed request for a specific user (identified by email address) to join a [Project](#project) with a designated [Project Role](#project-role). An Invitation has its own lifecycle ([Invitation Status](#invitation-status)) and is the formal mechanism for controlled member onboarding.

**Context:** Invitations are created by any [Member](#member) with the `manage_members` [Project Permission](#project-permission) (typically the [Owner](#owner)). Each Invitation targets a single email address and specifies the role the invitee will receive upon acceptance. If the email does not correspond to an existing [AuthUser](./auth.md#authuser) account, the system must handle account creation as part of the acceptance flow (coordinated with the Auth context). Duplicate invitations to the same email for the same project are rejected.

**Code mapping:**

- Python: `Invitation` entity in `project/domain/invitation.py`
 `Invitation` class in `packages/project/src/domain/invitation.ts`

**Related terms:** [Invitation Status](#invitation-status), [Invitation Token](#invitation-token), [Invitation Event](#invitation-event), [Member](#member), [Project Role](#project-role)

**Not to be confused with:** [Invite Link](#invite-link) — an Invitation is personal (targets a specific email), while an Invite Link is a reusable URL that anyone can use to join.

---

### Invitation Status

**Definition:** The current state of an [Invitation](#invitation). Values: `Pending` (sent but not yet acted upon), `Accepted` (invitee joined the project), `Declined` (invitee explicitly refused), `Expired` (time-to-live exceeded without action), `Revoked` (withdrawn by the inviter or Owner before acceptance).

**Context:** Status transitions follow strict rules: `Pending` → `Accepted` | `Declined` | `Expired` | `Revoked`. Once an Invitation leaves the `Pending` state, it is terminal — no further transitions are allowed. A new Invitation must be created if needed after expiration, decline, or revocation. Default TTL is configurable in [Project Settings](#project-settings) (e.g., 7 days).

**Code mapping:**

- Python: `InvitationStatus` enum in `project/domain/invitation_status.py`
 `InvitationStatus` union type in `packages/project/src/domain/invitation-status.ts`

**Related terms:** [Invitation](#invitation), [Invitation Token](#invitation-token)

---

### Invitation Token

**Definition:** A single-use, cryptographically secure token embedded in the invitation acceptance URL. The token uniquely identifies the [Invitation](#invitation) and proves the recipient is the intended invitee.

**Context:** Generated at invitation creation time. The token is sent as part of the acceptance link (e.g., `/invitations/accept?token=abc123`). It is valid only while the [Invitation Status](#invitation-status) is `Pending`. Once used (acceptance) or invalidated (expiration, revocation), the token cannot be reused. Tokens are hashed in storage; only the email recipient receives the plaintext.

**Code mapping:**

- Python: `InvitationToken` value object in `project/domain/invitation_token.py`
 `InvitationToken` branded type in `packages/project/src/domain/invitation-token.ts`

**Related terms:** [Invitation](#invitation), [Invitation Status](#invitation-status)

**Not to be confused with:** [Project-Scoped Token](#project-scoped-token) (an API access token for a specific project) or [Access Token](./auth.md#access-token) in Auth (authenticates a user session).

---

### Invite Link

**Definition:** A reusable, shareable URL that allows any user to join a [Project](#project) without a personal [Invitation](#invitation). The link encodes a unique token and is governed by an [Invite Link Policy](#invite-link-policy).

**Context:** Invite Links are a convenience mechanism for open or semi-open projects. Any user who follows the link and authenticates (or creates an account) will be added as a [Member](#member) with the role specified in the link's [Invite Link Policy](#invite-link-policy). Unlike personal Invitations, Invite Links are not targeted at a specific email and can be used multiple times (up to the configured limit). They are created by members with the `manage_members` permission and can be deactivated or regenerated at any time.

**Code mapping:**

- Python: `InviteLink` entity in `project/domain/invite_link.py`
 `InviteLink` class in `packages/project/src/domain/invite-link.ts`

**Related terms:** [Invite Link Policy](#invite-link-policy), [Invitation](#invitation), [Member](#member)

**Not to be confused with:** [Referral Link](./partnership.md#referral-link) in the Partnership context — a Referral Link tracks who referred a new user for commission purposes, while an Invite Link adds a user to a specific project. They may coexist: a user can arrive via a Referral Link and then join a project via an Invite Link.

---

### Invite Link Policy

**Definition:** A configuration object attached to an [Invite Link](#invite-link) that governs its behavior: default [Project Role](#project-role) for users who join through the link, maximum number of uses (or unlimited), expiration date (or no expiration), and whether joining requires approval.

**Context:** Policies allow fine-grained control over link behavior without creating separate links for each scenario. For example, an Owner may create one link that assigns the `Viewer` role with unlimited uses for public distribution, and another that assigns the `Member` role with a 10-use limit for a specific team. Changing a policy applies to future uses only — existing memberships created through the link are not retroactively affected.

**Code mapping:**

- Python: `InviteLinkPolicy` value object in `project/domain/invite_link_policy.py`
 `InviteLinkPolicy` interface in `packages/project/src/domain/invite-link-policy.ts`

**Related terms:** [Invite Link](#invite-link), [Project Role](#project-role), [Member Limit](#member-limit)

---

### Auto-Join Rule

**Definition:** A rule that automatically grants [Membership](#membership) to any user whose email address matches a specified domain pattern. When an [AuthUser](./auth.md#authuser) with a matching email authenticates and navigates to the [Project](#project), they are added as a [Member](#member) without requiring an explicit [Invitation](#invitation) or [Invite Link](#invite-link).

**Context:** Designed for organization-internal projects where all employees of a company should have access. For example, a rule matching `@acme.com` would auto-add any Acme employee who accesses the project. Each Auto-Join Rule specifies the [Allowed Domain](#allowed-domain), the default [Project Role](#project-role) to assign, and whether the rule is active. Auto-join still respects [Member Limit](#member-limit) — if the project is at capacity, auto-join is blocked and the user is notified.

**Code mapping:**

- Python: `AutoJoinRule` entity in `project/domain/auto_join_rule.py`
 `AutoJoinRule` class in `packages/project/src/domain/auto-join-rule.ts`

**Related terms:** [Allowed Domain](#allowed-domain), [Membership](#membership), [Project Role](#project-role), [Member Limit](#member-limit)

---

### Allowed Domain

**Definition:** An email domain pattern (e.g., `acme.com`, `*.acme.com`) that qualifies a user for automatic project membership through an [Auto-Join Rule](#auto-join-rule).

**Context:** Domains are stored as lowercase strings. Wildcard patterns (`*.acme.com`) match subdomains (e.g., `eng.acme.com`, `sales.acme.com`). The domain is extracted from the user's verified email address in the Auth context — unverified emails do not trigger auto-join. Multiple Allowed Domains can be configured per [Auto-Join Rule](#auto-join-rule), and multiple rules can coexist per [Project](#project) (e.g., different domains mapped to different roles).

**Code mapping:**

- Python: `AllowedDomain` value object in `project/domain/allowed_domain.py`
 `AllowedDomain` branded type in `packages/project/src/domain/allowed-domain.ts`

**Related terms:** [Auto-Join Rule](#auto-join-rule), [Membership](#membership)

---

### Invitation Event

**Definition:** A domain event emitted when the state of an [Invitation](#invitation) or [Invite Link](#invite-link) changes. A specialized subset of [Project Events](#project-event).

**Context:** Examples: `InvitationSent` (personal invitation created and dispatched), `InvitationAccepted`, `InvitationDeclined`, `InvitationExpired`, `InvitationRevoked`, `InviteLinkCreated`, `InviteLinkDeactivated`, `AutoJoinRuleCreated`, `AutoJoinTriggered`. Each event carries `ProjectId`, the actor's `IdentityId`, and event-specific payload (target email, role, link token, domain pattern).

**Code mapping:**

- Python: `InvitationEvent` subclasses of `ProjectEvent` in `project/domain/events.py` (`InvitationSentEvent`, `InvitationAcceptedEvent`, etc.)
 Invitation-specific types within `ProjectEvent` union in `packages/project/src/domain/events.ts`

**Related terms:** [Invitation](#invitation), [Invitation Status](#invitation-status), [Invite Link](#invite-link), [Auto-Join Rule](#auto-join-rule), [Project Event](#project-event)

---

## 4. Project Lifecycle

### Draft State

**Definition:** The initial [Project Status](#project-status) assigned when a [Project](#project) is first created. In Draft, the project is being set up — the [Owner](#owner) can configure [Project Settings](#project-settings), invite members, and prepare content, but the project is not yet "live."

**Context:** Draft is an optional incubation phase. The Owner can take as long as needed to set up the project before activating it. In Draft state: invitations can be sent and accepted, members can join, but certain features may be restricted (e.g., external integrations, webhooks, public visibility). The project does not appear in public or internal listings while in Draft. Transition: `Draft` → `Active` (requires at least the Owner as a member and a project name).

**Code mapping:**

- Python: `ProjectStatus.DRAFT` enum member in `project/domain/project_status.py`
 `"draft"` literal in `ProjectStatus` union type

**Related terms:** [Project Status](#project-status), [Active State](#active-state), [Project Transition](#project-transition)

---

### Active State

**Definition:** The primary operational [Project Status](#project-status). In Active state, the project is fully functional — all members can collaborate, content is editable, invitations are processed, and the project appears in listings according to its [Project Visibility](#project-visibility).

**Context:** Active is the state where a project spends most of its lifetime. All project features are available. Transitions: `Active` → `Completed` (Owner marks work as finished) or `Active` → `Archived` (Owner decides to shelve the project without completing it).

**Code mapping:**

- Python: `ProjectStatus.ACTIVE` enum member in `project/domain/project_status.py`
 `"active"` literal in `ProjectStatus` union type

**Related terms:** [Project Status](#project-status), [Draft State](#draft-state), [Completed State](#completed-state), [Archived State](#archived-state), [Project Transition](#project-transition)

---

### Completed State

**Definition:** A [Project Status](#project-status) indicating that the project's work has been finished. The project becomes read-only for content, but members retain access for reference and review.

**Context:** Completed projects serve as archives of finished work. Members can view all content but cannot create or edit. The [Owner](#owner) can still manage members and settings (e.g., add a new Viewer for a retrospective). Completed projects remain in listings marked with a visual indicator. Transitions: `Completed` → `Active` (reopen — Owner decides more work is needed) or `Completed` → `Archived` (final archival).

**Code mapping:**

- Python: `ProjectStatus.COMPLETED` enum member in `project/domain/project_status.py`
 `"completed"` literal in `ProjectStatus` union type

**Related terms:** [Project Status](#project-status), [Active State](#active-state), [Archived State](#archived-state), [Project Transition](#project-transition)

---

### Archived State

**Definition:** The terminal [Project Status](#project-status). An Archived project is frozen — all content is read-only, no new members can join, invitations are automatically revoked, and the project is hidden from default listings.

**Context:** Archival is for projects that are no longer relevant but must be preserved (compliance, historical reference). Archived projects do not consume active [Seats](#seat) for billing purposes. The project data is retained but may be subject to different storage policies (cold storage, reduced SLA). Transition: `Archived` → `Active` (unarchive — requires Owner action and may require billing reactivation if seat limits apply).

**Code mapping:**

- Python: `ProjectStatus.ARCHIVED` enum member in `project/domain/project_status.py`
 `"archived"` literal in `ProjectStatus` union type

**Related terms:** [Project Status](#project-status), [Completed State](#completed-state), [Seat](#seat), [Project Transition](#project-transition), [Lifecycle Policy](#lifecycle-policy)

---

### Project Transition

**Definition:** A validated state change of a [Project](#project) from one [Project Status](#project-status) to another. Each transition enforces preconditions, emits a [Project Event](#project-event), and may trigger side effects (e.g., revoking invitations on archival).

**Context:** Allowed transitions form a directed graph:
- `Draft` → `Active`
- `Active` → `Completed`
- `Active` → `Archived`
- `Completed` → `Active` (reopen)
- `Completed` → `Archived`
- `Archived` → `Active` (unarchive)

Each transition has preconditions defined by the [Lifecycle Policy](#lifecycle-policy). For example, `Draft → Active` requires a project name and at least one member; `Archived → Active` may require the Owner to confirm billing implications. Invalid transitions (e.g., `Draft → Completed`) are rejected by the domain model.

**Code mapping:**

- Python: `ProjectTransition` domain service in `project/domain/project_transition.py`
 `ProjectTransition` domain service in `packages/project/src/domain/project-transition.ts`

**Related terms:** [Project Status](#project-status), [Lifecycle Policy](#lifecycle-policy), [Project Event](#project-event)

---

### Lifecycle Policy

**Definition:** A set of rules that govern which [Project Transitions](#project-transition) are allowed, who can initiate them, and what preconditions must be met. The Lifecycle Policy is the central authority for project state machine validation.

**Context:** The Lifecycle Policy encodes business rules such as: "Only the Owner can archive a project," "A project cannot be completed if it has no content," "Unarchiving requires re-confirmation if the project has been archived for more than 90 days." The policy is enforced by the domain model, not by the application or presentation layer. Platform-wide defaults can be overridden per-project through [Project Settings](#project-settings) if the business allows it.

**Code mapping:**

- Python: `LifecyclePolicy` domain service in `project/domain/lifecycle_policy.py`
 `LifecyclePolicy` domain service in `packages/project/src/domain/lifecycle-policy.ts`

**Related terms:** [Project Transition](#project-transition), [Project Status](#project-status), [Owner](#owner), [Project Settings](#project-settings)

---

## 5. Permissions & Access Control

### Project Permission

**Definition:** A granular right that authorizes a specific action within a [Project](#project). Examples: `view_content`, `edit_content`, `manage_members`, `manage_settings`, `manage_invitations`, `delete_project`, `transfer_ownership`.

**Context:** Project Permissions are the finest-grained access control unit in this bounded context. They are NOT assigned directly to [Members](#member) — instead, they are mapped to [Project Roles](#project-role) through the [Permission Matrix](#permission-matrix). This indirection ensures consistency: all Owners have the same permissions, all Viewers have the same permissions. The project context defines and enforces its own permissions independently from the Auth context's system-wide [Permissions](./auth.md#permission).

**Code mapping:**

- Python: `ProjectPermission` enum in `project/domain/project_permission.py`
 `ProjectPermission` union type in `packages/project/src/domain/project-permission.ts`

**Related terms:** [Permission Matrix](#permission-matrix), [Project Role](#project-role), [Access Check](#access-check)

**Not to be confused with:** [Permission](./auth.md#permission) in the Auth context — Auth manages system-wide permissions (e.g., "can create projects," "can access admin panel"), while Project Permissions are scoped to actions within a single project.

---

### Permission Matrix

**Definition:** A mapping that defines which [Project Permissions](#project-permission) each [Project Role](#project-role) grants. The Permission Matrix is the single source of truth for role-to-permission resolution.

**Context:** Typical matrix:

| Permission | Owner | Member | Viewer |
|---|---|---|---|
| `view_content` | Yes | Yes | Yes |
| `edit_content` | Yes | Yes | No |
| `manage_members` | Yes | No | No |
| `manage_invitations` | Yes | No | No |
| `manage_settings` | Yes | No | No |
| `delete_project` | Yes | No | No |
| `transfer_ownership` | Yes | No | No |

The matrix is defined in the domain layer and is immutable at runtime (no custom role creation in this version). Future extension to custom roles would replace this static matrix with a configurable one, following the [Open/Closed Principle](../AGENTS.md#32-o--openclosed-principle-ocp).

**Code mapping:**

- Python: `PermissionMatrix` mapping in `project/domain/permission_matrix.py`
 `PermissionMatrix` readonly record in `packages/project/src/domain/permission-matrix.ts`

**Related terms:** [Project Permission](#project-permission), [Project Role](#project-role), [Access Check](#access-check)

---

### Access Check

**Definition:** A domain operation that determines whether a specific [Member](#member) is authorized to perform a specific action within a [Project](#project). The Access Check resolves the member's [Project Role](#project-role) through the [Permission Matrix](#permission-matrix) and returns an allow/deny decision.

**Context:** Access Checks are performed at the application layer (in Use Cases) before executing any state-changing operation. The check takes three inputs: `ProjectId`, `IdentityId`, and the required `ProjectPermission`. It verifies: (1) the user has an active [Membership](#membership) in the project, (2) the membership's role includes the required permission. Access Checks are a pure domain concern — they do not involve HTTP, tokens, or sessions (those are handled by the Auth context).

**Code mapping:**

- Python: `AccessChecker` domain service in `project/domain/access_checker.py`
 `AccessChecker` domain service in `packages/project/src/domain/access-checker.ts`

**Related terms:** [Project Permission](#project-permission), [Permission Matrix](#permission-matrix), [Membership](#membership), [Project Role](#project-role)

---

### Project-Scoped Token

**Definition:** An API access token that grants permissions limited to a single [Project](#project). Used for programmatic access (CI/CD pipelines, integrations, bots) where a full user session is unnecessary or undesirable.

**Context:** Project-Scoped Tokens are created by the [Owner](#owner) (or members with `manage_settings` permission) and carry a specific set of [Project Permissions](#project-permission) — they never exceed the permissions of the creating member's [Project Role](#project-role). Tokens have a configurable TTL and can be revoked at any time. They are distinct from [Access Tokens](./auth.md#access-token) (which authenticate a user across the platform) and from [Invitation Tokens](#invitation-token) (which authorize joining a project).

**Code mapping:**

- Python: `ProjectScopedToken` entity in `project/domain/project_scoped_token.py`
 `ProjectScopedToken` class in `packages/project/src/domain/project-scoped-token.ts`

**Related terms:** [Project Permission](#project-permission), [Owner](#owner), [Access Check](#access-check)

**Not to be confused with:** [Permission](./auth.md#permission) in the Auth context (grants system-wide access scoped by Auth roles), [Invitation Token](#invitation-token) (single-use token for joining a project), or [Referral Code](./partnership.md#referral-code) in Partnership (identifies a partner for referral tracking).

---

### Transfer Ownership

**Definition:** A domain operation that reassigns the [Owner](#owner) role from the current Owner to another active [Member](#member) of the [Project](#project). The previous Owner is demoted to [Member Role](#member-role).

**Context:** Ownership transfer is irreversible without a reverse transfer. Only the current Owner can initiate it (no other role has the `transfer_ownership` [Project Permission](#project-permission)). The operation requires the target Member to have an `Active` [Membership Status](#membership-status). The transfer emits an `OwnershipTransferred` [Membership Event](#membership-event) with both the old and new Owner's `IdentityId`. Use cases: founder leaving the project, organizational restructuring, or planned handover.

**Code mapping:**

- Python: `TransferOwnershipUseCase` in `project/application/transfer_ownership.py`
 `TransferOwnershipUseCase` in `packages/project/src/application/transfer-ownership.ts`

**Related terms:** [Owner](#owner), [Project Role](#project-role), [Membership Event](#membership-event), [Project Permission](#project-permission)

---

## 6. Capacity & Limits

### Member Limit

**Definition:** The maximum number of active [Members](#member) (with `Active` [Membership Status](#membership-status)) allowed in a [Project](#project) at any given time. Determined by the project's billing plan and overridable in [Project Settings](#project-settings).

**Context:** Member Limit is the bridge between this bounded context and Billing. The default limit comes from the Billing context via an Anti-Corruption Layer (see [AGENTS.md 4.3](../AGENTS.md#43-context-mapping-карта-контекстов)) — the Project context receives a `MemberLimitChanged` event when the billing plan changes, and stores the limit locally. Enforcement happens in the domain: any operation that would add a new member (invitation acceptance, invite link join, auto-join) must check the limit first. Reaching the limit emits a [Capacity Event](#capacity-event).

**Code mapping:**

- Python: `MemberLimit` value object in `project/domain/member_limit.py`
 `MemberLimit` branded type in `packages/project/src/domain/member-limit.ts`

**Related terms:** [Seat](#seat), [Project Settings](#project-settings), [Capacity Event](#capacity-event), [Member](#member)

---

### Seat

**Definition:** A unit of capacity representing one active [Membership](#membership) in a [Project](#project). Seats are the billing unit: the Billing context charges per seat, and the Project context tracks seat consumption against the [Member Limit](#member-limit).

**Context:** Seat count = number of members with `Active` [Membership Status](#membership-status). `Suspended` members do NOT consume seats (freeing capacity for replacements). `Removed` members release their seat immediately. [Archived](#archived-state) projects release all seats (members of archived projects do not count toward any billing quota). Seat usage is reported to the Billing context via [Project Events](#project-event) (`MemberJoined`, `MemberRemoved`, `ProjectArchived`).

**Code mapping:**

- Python: seat count logic in `Project` aggregate root methods (`project/domain/project.py`)
 seat count logic in `Project` class methods (`packages/project/src/domain/project.ts`)

**Related terms:** [Member Limit](#member-limit), [Membership Status](#membership-status), [Capacity Event](#capacity-event)

**Not to be confused with:** `License` or `Subscription Slot` in the Billing context — Billing defines how many seats the plan allows and charges accordingly, while the Project context enforces the limit and tracks consumption.

---

### Project Quota

**Definition:** Resource limits applied to a [Project](#project) beyond member capacity: storage space (MB/GB), maximum number of items (tasks, documents, boards), API request rate limits, or any other measurable resource.

**Context:** Like [Member Limit](#member-limit), quotas originate from the Billing context and are stored locally in the Project context via an ACL. Quota enforcement is the Project context's responsibility. When a quota is approached (e.g., 90% storage used), a warning [Capacity Event](#capacity-event) is emitted. When exceeded, the relevant write operation is blocked. Quotas are checked at the application layer before executing create/upload operations.

**Code mapping:**

- Python: `ProjectQuota` dataclass in `project/domain/project_quota.py`
 `ProjectQuota` interface in `packages/project/src/domain/project-quota.ts`

**Related terms:** [Member Limit](#member-limit), [Seat](#seat), [Capacity Event](#capacity-event), [Project Settings](#project-settings)

---

### Capacity Event

**Definition:** A domain event emitted when a [Project](#project) approaches or reaches a resource limit. A specialized subset of [Project Events](#project-event).

**Context:** Examples: `SeatLimitReached` (all seats occupied, no more members can join), `SeatLimitApproaching` (configurable threshold, e.g., 90%), `QuotaExceeded` (storage, item count, or other resource exceeded), `QuotaWarning` (approaching threshold). Capacity Events are consumed by: (1) the Presentation layer to display warnings, (2) the Billing context to suggest plan upgrades, (3) the Monitoring context for capacity planning. Each event carries `ProjectId`, the resource type, the current usage, and the limit.

**Code mapping:**

- Python: `CapacityEvent` subclasses of `ProjectEvent` in `project/domain/events.py` (`SeatLimitReachedEvent`, `QuotaExceededEvent`, etc.)
 Capacity-specific types within `ProjectEvent` union in `packages/project/src/domain/events.ts`

**Related terms:** [Member Limit](#member-limit), [Seat](#seat), [Project Quota](#project-quota), [Project Event](#project-event)

---

## Cross-Context Boundary Notes

The Projects & Members bounded context interacts with other contexts through explicit contracts. The following table clarifies term boundaries:

| Project Context Term | Other Context | Their Term | Relationship |
|---|---|---|---|
| `Member` | Auth | [`AuthUser`](./auth.md#authuser) | Linked via `IdentityId`. Project owns membership and project-scoped role; Auth owns credentials, sessions, and system-wide roles. |
| `Project Permission` | Auth | [`Permission`](./auth.md#permission) | Auth provides system-wide RBAC (e.g., "can create projects"). Project context defines and enforces project-scoped permissions (e.g., `edit_content`, `manage_members`). They are complementary, not overlapping. |
| `Invitation` / `Auto-Join Rule` | Auth | [`Account`](./auth.md#account) | An Invitation may target an email without an existing Account. Auth handles account creation during the invitation acceptance flow. Auto-Join Rules rely on Auth's verified email address. |
| `Project-Scoped Token` | Auth | [`Access Token`](./auth.md#access-token), [`Session`](./auth.md#session) | Auth validates the token's signature and identity. Project context validates the token's project-scoped permissions. |
| `Member Limit` / `Seat` | Billing | `Subscription`, `Plan` | Billing defines how many seats the plan allows and charges per seat. Project context enforces the limit and reports seat consumption via events. |
| `Project Quota` | Billing | `Plan Limits`, `Usage` | Billing defines resource quotas per plan. Project context stores them locally (via ACL) and enforces them. |
| `Project` | Partnership | [`Referral`](./partnership.md#referral), [`Qualifying Event`](./partnership.md#qualifying-event) | Creating a project may count as a Qualifying Event in the Partnership context. Partnership subscribes to `ProjectCreated` events and evaluates them for commission attribution. |
| `Project Event` | Monitoring | `Alert`, `Metric` | Project emits lifecycle and capacity events. Monitoring context consumes them for dashboards, alerting, and analytics. |

**Integration rules:**

- Other contexts MUST NOT import Project domain models directly. Use events or API contracts.
- The Project context MUST NOT query the Billing database directly. Plan limits (member limit, quotas) arrive via domain events (`PlanChanged`, `QuotaUpdated`) and are stored locally through an Anti-Corruption Layer (see [AGENTS.md 4.3](../AGENTS.md#43-context-mapping-карта-контекстов)).
- The Project context MUST NOT manage authentication or credentials. When verifying a user's identity during invitation acceptance or invite link usage, the Project context delegates to the Auth context via its Driving Port.
- Auth context MUST NOT contain project-specific authorization logic. The rule "does this user have `edit_content` permission in Project X?" is evaluated by the Project context, not Auth. Auth only answers "is this user authenticated?" and "does this user have the system-wide permission to access projects?"
- When a new member joins via [Auto-Join Rule](#auto-join-rule), the Project context verifies the email domain against Auth's verified email — never against unverified or self-reported email data.
- [Seat](#seat) consumption changes (`MemberJoined`, `MemberRemoved`, `ProjectArchived`) are published as [Project Events](#project-event) for the Billing context to update usage records and trigger billing adjustments.
