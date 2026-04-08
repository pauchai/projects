# Invitation System Architecture Plan

## Executive Summary

### Current State

- Open registration system allowing anyone to register
- OAuth integration (Google, Telegram) also creates accounts freely
- No mechanism to control user quality or track who invited whom

### Goal

Create an invitation-only system to control user acquisition while
maintaining flexibility for future growth features (referrals, rewards,
analytics).

### Key Decisions Made

1. **Architectural Approach**: Separate "Member Invitation" bounded context
   (instead of extending Auth or Project Collaboration).
2. **Interim Solution**: Simple registration gate + admin bootstrap while
   requirements mature.
3. **Strategic Wait**: Full implementation deferred until business model and
   user flow are clearly defined.

### Why Invitation-Only?

- **Quality Control**: Only invited people join, raising community quality.
- **Network Effect**: People invite those they know and trust.
- **Organic Growth**: Controlled but natural community growth.
- **Foundation for Referrals**: Invitation graph enables future reward systems.

---

## Architecture Analysis

### Bounded Context Options Evaluated

#### Option A: Extend Auth Context

- **Pros**: Reuse existing infrastructure, simpler integration.
- **Cons**: Mixed responsibilities (identity vs acquisition), future constraints.
- **Verdict**: Rejected. Auth should focus on identity verification only.

#### Option B: Extend Project Collaboration Context

- **Pros**: Simpler than a separate context, invitations naturally tied to projects.
- **Cons**: Mixed user-acquisition concerns with project management.
- **Verdict**: Backup option if a separate context proves too complex early on.

#### Option C: Separate "Member Invitation" Context (RECOMMENDED)

- **Pros**: Clear domain separation, independent evolution, business alignment.
- **Cons**: Additional complexity, eventual consistency, operational overhead.
- **Verdict**: Preferred. User acquisition is strategically important and deserves
  its own bounded context.

### Rationale for Separate Context

1. **Single Responsibility (SRP at architecture level)**:
   - Auth: "Who is this user and are their credentials valid?"
   - Project Collaboration: "How do we manage projects and members?"
   - Member Invitation: "How do people discover the platform and join?"

2. **Ubiquitous Language**: Three distinct vocabularies:
   - Auth: authenticate, credential, provider, session, token
   - Invitation: invite, accept, decline, expire, revoke, referral, conversion
   - Projects: project, member, role, application, collaboration

3. **Strategic Perspective**: Invitations evolve toward growth/marketing:
   - Referral programs and gamification
   - Conversion analytics and A/B testing
   - Campaign management
   - Integration with marketing tools

### Context Map

```
+-----------------+    Customer-Supplier    +------------------+
|      Auth       | ---------------------->| Member Invitation |
|                 |   (identity verify)     |                  |
+-----------------+                        +--------+---------+
                                                    |
                                                    | Published Language
                                                    | (domain events)
                                                    v
                                           +------------------+
                                           |    Project       |
                                           |  Collaboration   |
                                           +------------------+
```

**Integration contracts**:

- **Auth -> Invitations**: Customer-Supplier. Auth provides identity
  verification; Invitation context consumes it through an ACL.
- **Invitations -> Project Collaboration**: Published Language. Invitation
  events (e.g. `InvitationAccepted`) trigger membership creation.

---

## Domain Models

### Core Entity: Invitation

```python
@dataclass
class Invitation:
    """Personal invitation to join the platform."""

    invitation_id: str
    inviter_id: str            # Who created the invitation
    invitee_email: str         # Target email address
    invitation_token: str      # Cryptographically secure token
    status: InvitationStatus   # pending / accepted / expired / revoked
    expires_at: datetime
    created_at: datetime
    accepted_at: datetime | None = None

    # Future extension points (not implemented in MVP):
    # project_id: str | None     -- project-specific invitations
    # referral_code: str | None  -- public referral links
    # metadata: dict             -- extensible data for rewards/analytics
```

### Value Objects

```python
class InvitationStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"

@dataclass(frozen=True)
class InvitationToken:
    """Cryptographically secure token for invitation acceptance."""
    value: str

    def __post_init__(self) -> None:
        if len(self.value) < 32:
            raise ValueError("Token must be at least 32 characters")

@dataclass(frozen=True)
class InviteeEmail:
    """Validated, normalized email address for the invitee."""
    value: str

    def __post_init__(self) -> None:
        email = self.value.strip().lower()
        if not email or "@" not in email:
            raise ValueError("Invalid email format")
        object.__setattr__(self, "value", email)
```

### Domain Events

```python
@dataclass
class InvitationSent:
    invitation_id: str
    invitee_email: str
    inviter_id: str
    expires_at: datetime

@dataclass
class InvitationAccepted:
    invitation_id: str
    new_member_id: str   # Created user ID
    inviter_id: str      # Who invited them
    joined_via: str      # "personal_invitation" | "referral_link" (future)
```

### Ports

```python
class InvitationRepository(Protocol):
    def save(self, invitation: Invitation) -> None: ...
    def find_by_id(self, invitation_id: str) -> Invitation | None: ...
    def find_by_token(self, token_hash: str) -> Invitation | None: ...
    def find_by_invitee_email(self, email: str) -> list[Invitation]: ...
    def find_all_pending(self) -> list[Invitation]: ...

class AuthIdentityGateway(Protocol):
    """Anti-Corruption Layer for Auth context integration."""
    def verify_email_registered(self, email: str) -> bool: ...
    def ensure_user_exists(self, email: str) -> str: ...  # returns user_id
    def is_admin(self, user_id: str) -> bool: ...
```

### Database Schema

```sql
CREATE TABLE member_invitations (
    invitation_id  VARCHAR(255) PRIMARY KEY,
    inviter_id     VARCHAR(255) NOT NULL,       -- references auth_users
    invitee_email  VARCHAR(320) NOT NULL,
    token_hash     VARCHAR(64)  NOT NULL,        -- SHA-256 of the token
    status         VARCHAR(20)  NOT NULL DEFAULT 'pending',
    expires_at     TIMESTAMPTZ  NOT NULL,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    accepted_at    TIMESTAMPTZ
);

CREATE UNIQUE INDEX uq_pending_email
    ON member_invitations (invitee_email)
    WHERE status = 'pending';

CREATE INDEX idx_invitations_token_hash ON member_invitations (token_hash);
CREATE INDEX idx_invitations_status     ON member_invitations (status);
CREATE INDEX idx_invitations_inviter    ON member_invitations (inviter_id);
```

### Proposed Directory Structure

```
src/member_invitation/
|-- domain/
|   |-- invitation.py            # Invitation aggregate
|   |-- invitation_status.py     # Status enum
|   `-- ports.py                 # Repository + Gateway protocols
|-- application/
|   |-- send_invitation.py       # Use case: create + send
|   |-- accept_invitation.py     # Use case: validate + create user
|   |-- revoke_invitation.py     # Use case: cancel pending
|   `-- list_invitations.py      # Use case: admin view
|-- infrastructure/
|   |-- sqlalchemy_invitation_repository.py
|   |-- auth_identity_gateway.py  # ACL adapter
|   |-- database.py               # Engine and table definitions
|   `-- orm.py                     # Imperative mapping
`-- api/
    |-- app.py                    # Router factory
    |-- dependencies.py           # FastAPI DI
    |-- schemas.py                # Request/response models
    `-- routes/
        `-- invitations.py        # REST endpoints
```

---

## Implementation Phases

### Phase 0: Interim Solution (immediate)

**Goal**: Close open registration now while the full design matures.

- Add environment flag `REGISTRATION_OPEN` (default `false`).
- If `false`, `RegisterUserUseCase` rejects new registrations.
- Add `POST /admin/bootstrap` endpoint:
  - Protected by `BOOTSTRAP_SECRET_KEY` env var.
  - Creates the first admin user.
  - Auto-disables after first admin exists.
- Admin can create users directly through an admin endpoint.

### Phase 1: Domain Foundation

**Goal**: Establish the Member Invitation bounded context.

- Create `src/member_invitation/` package with domain models.
- Implement `InvitationRepository` port and SQLAlchemy adapter.
- Add database table via `create_tables`.
- Full unit test coverage for domain logic (TDD).

### Phase 2: Integration Layer

**Goal**: Wire contexts together safely.

- Implement `AuthIdentityGateway` (ACL for Auth context).
- Publish `InvitationAccepted` events via shared event bus.
- Integration tests for cross-context communication.
- Error handling for distributed operations.

### Phase 3: Core Use Cases

**Goal**: Essential invitation workflow.

- `SendInvitationUseCase`: admin creates invitation, generates token.
- `AcceptInvitationUseCase`: validates token, triggers user creation.
- `RevokeInvitationUseCase`: cancels pending invitations.
- `ListInvitationsUseCase`: admin queries invitations.
- Security: token hashing, expiration checks, single-use enforcement.

### Phase 4: API and Registration Integration

**Goal**: REST endpoints and modified registration flow.

- `POST   /invitations`          -- create invitation (admin)
- `GET    /invitations`          -- list invitations (admin)
- `DELETE /invitations/{id}`     -- revoke invitation (admin)
- `GET    /invitations/validate` -- check token validity (public)
- Modify `POST /auth/register` to require `invitation_token`.
- Modify OAuth callback flows to validate invitation on new user creation.

### Phase 5: Email and UX

**Goal**: Complete user experience.

- Email service for sending invitation links.
- HTML email templates with branding.
- Frontend UI for invitation management (admin panel).
- "Registration by invitation only" landing page for uninvited visitors.

---

## Future Extensions (Deferred)

These extensions are **not part of the MVP** but the architecture is designed
to support them with minimal refactoring.

### Referral System

```python
class ReferralCode:
    """Public, reusable code for viral growth."""
    code: str               # Short, memorable code
    owner_id: str
    is_active: bool
    usage_limit: int | None = None

class ReferralReward:
    """Incentive for successful referrals."""
    referrer_bonus: int
    referee_bonus: int
    reward_type: RewardType  # credits, premium, access
```

### Project-Specific Invitations

Invitations scoped to a particular project, granting membership upon
acceptance rather than (or in addition to) platform-level access.

### Mentor Invitations

Special invitation type where mentors invite mentees with extended
privileges or onboarding flows.

### Analytics and Campaign Management

- Conversion tracking and funnel analysis.
- A/B testing for invitation templates.
- Bulk invitation campaigns.
- Integration with marketing tools.

---

## Open Research Questions

### Business Model

1. **Invitation scope**: Platform-wide vs project-specific?
2. **Permission model**: Who can invite? Any user, admins only, or
   reputation-based?
3. **Limitation strategy**: Rate limits, quotas, approval workflows?
4. **Incentive structure**: What rewards for successful invitations?

### User Experience

5. **Post-signup flow**: Direct to a project or platform exploration?
6. **Visibility model**: Can uninvited visitors browse public projects?
7. **Mentor integration**: Special invitation privileges for mentors?
8. **Request flow**: "Request an invitation" form for prospective users?

### Technical

9. **Consistency model**: Eventual consistency acceptable for acceptance?
10. **Security**: Additional verification beyond email confirmation?
11. **Analytics**: Which metrics are critical for growth measurement?
12. **Complexity trade-off**: Separate context worth it from day one?

---

## Next Steps

### Immediate Actions

1. Deploy interim registration gate (Phase 0).
2. Conduct user research on discovery and onboarding preferences.
3. Competitive analysis (Discord, Slack, GitHub invitation models).
4. Clarify business model and user-acquisition strategy.

### Decision Points

- **Architecture confirmation**: Finalize separate context vs extension
  once requirements are clear.
- **Implementation priority**: Align with business timeline and strategic
  importance.
- **Integration approach**: Event-driven vs direct calls based on
  consistency requirements.

### Success Metrics

- **Quality**: Higher engagement from invited users vs open registration.
- **Growth control**: Sustainable acquisition rate matching platform capacity.
- **Viral coefficient**: Average invitations sent per active user.
- **Conversion**: Invitation acceptance rate and long-term retention.

---

**Status**: Architecture plan pending business requirements clarification.
**Next review**: After user research and requirements gathering phase.
