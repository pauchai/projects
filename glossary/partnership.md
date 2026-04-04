# Partnership & Referral Program — Ubiquitous Language Glossary

This glossary defines the authoritative vocabulary for the **Partnership & Referral Program** bounded context. All code, documentation, API contracts, and team communication within this context MUST use these terms consistently.

**Bounded Context scope:** Partner lifecycle management, referral invitations, multi-level referral chains, commission calculation and accrual, payout processing, fraud prevention, and performance analytics.

**Multi-level model:** This context supports a multi-level referral structure where partners can recruit sub-partners, forming a tree of referral relationships with configurable depth limits and tier-based commission rates.

**Code mapping convention:**

- Python: `partnership/domain/` for domain models, `partnership/application/` for use cases, `partnership/infrastructure/` for adapters
 `packages/partnership/src/domain/`, `packages/partnership/src/application/`, `packages/partnership/src/infrastructure/`

**Cross-context dependency:** This context references identities from the [Auth bounded context](./auth.md). A Partner is always linked to an [AuthUser](./auth.md#authuser) via `IdentityId`, but the two models are separate — Auth owns credentials and sessions, Partnership owns referral relationships and commissions.

---

## 1. Partner Identity

### Partner

**Definition:** A registered participant in the referral program who can invite new users and earn commissions from their activity. A Partner is the root entity of this bounded context.

**Context:** Every Partner is linked to an [AuthUser](./auth.md#authuser) via `IdentityId`, but `Partner` is a separate domain model — it does not inherit from or extend `AuthUser`. A user becomes a Partner by enrolling in the program and accepting the [Partner Agreement](#partner-agreement). A Partner has a unique [Referral Code](#referral-code), a [Partner Tier](#partner-tier), a [Partner Balance](#partner-balance), and a position in the [Referral Chain](#referral-chain).

**Code mapping:**

- Python: `Partner` aggregate root in `partnership/domain/partner.py`
 `Partner` class in `packages/partnership/src/domain/partner.ts`

**Related terms:** [Partner Tier](#partner-tier), [Partner Status](#partner-status), [Referral Code](#referral-code), [Partner Balance](#partner-balance), [Referral Chain](#referral-chain)

**Not to be confused with:** [AuthUser](./auth.md#authuser) in the Auth context (owns credentials, sessions, roles) or `BillingCustomer` in the Billing context (owns payment methods, subscriptions). A single person may be all three, but each context maintains its own model.

---

### Partner Tier

**Definition:** A classification level assigned to a [Partner](#partner) that determines their [Commission Rate](#commission-rate), access to promotional materials, and program benefits. Tiers are earned through performance or granted manually.

**Context:** Typical tier hierarchy: `Bronze` (default on enrollment) → `Silver` → `Gold` → `Platinum`. Each tier defines a set of [Commission Tiers](#commission-tier) (per-depth rates) and may unlock additional features (custom landing pages, dedicated support, early access). Tier promotion is triggered by reaching performance thresholds (e.g., 50 confirmed referrals, $5,000 in total commissions). Demotion may occur on periodic review if thresholds are no longer met.

**Code mapping:**

- Python: `PartnerTier` enum in `partnership/domain/partner_tier.py`
 `PartnerTier` union type in `packages/partnership/src/domain/partner-tier.ts`

**Related terms:** [Partner](#partner), [Commission Rate](#commission-rate), [Commission Tier](#commission-tier)

---

### Partner Profile

**Definition:** Public-facing metadata associated with a [Partner](#partner): display name, avatar, bio, website URL, social media links. Profile data is used on co-branded landing pages and partner directories.

**Context:** Partner Profile is separate from [AuthUser Profile](./auth.md#profile) — Auth owns the identity profile (locale, timezone), Partnership owns the promotional profile (bio, website, social links). Changes to Partner Profile do not affect authentication or authorization.

**Code mapping:**

- Python: `PartnerProfile` dataclass in `partnership/domain/partner_profile.py`
 `PartnerProfile` type in `packages/partnership/src/domain/partner-profile.ts`

**Related terms:** [Partner](#partner)

**Not to be confused with:** [Profile](./auth.md#profile) in the Auth context — that covers identity metadata (locale, timezone), not promotional information.

---

### Partner Agreement

**Definition:** A versioned set of terms and conditions that a user must accept to become a [Partner](#partner). The agreement defines commission structures, payout terms, prohibited activities, and grounds for termination.

**Context:** Every Partner enrollment records which version of the agreement was accepted and when. When the agreement is updated, existing partners may need to re-accept the new version before they can withdraw commissions. The agreement is a legal document — changes are tracked with full version history.

**Code mapping:**

- Python: `PartnerAgreement` dataclass in `partnership/domain/partner_agreement.py`, `AgreementAcceptance` value object
 `PartnerAgreement` type in `packages/partnership/src/domain/partner-agreement.ts`, `AgreementAcceptance` value object

**Related terms:** [Partner](#partner), [Partner Status](#partner-status)

---

### Partner Status

**Definition:** The current lifecycle state of a [Partner](#partner) within the program. Determines whether the partner can generate referrals, earn commissions, and request payouts.

**Context:** Status transitions:

- `Pending` — enrolled but awaiting approval or agreement acceptance. Cannot generate referrals.
- `Active` — fully operational. Can invite users, earn commissions, request payouts.
- `Suspended` — temporarily frozen due to [Fraud Review](#fraud-review) or [Compliance Hold](#compliance-hold). Existing commissions are held; new referrals are not tracked.
- `Terminated` — permanently removed from the program. All pending commissions are forfeited or clawed back. [Referral Links](#referral-link) become inactive.

**Code mapping:**

- Python: `PartnerStatus` enum in `partnership/domain/partner_status.py`
 `PartnerStatus` union type in `packages/partnership/src/domain/partner-status.ts`

**Related terms:** [Partner](#partner), [Compliance Hold](#compliance-hold), [Fraud Review](#fraud-review), [Clawback](#clawback)

---

## 2. Invitations & Referral Links

### Invitation

**Definition:** A direct, personalized request from a [Partner](#partner) to a specific individual to join the project. An Invitation is sent to a known recipient (via email, messaging, etc.) and carries a unique [Invite Token](#invite-token).

**Context:** Invitations are distinct from [Referral Links](#referral-link): an Invitation targets a specific person, while a Referral Link is a broadcast URL shared publicly. When the recipient accepts an Invitation, a [Referral](#referral) is created linking them to the inviting Partner. Invitations have an expiry date and can be revoked by the Partner.

**Code mapping:**

- Python: `Invitation` entity in `partnership/domain/invitation.py`
 `Invitation` class in `packages/partnership/src/domain/invitation.ts`

**Related terms:** [Invite Token](#invite-token), [Invitation Status](#invitation-status), [Referral](#referral), [Referral Link](#referral-link)

**Not to be confused with:** [Referral Link](#referral-link) — Invitations are one-to-one and personalized; Referral Links are one-to-many and anonymous.

---

### Referral Code

**Definition:** A unique, human-readable identifier assigned to each [Partner](#partner) upon enrollment. Used to attribute new users to the partner who referred them. Typically a short alphanumeric string (e.g., `PARTNER-ABC123` or `john-doe`).

**Context:** The Referral Code is embedded in [Referral Links](#referral-link) and can be entered manually during registration. A Partner has exactly one active Referral Code at a time, though historical codes may be retained for attribution of in-flight referrals. Codes are case-insensitive and URL-safe.

**Code mapping:**

- Python: `ReferralCode` value object in `partnership/domain/referral_code.py`
 `ReferralCode` branded type in `packages/partnership/src/domain/referral-code.ts`

**Related terms:** [Partner](#partner), [Referral Link](#referral-link), [Attribution](#attribution)

---

### Referral Link

**Definition:** A trackable URL containing a [Referral Code](#referral-code) or tracking parameters that attributes visitors to a specific [Partner](#partner). Shared publicly via social media, blogs, email campaigns, etc.

**Context:** When a user clicks a Referral Link, the system records a [Click](#click) and stores an attribution cookie (see [Attribution Window](#attribution-window)). If the user subsequently registers or performs a [Qualifying Event](#qualifying-event), the [Attribution](#attribution) process links them to the Partner. Referral Links become inactive when the Partner's [Status](#partner-status) is `Suspended` or `Terminated`.

**Code mapping:**

- Python: `ReferralLink` value object in `partnership/domain/referral_link.py`
 `ReferralLink` value object in `packages/partnership/src/domain/referral-link.ts`

**Related terms:** [Referral Code](#referral-code), [Click](#click), [Attribution](#attribution), [Landing Page Attribution](#landing-page-attribution)

**Not to be confused with:** [Invitation](#invitation) — Referral Links are broadcast and anonymous; Invitations are directed to a specific person.

---

### Invite Token

**Definition:** A single-use, time-limited cryptographic token embedded in an [Invitation](#invitation) URL. Proves that the recipient was specifically invited by a [Partner](#partner) and guarantees attribution regardless of cookies or other tracking mechanisms.

**Context:** Invite Tokens are more reliable than cookie-based [Attribution](#attribution) because they survive browser changes and cookie clearing. Each token is bound to a specific recipient email (optional), a specific Partner, and an expiry timestamp. Tokens are invalidated after first use or expiry. Token validation creates a [Referral](#referral) and transitions the [Invitation Status](#invitation-status) to `Accepted`.

**Code mapping:**

- Python: `InviteToken` value object in `partnership/domain/invite_token.py`
 `InviteToken` branded type in `packages/partnership/src/domain/invite-token.ts`

**Related terms:** [Invitation](#invitation), [Invitation Status](#invitation-status), [Attribution](#attribution)

**Not to be confused with:** [Access Token](./auth.md#access-token) or [Refresh Token](./auth.md#refresh-token) in the Auth context — those are authentication tokens. Invite Tokens serve a purely referral-attribution purpose.

---

### Landing Page Attribution

**Definition:** The process of recording which [Referral Link](#referral-link) brought a visitor to the project's landing page, before the visitor has registered or identified themselves.

**Context:** When a visitor arrives via a Referral Link, the system stores the [Referral Code](#referral-code) in a first-party cookie and records a [Click](#click) event. This pre-registration attribution survives page navigation and return visits within the [Attribution Window](#attribution-window). If the visitor later registers, the stored attribution data is used to create the [Referral](#referral).

**Code mapping:**

- Python: `LandingPageAttributionService` in `partnership/application/landing_page_attribution_service.py`
 `LandingPageAttributionService` in `packages/partnership/src/application/landing-page-attribution-service.ts`

**Related terms:** [Referral Link](#referral-link), [Click](#click), [Attribution](#attribution), [Attribution Window](#attribution-window)

---

### Invitation Status

**Definition:** The current lifecycle state of an [Invitation](#invitation). Tracks the progression from creation to resolution.

**Context:** Status transitions:

- `Sent` — Invitation created and delivered to the recipient.
- `Opened` — Recipient clicked the invitation link (optional tracking, not always available).
- `Accepted` — Recipient registered via the [Invite Token](#invite-token). A [Referral](#referral) is created.
- `Expired` — The [Invite Token](#invite-token) TTL elapsed without acceptance.
- `Revoked` — The [Partner](#partner) manually cancelled the invitation before acceptance.

**Code mapping:**

- Python: `InvitationStatus` enum in `partnership/domain/invitation_status.py`
 `InvitationStatus` union type in `packages/partnership/src/domain/invitation-status.ts`

**Related terms:** [Invitation](#invitation), [Invite Token](#invite-token), [Referral](#referral)

---

## 3. Referral Chain & Attribution

### Referral

**Definition:** A recorded fact that a specific [Partner](#partner) brought a specific user into the project. A Referral links the referring Partner (source) to the referred user (target) with a timestamp and [Attribution](#attribution) method.

**Context:** A Referral is created when a new user registers via a [Referral Link](#referral-link) or [Invitation](#invitation). Each user can have at most one Referral (one referring Partner). The Referral is immutable once created — it cannot be reassigned to a different Partner. The existence of a Referral is the prerequisite for [Commission](#commission) accrual.

**Code mapping:**

- Python: `Referral` entity in `partnership/domain/referral.py`
 `Referral` class in `packages/partnership/src/domain/referral.ts`

**Related terms:** [Partner](#partner), [Referral Chain](#referral-chain), [Attribution](#attribution), [Commission](#commission), [Qualifying Event](#qualifying-event)

---

### Referral Chain

**Definition:** The hierarchical tree of [Partner](#partner) → [Referral](#referral) → sub-Partner → sub-Referral relationships, spanning multiple levels. Each node in the chain is a Partner who was themselves referred by an [Upstream Partner](#upstream-partner).

**Context:** In a multi-level model, commissions propagate up the chain: when User Z pays, Partner C (direct referrer, Level 1) earns 20%, Partner B (who recruited C, Level 2) earns 10%, Partner A (who recruited B, Level 3) earns 5%. The chain has a configurable maximum [Referral Depth](#referral-depth). Cycles are prohibited — a Partner cannot appear as both upstream and downstream of the same node.

**Code mapping:**

- Python: `ReferralChain` domain service in `partnership/domain/referral_chain.py`
 `ReferralChain` domain service in `packages/partnership/src/domain/referral-chain.ts`

**Related terms:** [Referral](#referral), [Upstream Partner](#upstream-partner), [Downstream Referral](#downstream-referral), [Referral Depth](#referral-depth), [Commission Tier](#commission-tier)

---

### Upstream Partner

**Definition:** The [Partner](#partner) who is positioned above the current partner in the [Referral Chain](#referral-chain) — i.e., the one who recruited or referred the current partner into the program.

**Context:** Every Partner (except the root-level "organic" partners who joined without a referral) has exactly one Upstream Partner. Commissions from [Downstream Referrals](#downstream-referral) propagate upward through the chain, with each level receiving a rate defined by [Commission Tier](#commission-tier). The Upstream Partner relationship is immutable once established.

**Related terms:** [Referral Chain](#referral-chain), [Downstream Referral](#downstream-referral), [Referral Depth](#referral-depth)

**Not to be confused with:** The Partner who referred an end-user (that is a direct [Referral](#referral)). Upstream Partner specifically refers to the partner-to-partner recruitment relationship within the chain.

---

### Downstream Referral

**Definition:** A user or sub-[Partner](#partner) who was referred by the current partner or by anyone below them in the [Referral Chain](#referral-chain). Encompasses both direct referrals (Level 1) and indirect referrals (Level 2+).

**Context:** A Partner's downstream referrals generate [Commissions](#commission) at rates that decrease with [Referral Depth](#referral-depth). The partner dashboard shows downstream referrals grouped by level. Total downstream activity is a key input for [Partner Tier](#partner-tier) promotion decisions.

**Related terms:** [Referral Chain](#referral-chain), [Upstream Partner](#upstream-partner), [Referral Depth](#referral-depth), [Commission](#commission)

---

### Referral Depth

**Definition:** The number of edges between a [Partner](#partner) and a [Downstream Referral](#downstream-referral) in the [Referral Chain](#referral-chain). A direct referral has depth 1; a referral made by a sub-partner has depth 2; and so on.

**Context:** Referral Depth determines which [Commission Tier](#commission-tier) rate applies. The system enforces a maximum depth (e.g., 3-5 levels) beyond which no commissions are paid. This limit prevents unbounded chain growth and simplifies commission calculation. The maximum depth is configured at the program level and may vary by [Partner Tier](#partner-tier).

**Code mapping:**

- Python: `ReferralDepth` value object in `partnership/domain/referral_depth.py`, `MAX_REFERRAL_DEPTH` constant in `partnership/domain/program_config.py`
 `ReferralDepth` branded type in `packages/partnership/src/domain/referral-depth.ts`, `MAX_REFERRAL_DEPTH` constant in `packages/partnership/src/domain/program-config.ts`

**Related terms:** [Referral Chain](#referral-chain), [Commission Tier](#commission-tier), [Upstream Partner](#upstream-partner), [Downstream Referral](#downstream-referral)

---

### Attribution

**Definition:** The process of determining which [Partner](#partner) is credited with bringing a new user into the project. Attribution maps a registration or [Qualifying Event](#qualifying-event) to a specific Partner.

**Context:** Attribution can occur via multiple signals: [Invite Token](#invite-token) (highest priority — explicit, cryptographically verifiable), [Referral Code](#referral-code) entered during registration, attribution cookie from a [Referral Link](#referral-link) click, or UTM parameters. When multiple signals conflict, [Referral Conflict Resolution](#referral-conflict-resolution) rules determine the winner.

**Code mapping:**

- Python: `AttributionService` in `partnership/application/attribution_service.py`
 `AttributionService` in `packages/partnership/src/application/attribution-service.ts`

**Related terms:** [Attribution Window](#attribution-window), [First-Touch / Last-Touch Attribution](#first-touch--last-touch-attribution), [Referral Conflict Resolution](#referral-conflict-resolution), [Referral](#referral)

---

### Attribution Window

**Definition:** The time period after a [Click](#click) on a [Referral Link](#referral-link) during which a subsequent registration or [Qualifying Event](#qualifying-event) is still credited to the referring [Partner](#partner).

**Context:** Typical windows: 30 days for cookie-based attribution, unlimited for [Invite Token](#invite-token)-based attribution (until token expiry). If the user registers after the window expires, no [Referral](#referral) is created. The window duration is configured at the program level and may differ by [Partner Tier](#partner-tier) (higher tiers may get longer windows).

**Code mapping:**

- Python: `AttributionWindow` value object in `partnership/domain/attribution_window.py`
 `AttributionWindow` value object in `packages/partnership/src/domain/attribution-window.ts`

**Related terms:** [Attribution](#attribution), [Click](#click), [Referral Link](#referral-link), [Landing Page Attribution](#landing-page-attribution)

---

### First-Touch / Last-Touch Attribution

**Definition:** Models that determine which [Partner](#partner) gets credit when a user interacted with multiple [Referral Links](#referral-link) before converting. **First-Touch** credits the partner whose link the user clicked first. **Last-Touch** credits the partner whose link the user clicked most recently.

**Context:** The chosen model has significant financial implications — it determines which Partner earns the [Commission](#commission). First-Touch rewards discovery (who originally introduced the user), Last-Touch rewards closing (who triggered the final conversion). The model is configured at the program level. Some programs use weighted multi-touch models, but those add complexity and are less common.

**Related terms:** [Attribution](#attribution), [Click](#click), [Referral Conflict Resolution](#referral-conflict-resolution)

---

### Referral Conflict Resolution

**Definition:** The set of rules applied when multiple [Partners](#partner) claim [Attribution](#attribution) for the same user. Conflicts arise when a user clicks multiple [Referral Links](#referral-link), receives multiple [Invitations](#invitation), or enters a [Referral Code](#referral-code) different from their attribution cookie.

**Context:** Resolution priority (default, configurable):

1. **Invite Token** — explicit, personalized invitation wins over broadcast links.
2. **Manual Referral Code** — user deliberately entered a code during registration.
3. **Last-Touch cookie** — most recent Referral Link click within the [Attribution Window](#attribution-window).
4. **First-Touch cookie** — original Referral Link click.

Only one Partner is credited per user. Conflicts are logged for audit purposes.

**Code mapping:**

- Python: `ConflictResolutionPolicy` in `partnership/domain/conflict_resolution_policy.py`
 `ConflictResolutionPolicy` in `packages/partnership/src/domain/conflict-resolution-policy.ts`

**Related terms:** [Attribution](#attribution), [First-Touch / Last-Touch Attribution](#first-touch--last-touch-attribution), [Invite Token](#invite-token), [Referral Code](#referral-code)

---

## 4. Commissions & Rewards

### Commission

**Definition:** A monetary reward accrued to a [Partner](#partner) when a [Downstream Referral](#downstream-referral) performs a [Qualifying Event](#qualifying-event). The amount is determined by the [Commission Rate](#commission-rate) applicable to the event type and [Referral Depth](#referral-depth).

**Context:** A Commission is the core financial entity in this context. It goes through a lifecycle: accrued → [Pending](#pending-commission) (during [Hold Period](#hold-period)) → [Confirmed](#confirmed-commission) (available for payout) or [Reversed](#reversed-commission) (cancelled). A single Qualifying Event may generate multiple Commissions — one for each level in the [Referral Chain](#referral-chain) up to the maximum [Referral Depth](#referral-depth).

**Code mapping:**

- Python: `Commission` entity in `partnership/domain/commission.py`
 `Commission` class in `packages/partnership/src/domain/commission.ts`

**Related terms:** [Commission Rate](#commission-rate), [Commission Tier](#commission-tier), [Qualifying Event](#qualifying-event), [Pending Commission](#pending-commission), [Confirmed Commission](#confirmed-commission), [Reversed Commission](#reversed-commission), [Commission Ledger](#commission-ledger)

---

### Commission Rate

**Definition:** The percentage or fixed monetary amount earned per [Qualifying Event](#qualifying-event). Rates vary by event type, [Partner Tier](#partner-tier), and [Referral Depth](#referral-depth).

**Context:** Examples: "20% of first payment for Level 1 referrals", "$5 flat per registration for Bronze partners", "10% recurring for Gold partners at Level 1". Rates are defined in a rate table and can be adjusted without code changes. Rate changes apply only to future events — existing [Commissions](#commission) retain their original rate.

**Code mapping:**

- Python: `CommissionRate` value object in `partnership/domain/commission_rate.py`
 `CommissionRate` value object in `packages/partnership/src/domain/commission-rate.ts`

**Related terms:** [Commission](#commission), [Commission Tier](#commission-tier), [Partner Tier](#partner-tier), [Qualifying Event](#qualifying-event)

---

### Commission Tier

**Definition:** A specific [Commission Rate](#commission-rate) assigned to a particular [Referral Depth](#referral-depth) level within a [Partner Tier](#partner-tier). Defines how much a Partner earns from activity at each level of their [Referral Chain](#referral-chain).

**Context:** Example commission tier table for a Gold partner:

| Referral Depth | Commission Rate |
|----------------|----------------|
| Level 1 (direct) | 20% |
| Level 2 (sub-partner's referral) | 10% |
| Level 3 (sub-sub-partner's referral) | 5% |

Higher [Partner Tiers](#partner-tier) typically unlock deeper levels and/or higher rates. The total commission across all levels for a single event must not exceed a configurable ceiling (e.g., 35%).

**Code mapping:**

- Python: `CommissionTierTable` in `partnership/domain/commission_tier.py`
 `CommissionTierTable` in `packages/partnership/src/domain/commission-tier.ts`

**Related terms:** [Commission Rate](#commission-rate), [Referral Depth](#referral-depth), [Partner Tier](#partner-tier), [Referral Chain](#referral-chain)

---

### Qualifying Event

**Definition:** An action performed by a [Downstream Referral](#downstream-referral) that triggers [Commission](#commission) accrual for the referring [Partner](#partner) (and their [Upstream Partners](#upstream-partner)). The event type and amount determine the commission calculation.

**Context:** Common qualifying events:

- `Registration` — user created an account (may trigger a flat [Referral Bonus](#referral-bonus)).
- `FirstPayment` — user completed their first paid transaction.
- `Subscription` — user subscribed to a paid plan.
- `RecurringPayment` — user made a subsequent payment (triggers [Lifetime Commission](#lifetime-commission) if applicable).
- `Upgrade` — user upgraded to a higher plan.

Not every user action is a Qualifying Event — only events explicitly defined in the [Partner Agreement](#partner-agreement) trigger commissions.

**Code mapping:**

- Python: `QualifyingEvent` domain event in `partnership/domain/events.py`
 `QualifyingEvent` type in `packages/partnership/src/domain/events.ts`

**Related terms:** [Commission](#commission), [Referral](#referral), [Lifetime Commission](#lifetime-commission), [Referral Bonus](#referral-bonus)

---

### Commission Ledger

**Definition:** An append-only, auditable record of all [Commission](#commission) transactions: accruals, confirmations, reversals, and adjustments. Every change to a Partner's commission balance is recorded as a ledger entry.

**Context:** The ledger is the single source of truth for commission accounting. Each entry contains: timestamp, Partner ID, Commission ID, event type (accrued, confirmed, reversed, adjusted), amount, currency, and reason. The [Partner Balance](#partner-balance) is derived by aggregating ledger entries — it is never stored as a standalone mutable field.

**Code mapping:**

- Python: `CommissionLedger` entity in `partnership/domain/commission_ledger.py`, `LedgerEntry` value object
 `CommissionLedger` class in `packages/partnership/src/domain/commission-ledger.ts`, `LedgerEntry` value object

**Related terms:** [Commission](#commission), [Partner Balance](#partner-balance), [Confirmed Commission](#confirmed-commission), [Reversed Commission](#reversed-commission)

---

### Pending Commission

**Definition:** A [Commission](#commission) that has been accrued but is still within the [Hold Period](#hold-period). Pending Commissions are visible on the partner dashboard but are not yet available for [Payout](#payout).

**Context:** The pending state protects against premature payouts for events that may be reversed (refunds, chargebacks, trial cancellations). If the underlying event is reversed during the hold period, the commission transitions to [Reversed](#reversed-commission) instead of [Confirmed](#confirmed-commission).

**Related terms:** [Commission](#commission), [Hold Period](#hold-period), [Confirmed Commission](#confirmed-commission), [Reversed Commission](#reversed-commission)

---

### Hold Period

**Definition:** A configurable duration after [Commission](#commission) accrual during which the commission remains in [Pending](#pending-commission) state before it can be confirmed and paid out.

**Context:** Hold Period protects the program from paying commissions on events that are later reversed (refunds, chargebacks, free trial abuse). Typical durations: 14-30 days for one-time payments, full trial period + 7 days for trial-based subscriptions. The hold period is defined per [Qualifying Event](#qualifying-event) type and may vary by [Partner Tier](#partner-tier) (trusted partners may get shorter holds).

**Code mapping:**

- Python: `HoldPeriod` value object in `partnership/domain/hold_period.py`
 `HoldPeriod` value object in `packages/partnership/src/domain/hold-period.ts`

**Related terms:** [Pending Commission](#pending-commission), [Confirmed Commission](#confirmed-commission), [Qualifying Event](#qualifying-event)

---

### Confirmed Commission

**Definition:** A [Commission](#commission) that has passed the [Hold Period](#hold-period) without reversal and is now available for [Payout](#payout). The amount is added to the [Partner Balance](#partner-balance).

**Context:** Confirmation is an automated, irreversible transition (under normal circumstances). Once confirmed, a commission can only be removed via [Clawback](#clawback) in fraud cases. The confirmation event is recorded in the [Commission Ledger](#commission-ledger) and triggers a recalculation of the [Partner Balance](#partner-balance).

**Related terms:** [Commission](#commission), [Hold Period](#hold-period), [Pending Commission](#pending-commission), [Partner Balance](#partner-balance), [Payout](#payout)

---

### Reversed Commission

**Definition:** A [Commission](#commission) that has been cancelled before or after confirmation, due to the underlying [Qualifying Event](#qualifying-event) being invalidated (refund, chargeback, fraud).

**Context:** Reversal reasons: the referred user requested a refund, the payment was charged back, [Fraud Review](#fraud-review) determined the referral was illegitimate, or the referred user's account was terminated. If the commission was already paid out, the reversal creates a negative entry in the [Commission Ledger](#commission-ledger) and reduces the [Partner Balance](#partner-balance) (see [Clawback](#clawback)).

**Related terms:** [Commission](#commission), [Clawback](#clawback), [Fraud Review](#fraud-review), [Commission Ledger](#commission-ledger)

---

### Referral Bonus

**Definition:** A one-time reward granted to the referred user (not the Partner) as an incentive for accepting the invitation and completing a specific action (registration, first purchase).

**Context:** Referral Bonuses are a marketing tool to increase conversion — they make the invitation more attractive to the recipient. Examples: "$10 credit on first purchase", "1 month free on any plan", "500 bonus points". The bonus is distinct from the [Commission](#commission) (which goes to the Partner). Bonus fulfillment may be delegated to the Billing context via a domain event.

**Code mapping:**

- Python: `ReferralBonus` value object in `partnership/domain/referral_bonus.py`
 `ReferralBonus` value object in `packages/partnership/src/domain/referral-bonus.ts`

**Related terms:** [Referral](#referral), [Qualifying Event](#qualifying-event), [Commission](#commission)

**Not to be confused with:** [Commission](#commission) — the bonus goes to the referred user; the commission goes to the Partner.

---

### Lifetime Commission

**Definition:** A [Commission](#commission) model where the [Partner](#partner) earns a percentage of every future payment made by a [Downstream Referral](#downstream-referral), for as long as the referred user remains a paying customer.

**Context:** Lifetime Commission is the most lucrative model for partners and the most expensive for the platform. It creates strong alignment — the partner is incentivized to refer high-quality, long-term users. Lifetime commissions are accrued on each [RecurringPayment](#qualifying-event) qualifying event. They can be capped by time (e.g., commissions for 12 months after referral) or total amount (e.g., up to $500 per referred user).

**Related terms:** [Commission](#commission), [Commission Rate](#commission-rate), [Qualifying Event](#qualifying-event), [Downstream Referral](#downstream-referral)

---

## 5. Payouts & Balances

### Partner Balance

**Definition:** The current amount of [Confirmed Commissions](#confirmed-commission) available for withdrawal by a [Partner](#partner). The balance is a derived value, calculated by aggregating all entries in the [Commission Ledger](#commission-ledger) and [Payout Ledger](#payout-ledger).

**Context:** Partner Balance = sum of confirmed commissions - sum of completed payouts - sum of clawbacks. The balance is never directly modified — it changes only as a result of new ledger entries. A negative balance (from [Clawbacks](#clawback)) is deducted from future commissions.

**Code mapping:**

- Python: `PartnerBalanceService` in `partnership/application/partner_balance_service.py`
 `PartnerBalanceService` in `packages/partnership/src/application/partner-balance-service.ts`

**Related terms:** [Confirmed Commission](#confirmed-commission), [Payout](#payout), [Clawback](#clawback), [Commission Ledger](#commission-ledger), [Payout Ledger](#payout-ledger)

---

### Payout

**Definition:** A transfer of funds from the platform to the [Partner](#partner)'s external account, reducing their [Partner Balance](#partner-balance) by the payout amount.

**Context:** Payouts can be triggered manually by the Partner (on-demand) or automatically via [Payout Schedule](#payout-schedule). Each payout must meet the [Minimum Payout Threshold](#minimum-payout-threshold). Payouts are processed through an external payment provider (PayPal, Stripe Connect, bank transfer) via a Driven Port / adapter in the infrastructure layer.

**Code mapping:**

- Python: `Payout` entity in `partnership/domain/payout.py`, `PayoutGateway` Protocol in `partnership/domain/payout_gateway.py`
 `Payout` class in `packages/partnership/src/domain/payout.ts`, `PayoutGateway` interface in `packages/partnership/src/domain/payout-gateway.ts`

**Related terms:** [Partner Balance](#partner-balance), [Payout Status](#payout-status), [Payout Method](#payout-method), [Minimum Payout Threshold](#minimum-payout-threshold), [Payout Schedule](#payout-schedule)

---

### Payout Method

**Definition:** The channel through which a [Partner](#partner) receives their [Payout](#payout). Each Partner selects and configures at least one payout method.

**Context:** Supported methods are defined at the program level. Common options: bank transfer (requires IBAN/routing number), PayPal (requires email), Stripe Connect (requires connected account), cryptocurrency (requires wallet address). Payout methods are validated at setup and can be changed at any time, but changes may trigger a [Compliance Hold](#compliance-hold) for security.

**Code mapping:**

- Python: `PayoutMethod` entity in `partnership/domain/payout_method.py`
 `PayoutMethod` class in `packages/partnership/src/domain/payout-method.ts`

**Related terms:** [Payout](#payout), [Partner](#partner)

---

### Minimum Payout Threshold

**Definition:** The minimum [Partner Balance](#partner-balance) required before a [Payout](#payout) can be requested or automatically triggered. Payouts below this amount are not processed.

**Context:** The threshold prevents micro-payouts that would be uneconomical due to transaction fees. Typical values: $50-$100. The threshold is configured at the program level and may vary by [Payout Method](#payout-method) (bank transfers may have higher thresholds than PayPal due to higher fees).

**Code mapping:**

- Python: `MinimumPayoutThreshold` value object in `partnership/domain/payout_policy.py`
 `MinimumPayoutThreshold` value object in `packages/partnership/src/domain/payout-policy.ts`

**Related terms:** [Partner Balance](#partner-balance), [Payout](#payout), [Payout Schedule](#payout-schedule)

---

### Payout Schedule

**Definition:** The automatic timing for processing [Payouts](#payout) to [Partners](#partner). Defines when the system checks balances and initiates transfers.

**Context:** Schedule options:

- `Monthly` — payouts on a fixed day each month (e.g., 1st or 15th).
- `Biweekly` — every two weeks.
- `OnThreshold` — automatically when [Partner Balance](#partner-balance) exceeds the [Minimum Payout Threshold](#minimum-payout-threshold).
- `Manual` — partner requests payouts manually; no automatic processing.

Partners can select their preferred schedule. Regardless of schedule, the [Minimum Payout Threshold](#minimum-payout-threshold) must be met.

**Code mapping:**

- Python: `PayoutSchedule` value object in `partnership/domain/payout_policy.py`
 `PayoutSchedule` value object in `packages/partnership/src/domain/payout-policy.ts`

**Related terms:** [Payout](#payout), [Minimum Payout Threshold](#minimum-payout-threshold), [Partner Balance](#partner-balance)

---

### Payout Status

**Definition:** The current lifecycle state of a [Payout](#payout) request.

**Context:** Status transitions:

- `Requested` — Partner or schedule initiated a payout. Funds are reserved from [Partner Balance](#partner-balance).
- `Processing` — Payout submitted to the external [Payout Method](#payout-method) provider.
- `Completed` — Funds successfully transferred. Recorded in the [Payout Ledger](#payout-ledger).
- `Failed` — Transfer failed (invalid account, provider error). Reserved funds are returned to Partner Balance. Partner is notified.
- `Cancelled` — Payout cancelled by Partner or admin before processing. Reserved funds returned.

**Code mapping:**

- Python: `PayoutStatus` enum in `partnership/domain/payout_status.py`
 `PayoutStatus` union type in `packages/partnership/src/domain/payout-status.ts`

**Related terms:** [Payout](#payout), [Partner Balance](#partner-balance), [Payout Ledger](#payout-ledger)

---

### Payout Ledger

**Definition:** An append-only, auditable record of all [Payout](#payout) transactions: requests, completions, failures, and cancellations. Together with the [Commission Ledger](#commission-ledger), it forms the complete financial history of a [Partner](#partner).

**Context:** Each entry contains: timestamp, Partner ID, Payout ID, amount, currency, [Payout Method](#payout-method), [Payout Status](#payout-status) transition, and external transaction reference (from payment provider). The [Partner Balance](#partner-balance) is derived from both ledgers: commission ledger (credits) minus payout ledger (debits).

**Code mapping:**

- Python: `PayoutLedger` entity in `partnership/domain/payout_ledger.py`, `PayoutLedgerEntry` value object
 `PayoutLedger` class in `packages/partnership/src/domain/payout-ledger.ts`, `PayoutLedgerEntry` value object

**Related terms:** [Payout](#payout), [Commission Ledger](#commission-ledger), [Partner Balance](#partner-balance)

---

## 6. Fraud Prevention & Compliance

### Self-Referral

**Definition:** A prohibited pattern where a [Partner](#partner) creates referrals to accounts they control (their own email addresses, family accounts, fake accounts) to earn illegitimate [Commissions](#commission).

**Context:** Self-referral detection compares IP addresses, device fingerprints, email domains, and payment methods between the Partner and the referred user. Detected self-referrals result in [Commission](#commission) reversal, [Partner Status](#partner-status) suspension, and potential [Clawback](#clawback) of previously paid commissions.

**Related terms:** [Referral Fraud](#referral-fraud), [Fraud Review](#fraud-review), [Clawback](#clawback)

---

### Cookie Stuffing

**Definition:** A fraudulent technique where a [Partner](#partner) drops attribution cookies on users' browsers without their knowledge or genuine interaction — typically via hidden iframes, pop-unders, or injected scripts.

**Context:** Cookie stuffing inflates [Click](#click) counts and steals [Attribution](#attribution) from legitimate partners. Detection signals: abnormally high click-to-conversion ratio from a single source, clicks without corresponding page views, clicks from known bot user-agents. Detected stuffing results in immediate [Partner Status](#partner-status) termination and [Clawback](#clawback).

**Related terms:** [Referral Fraud](#referral-fraud), [Attribution](#attribution), [Click](#click), [Fraud Review](#fraud-review)

---

### Referral Fraud

**Definition:** Any deliberate manipulation of the referral system to earn undeserved [Commissions](#commission). Encompasses [Self-Referral](#self-referral), [Cookie Stuffing](#cookie-stuffing), fake account creation, incentivized sign-ups without genuine intent, and attribution manipulation.

**Context:** Referral fraud undermines program economics and alienates legitimate partners. The system must implement both automated detection (anomaly scoring, velocity checks, device fingerprinting) and manual [Fraud Review](#fraud-review) processes. All fraud-related actions are recorded as [Security Events](./auth.md#security-event) for audit.

**Code mapping:**

- Python: `FraudDetectionService` in `partnership/application/fraud_detection_service.py`
 `FraudDetectionService` in `packages/partnership/src/application/fraud-detection-service.ts`

**Related terms:** [Self-Referral](#self-referral), [Cookie Stuffing](#cookie-stuffing), [Fraud Review](#fraud-review), [Clawback](#clawback), [Compliance Hold](#compliance-hold)

---

### Fraud Review

**Definition:** A manual or semi-automated investigation process triggered when the system detects suspicious [Referral](#referral) or [Commission](#commission) patterns. During review, the affected [Partner](#partner) is placed on [Compliance Hold](#compliance-hold).

**Context:** Fraud Review is initiated by automated alerts (anomaly scores above threshold) or manual reports. The reviewer examines: click patterns, conversion timing, device fingerprints, payment method overlap between Partner and referrals, geographic anomalies. Review outcomes: `Cleared` (false positive, Partner reactivated), `Confirmed Fraud` (commissions reversed, partner terminated, potential [Clawback](#clawback)).

**Code mapping:**

- Python: `FraudReview` entity in `partnership/domain/fraud_review.py`
 `FraudReview` class in `packages/partnership/src/domain/fraud-review.ts`

**Related terms:** [Referral Fraud](#referral-fraud), [Compliance Hold](#compliance-hold), [Clawback](#clawback), [Partner Status](#partner-status)

---

### Clawback

**Definition:** The recovery of previously paid [Commissions](#commission) from a [Partner](#partner) after fraud is confirmed or a qualifying event is reversed (refund, chargeback). Creates a negative entry in the [Commission Ledger](#commission-ledger) and reduces the [Partner Balance](#partner-balance).

**Context:** Clawbacks are the last resort and only occur after: (1) the [Hold Period](#hold-period) has already passed (otherwise the commission is simply [Reversed](#reversed-commission)), AND (2) the commission has already been [Confirmed](#confirmed-commission) or paid out. If the Partner Balance is insufficient to cover the clawback, the balance goes negative — future commissions are applied against the negative balance first. Clawbacks require admin approval and are fully auditable.

**Code mapping:**

- Python: `ClawbackService` in `partnership/application/clawback_service.py`
 `ClawbackService` in `packages/partnership/src/application/clawback-service.ts`

**Related terms:** [Commission Ledger](#commission-ledger), [Partner Balance](#partner-balance), [Reversed Commission](#reversed-commission), [Fraud Review](#fraud-review)

---

### Compliance Hold

**Definition:** A temporary freeze on a [Partner](#partner)'s ability to receive [Payouts](#payout) while a [Fraud Review](#fraud-review), legal review, or account verification is in progress.

**Context:** During a Compliance Hold, the Partner's [Status](#partner-status) is set to `Suspended`. Existing [Commissions](#commission) continue to accrue (they may be legitimate) but cannot be paid out. New [Referral Links](#referral-link) remain active to avoid alerting the Partner prematurely (in fraud cases). The hold is lifted when the review concludes — either the Partner is cleared and status restored to `Active`, or fraud is confirmed and status transitions to `Terminated`.

**Related terms:** [Partner Status](#partner-status), [Fraud Review](#fraud-review), [Payout](#payout)

---

## 7. Analytics & Performance

### Click

**Definition:** A recorded instance of a user following a [Referral Link](#referral-link). Each click captures: timestamp, [Referral Code](#referral-code), IP address (hashed for privacy), user agent, referrer URL, and landing page.

**Context:** Clicks are the top of the referral funnel. They feed into [Landing Page Attribution](#landing-page-attribution) and are the numerator for [Conversion Rate](#conversion-rate) calculations. Duplicate clicks from the same device within a short window (e.g., 5 minutes) are deduplicated. Bot traffic is filtered using user-agent analysis and behavioral signals.

**Code mapping:**

- Python: `Click` domain event in `partnership/domain/events.py`, `ClickTracker` in `partnership/application/click_tracker.py`
 `Click` type in `packages/partnership/src/domain/events.ts`, `ClickTracker` in `packages/partnership/src/application/click-tracker.ts`

**Related terms:** [Referral Link](#referral-link), [Conversion](#conversion), [Conversion Rate](#conversion-rate), [Landing Page Attribution](#landing-page-attribution)

---

### Conversion

**Definition:** The transition of a [Click](#click) visitor into a user who has completed a [Qualifying Event](#qualifying-event) (typically registration or first payment). A Conversion is the point at which a [Referral](#referral) is created and [Commission](#commission) accrual begins.

**Context:** Not every click results in a conversion — the funnel is: Click → Visit → Registration → Qualifying Event. The conversion event depends on program configuration: some programs count registration as a conversion, others require a paid transaction. Conversion data is used to calculate [Conversion Rate](#conversion-rate) and [Earnings Per Click (EPC)](#earnings-per-click-epc).

**Related terms:** [Click](#click), [Qualifying Event](#qualifying-event), [Referral](#referral), [Conversion Rate](#conversion-rate)

---

### Conversion Rate

**Definition:** The percentage of [Clicks](#click) that result in [Conversions](#conversion) within the [Attribution Window](#attribution-window). Calculated as: `(conversions / clicks) * 100%`.

**Context:** Conversion Rate is a key performance metric for [Partners](#partner) and the program as a whole. Low conversion rates may indicate: low-quality traffic, mismatched audience, poor landing page experience, or broken tracking. Partners can compare their rates against program averages. Sudden drops in conversion rate may signal technical issues or fraud.

**Related terms:** [Click](#click), [Conversion](#conversion), [Earnings Per Click (EPC)](#earnings-per-click-epc), [Partner Performance Report](#partner-performance-report)

---

### Earnings Per Click (EPC)

**Definition:** The average revenue a [Partner](#partner) earns for each [Click](#click) on their [Referral Links](#referral-link). Calculated as: `total confirmed commissions / total clicks` over a given period.

**Context:** EPC is the single most important metric for partners comparing program profitability. It combines [Conversion Rate](#conversion-rate) and [Commission Rate](#commission-rate) into a single number. Higher EPC indicates either better-converting traffic or higher-value referrals. Program-wide EPC is published to attract new partners.

**Related terms:** [Click](#click), [Confirmed Commission](#confirmed-commission), [Conversion Rate](#conversion-rate), [Partner Performance Report](#partner-performance-report)

---

### Partner Performance Report

**Definition:** An aggregated view of a [Partner](#partner)'s referral metrics over a configurable time period. Includes: total [Clicks](#click), [Conversions](#conversion), [Conversion Rate](#conversion-rate), [EPC](#earnings-per-click-epc), commissions earned (pending / confirmed / reversed), [Downstream Referral](#downstream-referral) count by [Referral Depth](#referral-depth), and payout history.

**Context:** Performance Reports are available on the partner dashboard and via API. They serve both the Partner (track their own performance) and the program team (identify top performers, detect anomalies, plan tier promotions). Reports are generated asynchronously for large date ranges and cached for repeated access.

**Code mapping:**

- Python: `PartnerPerformanceReportService` in `partnership/application/partner_performance_report_service.py`
 `PartnerPerformanceReportService` in `packages/partnership/src/application/partner-performance-report-service.ts`

**Related terms:** [Click](#click), [Conversion](#conversion), [Conversion Rate](#conversion-rate), [Earnings Per Click (EPC)](#earnings-per-click-epc), [Partner Tier](#partner-tier)

---

## Cross-Context Boundary Notes

The Partnership bounded context interacts with other contexts through explicit contracts. The following table clarifies term boundaries:

| Partnership Term | Other Context | Their Term | Relationship |
|------------------|---------------|------------|--------------|
| `Partner` | Auth | [`AuthUser`](./auth.md#authuser) | Linked via `IdentityId`. Partnership owns referral relationships and commissions; Auth owns credentials, sessions, roles. |
| `Partner` | Billing | [`Billing Customer`](./billing.md#billing-customer) | A Partner may also be a paying customer. Partnership does not access billing data directly — commission triggers arrive via domain events from Billing. |
| `Partner` | Project | [`Member`](./project.md#member) | A Partner may also be a Member of one or more Projects. Partnership manages referral relationships; Project manages workspace membership. The two contexts do not share models. |
| `Partner` | Learning | [`Master`](./learning.md#master), [`Learner`](./learning.md#learner) | A Partner may also be a Master or Learner. Partnership manages referral relationships and commissions; Learning manages educational relationships. The two contexts do not share models. |
| `Qualifying Event` | Billing | [`Payment`](./billing.md#payment), [`Subscription`](./billing.md#subscription) | Billing emits payment/subscription events. Partnership subscribes and evaluates them as potential Qualifying Events. |
| `Qualifying Event` | Learning | [`Enrollment`](./learning.md#enrollment), [`Graduation`](./learning.md#graduation) | A referral that leads to a paid Enrollment may trigger a commission. Graduation may trigger an additional commission. Partnership subscribes to `EnrollmentCreated` and `LearnerGraduated` events. |
| `Referral Bonus` | Billing | [`Credit`](./billing.md#credit), [`Coupon`](./billing.md#coupon) | Partnership decides the bonus; Billing fulfills it by applying a credit or coupon to the referred user's account. |
| `Referral Link` | Project | [`Invite Link`](./project.md#invite-link) | A Referral Link may be embedded within or associated with a Project Invite Link. Partnership tracks attribution; Project handles workspace joining. |
| `Payout` | Billing / Payments | `Transfer`, `Disbursement` | Partnership calculates the payout amount and triggers the transfer. The actual fund movement is handled by a payment provider adapter in Partnership's infrastructure layer. |
| `Referral Fraud` | Auth | [`Security Event`](./auth.md#security-event) | Fraud detection in Partnership emits events that the Auth/Security context may consume for cross-context threat analysis. |

**Integration rules:**

- Other contexts MUST NOT import Partnership domain models directly. Use events or API contracts.
- Partnership MUST NOT query the Billing database directly. Payment and subscription data arrives via domain events (`PaymentCompleted`, `SubscriptionCreated`), which Partnership maps to [Qualifying Events](#qualifying-event) through its own Anti-Corruption Layer (see [AGENTS.md 4.3](../AGENTS.md#43-context-mapping-карта-контекстов)).
- When a new user registers via a referral, the Auth context emits a `UserRegistered` event. Partnership subscribes to this event and creates the [Referral](#referral) if valid [Attribution](#attribution) data exists.
- [Partner Balance](#partner-balance) and [Payout](#payout) are financial concepts owned by Partnership. They are NOT shared with or derived from the Billing context's account balance.
