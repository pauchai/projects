# Billing & Payments — Ubiquitous Language Glossary

This glossary defines the authoritative vocabulary for the **Billing & Payments** bounded context. All code, documentation, API contracts, and team communication within this context MUST use these terms consistently.

**Bounded Context scope:** Customer billing accounts, payment processing (cards, crypto, platform balance), subscription management with usage-based metering, invoice generation, refunds, credits and promotional discounts, and master payouts for teaching services. Partner payouts are NOT part of this context — they are managed by the [Partnership context](./partnership.md).

**Financial model:** The platform operates a **mixed billing model**: subscriptions with usage-based components (seats, storage), one-time payments for mentorship enrollment, and outgoing payouts to masters. All monetary values are represented as [Money](#money) value objects (amount + currency). The platform takes a [Platform Commission](#platform-commission) from learner payments before paying out masters.

**Code mapping convention:**

- Python: `billing/domain/` for domain models, `billing/application/` for use cases, `billing/infrastructure/` for adapters
 `packages/billing/src/domain/`, `packages/billing/src/application/`, `packages/billing/src/infrastructure/`

**Cross-context dependencies:** This context references identities from the [Auth bounded context](./auth.md). A [Billing Customer](#billing-customer) is linked to an [AuthUser](./auth.md#authuser) via `IdentityId`, but the two models are separate — Auth owns credentials and sessions, Billing owns financial data, payment methods, and transaction history.

---

## 1. Customer & Account

### Billing Customer

**Definition:** The financial identity of a user within the Billing context. A Billing Customer owns a [Billing Account](#billing-account), one or more [Payment Methods](#payment-method), [Subscriptions](#subscription), and a complete transaction history.

**Context:** Every Billing Customer is linked to an [AuthUser](./auth.md#authuser) via `IdentityId`, but `Billing Customer` is a separate domain model — it does not inherit from or extend `AuthUser`. A Billing Customer is created automatically when a user performs their first financial action (subscribes, purchases, or adds a payment method). The customer record stores billing-specific data: legal name, billing address, tax ID, preferred [Currency](#currency), and [Default Payment Method](#default-payment-method).

**Code mapping:**

- Python: `BillingCustomer` aggregate root in `billing/domain/billing_customer.py`
 `BillingCustomer` class in `packages/billing/src/domain/billing-customer.ts`

**Related terms:** [Billing Account](#billing-account), [Payment Method](#payment-method), [Subscription](#subscription), [Default Payment Method](#default-payment-method)

**Not to be confused with:** [AuthUser](./auth.md#authuser) in Auth (owns credentials, sessions, roles), [Member](./project.md#member) in Projects (owns project membership), [Learner](./learning.md#learner) in Learning (owns educational progress), or [Partner](./partnership.md#partner) in Partnership (owns referral relationships). A single person may be all of these, but each context maintains its own model.

---

### Billing Account

**Definition:** A financial ledger associated with a [Billing Customer](#billing-customer). Tracks the customer's current [Platform Balance](#platform-balance), [Credit](#credit) balance, outstanding charges, and provides a consolidated view of all [Transactions](#transaction).

**Context:** Every Billing Customer has exactly one Billing Account. The account is the central financial record — all charges, payments, refunds, credits, and adjustments are recorded as [Transactions](#transaction) against this account. The account balance reflects the net of all transactions. A negative balance means the customer owes money; a positive balance means they have prepaid funds or [Credits](#credit) available.

**Code mapping:**

- Python: `BillingAccount` entity in `billing/domain/billing_account.py`
 `BillingAccount` class in `packages/billing/src/domain/billing-account.ts`

**Related terms:** [Billing Customer](#billing-customer), [Transaction](#transaction), [Platform Balance](#platform-balance), [Credit](#credit)

---

### Payment Method

**Definition:** A stored instrument that a [Billing Customer](#billing-customer) can use to make payments. Each Payment Method has a [Payment Method Type](#payment-method-type), a display identifier (e.g., last 4 digits of a card), and a status (active, expired, removed).

**Context:** Customers can have multiple Payment Methods on file. One is designated as the [Default Payment Method](#default-payment-method) for automatic charges (subscription renewals, usage-based billing). Payment Method details (full card numbers, crypto private keys) are NEVER stored in the Billing domain — only tokenized references from the [Payment Gateway](#payment-gateway). The domain stores: type, display label, expiry (for cards), status, and the gateway-issued token.

**Code mapping:**

- Python: `PaymentMethod` entity in `billing/domain/payment_method.py`
 `PaymentMethod` class in `packages/billing/src/domain/payment-method.ts`

**Related terms:** [Payment Method Type](#payment-method-type), [Default Payment Method](#default-payment-method), [Billing Customer](#billing-customer), [Payment Gateway](#payment-gateway)

---

### Payment Method Type

**Definition:** An enum classifying the instrument used for payment. Values: `CreditCard`, `DebitCard`, `CryptoWallet`, `PlatformBalance`.

**Context:** Each type has different processing characteristics: cards are charged via traditional payment gateways (Stripe, etc.); crypto wallets go through a crypto payment processor; `PlatformBalance` deducts directly from the customer's prepaid [Platform Balance](#platform-balance) or available [Credits](#credit). The type determines which [Payment Gateway](#payment-gateway) adapter is used for processing. A customer may mix types — e.g., pay with platform balance first, then charge the remainder to a card.

**Code mapping:**

- Python: `PaymentMethodType` enum in `billing/domain/payment_method_type.py`
 `PaymentMethodType` union type in `packages/billing/src/domain/payment-method-type.ts`

**Related terms:** [Payment Method](#payment-method), [Platform Balance](#platform-balance), [Payment Gateway](#payment-gateway), [Credit](#credit)

---

### Default Payment Method

**Definition:** The [Payment Method](#payment-method) automatically used when a [Billing Customer](#billing-customer) is charged without explicitly selecting a method — e.g., subscription renewals, usage-based overage charges.

**Context:** Every Billing Customer with an active [Subscription](#subscription) must have a Default Payment Method set. If the default method fails (card declined, insufficient crypto balance), the system may attempt other stored methods before marking the payment as `Failed`. Changing the Default Payment Method does not affect in-flight [Payment Intents](#payment-intent) — only future automatic charges.

**Code mapping:**

- Python: property on `BillingCustomer` aggregate root in `billing/domain/billing_customer.py`
 property on `BillingCustomer` class in `packages/billing/src/domain/billing-customer.ts`

**Related terms:** [Payment Method](#payment-method), [Billing Customer](#billing-customer), [Subscription](#subscription)

---

### Billing Event

**Definition:** A domain event emitted when a significant financial action occurs within the Billing context. Billing Events are the official contract for cross-context consumers.

**Context:** Examples: `PaymentCompleted`, `PaymentFailed`, `SubscriptionCreated`, `SubscriptionRenewed`, `SubscriptionCancelled`, `InvoiceIssued`, `RefundProcessed`, `CreditApplied`, `PayoutCompleted`, `UsageRecorded`, `PlanChanged`. Events follow the Published Language pattern (see [AGENTS.md 4.3](../AGENTS.md#43-context-mapping-карта-контекстов)). Each event carries a timestamp, the `BillingCustomerId`, and event-specific payload (amount, currency, related entity IDs).

**Code mapping:**

- Python: `BillingEvent` base dataclass in `billing/domain/events.py` with specific subclasses (`PaymentCompletedEvent`, `SubscriptionRenewedEvent`, etc.)
 `BillingEvent` union type in `packages/billing/src/domain/events.ts` with specific types

**Related terms:** [Payment](#payment), [Subscription](#subscription), [Invoice](#invoice), [Refund](#refund), [Master Payout](#master-payout)

---

## 2. Plans & Subscriptions

### Plan

**Definition:** A predefined pricing package that defines what resources and features a [Billing Customer](#billing-customer) gets for a recurring price. Each Plan specifies included limits (seats, storage, features), a base price per [Billing Cycle](#billing-cycle), and [Overage](#overage) rates for usage beyond included limits.

**Context:** Plans are platform-managed entities (created by admins, not by customers). They serve as templates — a customer subscribes to a Plan, creating a [Subscription](#subscription). Plans can target different scopes: platform-wide access or per-project resources. Each Plan belongs to a [Plan Tier](#plan-tier) that positions it in the pricing hierarchy. Plans are versioned — when pricing changes, existing subscriptions keep their original plan terms until renewal or explicit migration.

**Code mapping:**

- Python: `Plan` entity in `billing/domain/plan.py`
 `Plan` class in `packages/billing/src/domain/plan.ts`

**Related terms:** [Plan Tier](#plan-tier), [Billing Cycle](#billing-cycle), [Subscription](#subscription), [Overage](#overage)

**Not to be confused with:** [Learning Program](./learning.md#learning-program) in the Learning context — a Learning Program is an educational curriculum; a Plan is a pricing package.

---

### Plan Tier

**Definition:** A classification level that positions a [Plan](#plan) within the pricing hierarchy. Typical values: `Free`, `Starter`, `Professional`, `Enterprise`. Higher tiers unlock more resources, higher limits, and premium features.

**Context:** Plan Tiers are a marketing and product concept reified in the domain. Each tier maps to one or more Plans (e.g., `Professional Monthly`, `Professional Annual` are two Plans within the `Professional` tier). Tier determines: maximum [Seats](./project.md#seat), storage quota, API rate limits, support level, and access to premium features (advanced analytics, custom branding, priority matching with [Masters](./learning.md#master)). Upgrading tier mid-cycle is prorated; downgrading takes effect at the next billing cycle.

**Code mapping:**

- Python: `PlanTier` enum in `billing/domain/plan_tier.py`
 `PlanTier` union type in `packages/billing/src/domain/plan-tier.ts`

**Related terms:** [Plan](#plan), [Subscription](#subscription)

---

### Billing Cycle

**Definition:** The recurring time period for subscription charges. Values: `Monthly`, `Quarterly`, `Annual`. Determines how often the customer is billed and when the [Subscription](#subscription) renews.

**Context:** Billing Cycle is set when a [Subscription](#subscription) is created and can be changed at renewal (e.g., switching from Monthly to Annual for a discount). The cycle defines the invoice period: at the start of each cycle, an [Invoice](#invoice) is generated with the plan's base price plus any [Overage](#overage) from the previous period. Annual cycles typically offer a discount (e.g., "2 months free"). The cycle also determines proration calculations when upgrading or downgrading mid-cycle.

**Code mapping:**

- Python: `BillingCycle` enum in `billing/domain/billing_cycle.py`
 `BillingCycle` union type in `packages/billing/src/domain/billing-cycle.ts`

**Related terms:** [Subscription](#subscription), [Plan](#plan), [Invoice](#invoice), [Overage](#overage)

---

### Subscription

**Definition:** An active, recurring agreement between a [Billing Customer](#billing-customer) and the platform for access to a [Plan](#plan). A Subscription tracks: the current billing period, next renewal date, [Subscription Status](#subscription-status), and payment history for this plan.

**Context:** A Subscription is created when a customer selects a Plan and completes the initial payment (or starts a [Trial Period](#trial-period)). Each customer can have multiple subscriptions (e.g., a platform subscription plus per-project subscriptions). Subscriptions auto-renew at the end of each [Billing Cycle](#billing-cycle) unless cancelled. Renewal triggers: (1) usage aggregation for the completed period, (2) [Invoice](#invoice) generation, (3) [Payment](#payment) attempt via the [Default Payment Method](#default-payment-method). If payment fails, the subscription enters `PastDue` status.

**Code mapping:**

- Python: `Subscription` entity in `billing/domain/subscription.py`
 `Subscription` class in `packages/billing/src/domain/subscription.ts`

**Related terms:** [Subscription Status](#subscription-status), [Plan](#plan), [Billing Cycle](#billing-cycle), [Billing Customer](#billing-customer), [Trial Period](#trial-period), [Invoice](#invoice)

---

### Subscription Status

**Definition:** An enum representing the current state of a [Subscription](#subscription). Values: `Trialing` (in free trial, not yet charged), `Active` (paid and current), `PastDue` (renewal payment failed, grace period), `Cancelled` (customer cancelled, access until end of paid period), `Expired` (billing period ended after cancellation or failed recovery).

**Context:** Status transitions:
- `Trialing` → `Active` (trial ends, first payment succeeds) | `Expired` (trial ends, no payment method)
- `Active` → `PastDue` (renewal payment fails) | `Cancelled` (customer requests cancellation)
- `PastDue` → `Active` (payment retry succeeds) | `Expired` (all retries exhausted, grace period over)
- `Cancelled` → `Expired` (current paid period ends)

Only `Trialing` and `Active` subscriptions grant full access to plan features. `PastDue` may have a configurable grace period (e.g., 7 days) with degraded access. `Cancelled` retains access until the end of the already-paid period.

**Code mapping:**

- Python: `SubscriptionStatus` enum in `billing/domain/subscription_status.py`
 `SubscriptionStatus` union type in `packages/billing/src/domain/subscription-status.ts`

**Related terms:** [Subscription](#subscription), [Trial Period](#trial-period), [Billing Event](#billing-event)

---

### Trial Period

**Definition:** A time-limited free access period granted to a [Billing Customer](#billing-customer) when they first subscribe to a [Plan](#plan). During the trial, the customer has full access to plan features without being charged.

**Context:** Trial Period is configured per [Plan](#plan) (e.g., "14-day free trial for Professional"). The trial starts when the [Subscription](#subscription) is created with `Trialing` [Subscription Status](#subscription-status). The customer is required to provide a [Payment Method](#payment-method) before or at trial start (depending on platform policy). When the trial ends: if a valid payment method exists, the first charge is attempted and the subscription transitions to `Active`; if not, the subscription transitions to `Expired`. A customer can only trial a given Plan Tier once (fraud prevention).

**Code mapping:**

- Python: `TrialPeriod` value object in `billing/domain/trial_period.py`
 `TrialPeriod` interface in `packages/billing/src/domain/trial-period.ts`

**Related terms:** [Subscription](#subscription), [Subscription Status](#subscription-status), [Plan](#plan), [Payment Method](#payment-method)

---

### Subscription Event

**Definition:** A domain event emitted when the state of a [Subscription](#subscription) changes. A specialized subset of [Billing Events](#billing-event).

**Context:** Examples: `SubscriptionCreated` (new subscription started), `SubscriptionRenewed` (auto-renewal succeeded), `SubscriptionUpgraded` (plan tier changed upward), `SubscriptionDowngraded` (plan tier changed downward), `SubscriptionCancelled` (customer requested cancellation), `SubscriptionExpired` (access ended), `TrialStarted`, `TrialExpired`, `SubscriptionPastDue` (payment failed). Each event carries `SubscriptionId`, `BillingCustomerId`, `PlanId`, and event-specific payload. These events are consumed by the Project context (to update [Member Limits](./project.md#member-limit) and [Project Quotas](./project.md#project-quota)) and by the Monitoring context.

**Code mapping:**

- Python: `SubscriptionEvent` subclasses of `BillingEvent` in `billing/domain/events.py` (`SubscriptionCreatedEvent`, `SubscriptionRenewedEvent`, etc.)
 Subscription-specific types within `BillingEvent` union in `packages/billing/src/domain/events.ts`

**Related terms:** [Subscription](#subscription), [Subscription Status](#subscription-status), [Billing Event](#billing-event)

---

## 3. Usage & Metering

### Usage Record

**Definition:** A timestamped entry recording the consumption of a measurable resource by a [Billing Customer](#billing-customer). Each record captures: who consumed (customer/project), what was consumed ([Usage Metric](#usage-metric)), how much, and when.

**Context:** Usage Records are the raw data for usage-based billing. They are reported by other bounded contexts via events: the Project context emits seat count changes ([MemberJoined](./project.md#membership-event), [MemberRemoved](./project.md#membership-event)), storage usage changes, etc. The Billing context receives these events through its Anti-Corruption Layer and stores them as Usage Records. Records are immutable once created — corrections are handled by creating adjustment records. At the end of each [Metering Period](#metering-period), records are aggregated to calculate charges.

**Code mapping:**

- Python: `UsageRecord` entity in `billing/domain/usage_record.py`
 `UsageRecord` class in `packages/billing/src/domain/usage-record.ts`

**Related terms:** [Usage Metric](#usage-metric), [Metering Period](#metering-period), [Overage](#overage), [Usage Invoice](#usage-invoice)

---

### Usage Metric

**Definition:** A named type of measurable resource tracked for billing purposes. Examples: `seat_count` (number of active project members), `storage_bytes` (file storage consumed), `api_calls` (API request count), `apprenticeship_sessions` (number of field sessions conducted).

**Context:** Usage Metrics are platform-defined and tied to [Plan](#plan) limits. Each Plan specifies an included quantity per metric (e.g., "10 seats included, 5 GB storage included"). Consumption beyond the included amount is billed as [Overage](#overage). Metrics have a measurement unit (`count`, `bytes`, `requests`) and an aggregation method (`max` for seats — peak concurrent usage; `sum` for API calls — total over the period).

**Code mapping:**

- Python: `UsageMetric` enum in `billing/domain/usage_metric.py`
 `UsageMetric` union type in `packages/billing/src/domain/usage-metric.ts`

**Related terms:** [Usage Record](#usage-record), [Plan](#plan), [Overage](#overage), [Metering Period](#metering-period)

---

### Metering Period

**Definition:** The time window over which [Usage Records](#usage-record) are aggregated to calculate the usage-based portion of a customer's bill. Typically aligned with the [Billing Cycle](#billing-cycle) (monthly, quarterly, annual).

**Context:** At the end of each Metering Period, the system: (1) aggregates all Usage Records per [Usage Metric](#usage-metric), (2) compares against Plan-included limits, (3) calculates [Overage](#overage) charges if limits were exceeded, (4) adds overage line items to the next [Invoice](#invoice). The Metering Period closes automatically at subscription renewal time. Records submitted after period closure are applied to the next period.

**Code mapping:**

- Python: `MeteringPeriod` value object in `billing/domain/metering_period.py`
 `MeteringPeriod` interface in `packages/billing/src/domain/metering-period.ts`

**Related terms:** [Usage Record](#usage-record), [Billing Cycle](#billing-cycle), [Overage](#overage), [Invoice](#invoice)

---

### Overage

**Definition:** Consumption of a [Usage Metric](#usage-metric) beyond the quantity included in a customer's [Plan](#plan). Overage is billed at a per-unit rate defined on the Plan (e.g., "$10 per additional seat per month," "$0.10 per GB of storage beyond 5 GB").

**Context:** Overage charges are calculated at the end of each [Metering Period](#metering-period) and added as [Invoice Line Items](#invoice-line-item) to the renewal invoice. Not all Plans allow overage — some have hard limits (usage blocked when the limit is reached). Plans that allow overage define an overage rate per [Usage Metric](#usage-metric). The system may emit warnings when usage approaches the limit (e.g., 80% threshold) so the customer can upgrade proactively. Overage events are consumed by the Project context as [Capacity Events](./project.md#capacity-event).

**Code mapping:**

- Python: `Overage` value object in `billing/domain/overage.py`
 `Overage` interface in `packages/billing/src/domain/overage.ts`

**Related terms:** [Usage Metric](#usage-metric), [Plan](#plan), [Metering Period](#metering-period), [Invoice Line Item](#invoice-line-item), [Usage Invoice](#usage-invoice)

---

### Usage Invoice

**Definition:** An [Invoice](#invoice) (or a section of an invoice) specifically covering usage-based charges for a [Metering Period](#metering-period). Contains [Invoice Line Items](#invoice-line-item) for each [Usage Metric](#usage-metric) where [Overage](#overage) occurred.

**Context:** Usage Invoices may be standalone (billed separately from the subscription) or merged into the subscription renewal invoice as additional line items — this is a platform configuration choice. Each line item shows: the metric, included amount, actual usage, overage quantity, per-unit rate, and total charge. The Usage Invoice is generated automatically at the close of each Metering Period.

**Code mapping:**

- Python: Usage-related `InvoiceLineItem` entries generated by `UsageBillingService` in `billing/application/usage_billing_service.py`
 Usage-related line items generated by `UsageBillingService` in `packages/billing/src/application/usage-billing-service.ts`

**Related terms:** [Invoice](#invoice), [Invoice Line Item](#invoice-line-item), [Overage](#overage), [Metering Period](#metering-period), [Usage Record](#usage-record)

---

## 4. Payments & Transactions

### Payment

**Definition:** A single monetary transfer from a [Billing Customer](#billing-customer) to the platform. A Payment is the result of processing a [Payment Intent](#payment-intent) through a [Payment Gateway](#payment-gateway).

**Context:** Payments are created for: subscription charges (initial and renewal), one-time mentorship enrollment fees, manual top-ups of [Platform Balance](#platform-balance), and overage charges. Each Payment has a [Payment Status](#payment-status), a source [Payment Method](#payment-method), an [Amount](#money) in a specific [Currency](#currency), and is linked to the [Invoice](#invoice) it settles. A Payment emits a `PaymentCompleted` or `PaymentFailed` [Billing Event](#billing-event) consumed by other contexts (e.g., Learning activates [Enrollment](./learning.md#enrollment) on `PaymentCompleted`).

**Code mapping:**

- Python: `Payment` entity in `billing/domain/payment.py`
 `Payment` class in `packages/billing/src/domain/payment.ts`

**Related terms:** [Payment Status](#payment-status), [Payment Intent](#payment-intent), [Payment Method](#payment-method), [Payment Gateway](#payment-gateway), [Invoice](#invoice), [Money](#money), [Billing Event](#billing-event)

---

### Payment Status

**Definition:** An enum representing the current state of a [Payment](#payment). Values: `Pending` (created, not yet submitted to gateway), `Processing` (submitted to [Payment Gateway](#payment-gateway), awaiting confirmation), `Completed` (funds received), `Failed` (gateway declined or error), `Cancelled` (voided before processing).

**Context:** Status transitions: `Pending` → `Processing` (submitted to gateway) → `Completed` | `Failed`. `Pending` → `Cancelled` (voided before submission). `Failed` payments may trigger automatic retry (for subscription renewals) or require manual intervention. The number of retry attempts and backoff schedule are configurable. After all retries are exhausted, the associated [Subscription](#subscription) transitions to `PastDue` or `Expired`.

**Code mapping:**

- Python: `PaymentStatus` enum in `billing/domain/payment_status.py`
 `PaymentStatus` union type in `packages/billing/src/domain/payment-status.ts`

**Related terms:** [Payment](#payment), [Payment Gateway](#payment-gateway), [Subscription Status](#subscription-status)

---

### Transaction

**Definition:** An immutable record in the financial ledger representing any movement of money within a [Billing Account](#billing-account). Every financial operation — charge, refund, payout, credit, adjustment — creates a Transaction.

**Context:** Transactions are the audit trail of all financial activity. They are append-only: once created, a Transaction cannot be modified or deleted. Corrections are made by creating compensating transactions (e.g., a refund transaction offsets a charge transaction). Each Transaction records: type ([Transaction Type](#transaction-type)), amount ([Money](#money)), balance after transaction, related entity (payment ID, refund ID, payout ID), timestamp, and description. The sum of all transactions for an account equals the current account balance.

**Code mapping:**

- Python: `Transaction` entity in `billing/domain/transaction.py`
 `Transaction` class in `packages/billing/src/domain/transaction.ts`

**Related terms:** [Transaction Type](#transaction-type), [Billing Account](#billing-account), [Money](#money), [Payment](#payment), [Refund](#refund)

---

### Transaction Type

**Definition:** An enum classifying the nature of a [Transaction](#transaction). Values: `Charge` (money owed by customer — subscription, purchase, overage), `Refund` (money returned to customer), `Payout` (money sent to a master), `Credit` (bonus/compensation added to account), `Adjustment` (manual correction by platform admin).

**Context:** Transaction Type determines how the transaction affects the account balance: `Charge` increases the amount owed (or decreases prepaid balance); `Refund` and `Credit` increase the available balance; `Payout` records money leaving the platform to a master; `Adjustment` can go either direction and requires admin authorization with a mandatory reason field.

**Code mapping:**

- Python: `TransactionType` enum in `billing/domain/transaction_type.py`
 `TransactionType` union type in `packages/billing/src/domain/transaction-type.ts`

**Related terms:** [Transaction](#transaction), [Payment](#payment), [Refund](#refund), [Credit](#credit), [Master Payout](#master-payout)

---

### Payment Intent

**Definition:** A domain object representing the intention to collect a specific amount from a [Billing Customer](#billing-customer) before the actual charge is processed. A Payment Intent captures: the amount ([Money](#money)), target [Payment Method](#payment-method), reason (subscription renewal, enrollment fee, top-up), and associated [Invoice](#invoice).

**Context:** Payment Intents decouple the decision to charge from the actual charge execution. They are created by application-layer use cases (e.g., `RenewSubscriptionUseCase` creates a Payment Intent) and then processed by the [Payment Gateway](#payment-gateway) adapter. This two-phase approach allows: validation before charging, support for asynchronous payment flows (crypto confirmation), and idempotent retry on failure. A Payment Intent transitions to a [Payment](#payment) upon gateway submission.

**Code mapping:**

- Python: `PaymentIntent` entity in `billing/domain/payment_intent.py`
 `PaymentIntent` class in `packages/billing/src/domain/payment-intent.ts`

**Related terms:** [Payment](#payment), [Payment Method](#payment-method), [Invoice](#invoice), [Payment Gateway](#payment-gateway), [Money](#money)

---

### Payment Gateway

**Definition:** A driven port (interface defined in the domain, implemented in infrastructure) that abstracts the communication with external payment processors. The domain calls the gateway to process charges, verify payment methods, and handle refunds — without knowing the specifics of the underlying provider.

**Context:** Multiple Payment Gateway implementations can coexist: a card processor (e.g., Stripe), a crypto processor (e.g., Coinbase Commerce), and an internal processor for [Platform Balance](#platform-balance) deductions. The gateway is selected based on the [Payment Method Type](#payment-method-type) at processing time. Gateway adapters live in the infrastructure layer and implement the domain-defined interface — this is the [Dependency Inversion Principle](../AGENTS.md#35-d--dependency-inversion-principle-dip) in action. Gateway responses are translated into domain events through the Anti-Corruption Layer.

**Code mapping:**

- Python: `PaymentGateway` Protocol in `billing/domain/payment_gateway.py`, implemented by `StripeGateway`, `CryptoGateway`, `BalanceGateway` in `billing/infrastructure/`
 `PaymentGateway` interface in `packages/billing/src/domain/payment-gateway.ts`, implemented in `packages/billing/src/infrastructure/`

**Related terms:** [Payment](#payment), [Payment Method Type](#payment-method-type), [Refund](#refund), [Billing Event](#billing-event)

---

### Currency

**Definition:** An ISO 4217 currency code (e.g., `USD`, `EUR`, `BTC`, `ETH`) identifying the denomination of a monetary value. All financial operations in the Billing context explicitly specify the Currency.

**Context:** The platform may support multiple currencies. Each [Billing Customer](#billing-customer) has a preferred Currency set at account creation. [Plans](#plan) may be priced in multiple currencies. Cross-currency transactions require conversion, which is handled at the infrastructure layer using exchange rates from an external provider (driven port). Crypto currencies (`BTC`, `ETH`, etc.) are treated as first-class currencies alongside fiat, with the same domain model — the difference is only in the [Payment Gateway](#payment-gateway) adapter used.

**Code mapping:**

- Python: `Currency` value object (branded `str`) in `billing/domain/currency.py`
 `Currency` branded type in `packages/billing/src/domain/currency.ts`

**Related terms:** [Money](#money), [Payment](#payment), [Billing Customer](#billing-customer)

---

### Money

**Definition:** A value object representing a monetary amount paired with a [Currency](#currency). All financial calculations, comparisons, and storage in the Billing context use Money — never raw numeric values.

**Context:** Money encapsulates: an integer amount in the smallest currency unit (cents for USD, satoshis for BTC) and a Currency code. This prevents floating-point errors and ensures currency mismatches are caught at compile/runtime. Arithmetic operations on Money (add, subtract, multiply) enforce that both operands share the same Currency — cross-currency operations require explicit conversion. Money is immutable.

**Code mapping:**

- Python: `Money` frozen dataclass in `billing/domain/money.py`
 `Money` readonly interface in `packages/billing/src/domain/money.ts`

**Related terms:** [Currency](#currency), [Transaction](#transaction), [Payment](#payment), [Invoice Line Item](#invoice-line-item)

---

## 5. Invoices & Documents

### Invoice

**Definition:** A formal financial document itemizing charges owed by a [Billing Customer](#billing-customer) for a specific billing period or one-time purchase. An Invoice contains one or more [Invoice Line Items](#invoice-line-item), applicable [Discounts](#discount), tax amounts, and a total due.

**Context:** Invoices are generated automatically: at subscription renewal (covering the next cycle's base price + previous cycle's overage), at mentorship enrollment (one-time charge), and for manual charges. Each Invoice has a unique sequential number, issue date, due date, and [Invoice Status](#invoice-status). Invoices are the legal billing documents — they are immutable once issued. Corrections are handled via [Credit Notes](#credit-note). Invoices are stored as domain entities; the PDF rendering is an infrastructure concern (driven port).

**Code mapping:**

- Python: `Invoice` entity in `billing/domain/invoice.py`
 `Invoice` class in `packages/billing/src/domain/invoice.ts`

**Related terms:** [Invoice Line Item](#invoice-line-item), [Invoice Status](#invoice-status), [Billing Customer](#billing-customer), [Payment](#payment), [Discount](#discount), [Credit Note](#credit-note)

---

### Invoice Line Item

**Definition:** A single entry on an [Invoice](#invoice) describing one charge: description, quantity, unit price ([Money](#money)), applicable [Discount](#discount), and line total.

**Context:** Line items represent individual charges: "Professional Plan — Monthly" (1 × $49), "Additional seats — 3 seats" (3 × $10), "Mentorship enrollment — Advanced Plumbing" (1 × $200), "Storage overage — 2.5 GB" (2.5 × $0.10). Each line item may have a Discount applied (from a [Coupon](#coupon) or [Promo Code](#promo-code)). The sum of all line items (after discounts and tax) equals the invoice total.

**Code mapping:**

- Python: `InvoiceLineItem` value object in `billing/domain/invoice_line_item.py`
 `InvoiceLineItem` interface in `packages/billing/src/domain/invoice-line-item.ts`

**Related terms:** [Invoice](#invoice), [Money](#money), [Discount](#discount), [Overage](#overage)

---

### Invoice Status

**Definition:** An enum representing the current state of an [Invoice](#invoice). Values: `Draft` (being prepared, not yet finalized), `Issued` (finalized and sent to customer, awaiting payment), `Paid` (payment received in full), `Overdue` (past due date, payment not received), `Void` (cancelled — replaced by a corrected invoice or [Credit Note](#credit-note)).

**Context:** Status transitions: `Draft` → `Issued` (finalized) → `Paid` (payment completed) | `Overdue` (due date passed). `Overdue` → `Paid` (late payment received). `Issued` | `Overdue` → `Void` (invoice cancelled). `Void` invoices are preserved for audit but are no longer collectible. A `Paid` invoice cannot be voided — corrections require a [Credit Note](#credit-note) and optional [Refund](#refund).

**Code mapping:**

- Python: `InvoiceStatus` enum in `billing/domain/invoice_status.py`
 `InvoiceStatus` union type in `packages/billing/src/domain/invoice-status.ts`

**Related terms:** [Invoice](#invoice), [Payment](#payment), [Credit Note](#credit-note), [Refund](#refund)

---

### Credit Note

**Definition:** A financial document that partially or fully reverses a previously [Issued](#invoice-status) or [Paid](#invoice-status) [Invoice](#invoice). A Credit Note records the refunded or credited amount, the reason, and the affected invoice line items.

**Context:** Credit Notes are used when an invoice was incorrect (wrong amount, duplicate charge) or when a customer is entitled to a partial credit (e.g., prorated refund for plan downgrade mid-cycle). A Credit Note can result in: (1) a [Refund](#refund) to the original payment method, (2) a [Credit](#credit) added to the customer's [Billing Account](#billing-account), or (3) both. Credit Notes have their own sequential numbering and are linked to the original invoice. They are immutable once issued.

**Code mapping:**

- Python: `CreditNote` entity in `billing/domain/credit_note.py`
 `CreditNote` class in `packages/billing/src/domain/credit-note.ts`

**Related terms:** [Invoice](#invoice), [Refund](#refund), [Credit](#credit), [Invoice Status](#invoice-status)

---

### Receipt

**Definition:** A confirmation document generated after a [Payment](#payment) is successfully completed. Serves as proof of payment for the [Billing Customer](#billing-customer).

**Context:** Receipts are simpler than Invoices — they confirm that money was received rather than itemizing charges. Each Receipt references the [Payment](#payment) ID, the amount, the [Payment Method](#payment-method) used (masked), the date, and the associated [Invoice](#invoice) number. Receipts are generated automatically on `PaymentCompleted` events. They are sent to the customer via email and available in the billing dashboard. Like invoices, the PDF rendering is an infrastructure concern.

**Code mapping:**

- Python: `Receipt` entity in `billing/domain/receipt.py`
 `Receipt` class in `packages/billing/src/domain/receipt.ts`

**Related terms:** [Payment](#payment), [Invoice](#invoice), [Billing Customer](#billing-customer)

---

## 6. Refunds, Credits & Promotions

### Refund

**Definition:** A reversal of a previous [Payment](#payment), returning funds to the [Billing Customer](#billing-customer)'s original [Payment Method](#payment-method). Refunds can be full (entire payment amount) or partial (a portion of the payment).

**Context:** Refunds are initiated by platform admins, automated policies, or customer request (subject to [Refund Policy](#refund-policy)). Each Refund is linked to the original Payment and creates a [Transaction](#transaction) of type `Refund`. The refund is processed through the same [Payment Gateway](#payment-gateway) that handled the original payment. For crypto payments, refunds go to the originating wallet address. For [Platform Balance](#platform-balance) payments, the balance is restored. Refunds emit a `RefundProcessed` [Billing Event](#billing-event).

**Code mapping:**

- Python: `Refund` entity in `billing/domain/refund.py`
 `Refund` class in `packages/billing/src/domain/refund.ts`

**Related terms:** [Payment](#payment), [Refund Policy](#refund-policy), [Transaction](#transaction), [Credit Note](#credit-note), [Payment Gateway](#payment-gateway), [Billing Event](#billing-event)

---

### Refund Policy

**Definition:** A set of rules governing when and how [Refunds](#refund) are granted. Defines: the refund window (e.g., "within 14 days of payment"), eligible scenarios (cancellation, dissatisfaction, platform error), refund type (full/partial), and whether the refund goes to the payment method or as [Credit](#credit).

**Context:** Refund Policies are platform-defined and may vary by product type: subscription charges may have a different policy than mentorship enrollment fees. The domain enforces the policy — a refund request that violates the policy is rejected. Exceptional refunds (outside policy) require admin override with a mandatory reason. The policy is a domain service, not a data entity.

**Code mapping:**

- Python: `RefundPolicy` domain service in `billing/domain/refund_policy.py`
 `RefundPolicy` domain service in `packages/billing/src/domain/refund-policy.ts`

**Related terms:** [Refund](#refund), [Payment](#payment), [Credit](#credit)

---

### Credit

**Definition:** A non-cash monetary value added to a [Billing Customer](#billing-customer)'s [Billing Account](#billing-account) that can be used to pay for future charges. Credits reduce the amount charged to external [Payment Methods](#payment-method).

**Context:** Credits are added for various reasons tracked by [Credit Source](#credit-source): promotional bonuses, compensation for service issues, referral rewards from the Partnership context, or manual adjustments by admins. Credits are applied automatically at payment time: when a [Payment Intent](#payment-intent) is created, the system checks available credit balance and deducts from it first, then charges the remainder to the [Default Payment Method](#default-payment-method). Credits may have an expiry date (e.g., promotional credits expire in 90 days). Credits create a [Transaction](#transaction) of type `Credit`.

**Code mapping:**

- Python: `Credit` entity in `billing/domain/credit.py`
 `Credit` class in `packages/billing/src/domain/credit.ts`

**Related terms:** [Credit Source](#credit-source), [Billing Account](#billing-account), [Transaction](#transaction), [Payment Intent](#payment-intent), [Platform Balance](#platform-balance)

---

### Credit Source

**Definition:** An enum identifying the origin of a [Credit](#credit). Values: `Promotional` (marketing campaign, sign-up bonus), `Compensation` (service issue, downtime, SLA breach), `ReferralBonus` (reward from the [Partnership context](./partnership.md) for a successful referral), `ManualAdjustment` (admin-initiated correction with reason).

**Context:** Credit Source is recorded for audit and analytics: the platform can track how much credit is issued per source, identify abuse patterns (e.g., excessive compensation claims), and measure the effectiveness of promotional campaigns. `ReferralBonus` credits are triggered by events from the Partnership context — when a [Referral Bonus](./partnership.md#referral-bonus) is decided by Partnership, Billing fulfills it by creating a Credit with `ReferralBonus` source.

**Code mapping:**

- Python: `CreditSource` enum in `billing/domain/credit_source.py`
 `CreditSource` union type in `packages/billing/src/domain/credit-source.ts`

**Related terms:** [Credit](#credit), [Billing Event](#billing-event)

---

### Promo Code

**Definition:** A text string that a [Billing Customer](#billing-customer) can enter at checkout to receive a [Discount](#discount) or a [Credit](#credit). Each Promo Code is linked to a [Coupon](#coupon) that defines the actual discount terms.

**Context:** Promo Codes are the distribution mechanism for Coupons. One Coupon can have multiple Promo Codes (e.g., different codes for different marketing channels, affiliate partners, or events). Each Promo Code has: a unique string value, a maximum number of redemptions (or unlimited), an expiry date, and a minimum purchase amount. When redeemed, the code is validated, the associated Coupon is applied to the purchase, and the redemption is recorded. Promo Codes may also grant a [Credit](#credit) instead of a discount (e.g., "$20 credit on sign-up").

**Code mapping:**

- Python: `PromoCode` entity in `billing/domain/promo_code.py`
 `PromoCode` class in `packages/billing/src/domain/promo-code.ts`

**Related terms:** [Coupon](#coupon), [Discount](#discount), [Credit](#credit), [Invoice](#invoice)

---

### Coupon

**Definition:** A discount template that defines the terms of a price reduction: discount type (percentage or fixed amount), value (e.g., 20% or $10), applicable products (all plans, specific plan tiers, mentorship enrollments), duration (one-time, repeating for N cycles, forever), and maximum redemptions.

**Context:** Coupons are the business logic behind discounts — [Promo Codes](#promo-code) are the user-facing redemption mechanism. A Coupon is created by platform admins and linked to one or more Promo Codes. When a Promo Code is redeemed, the system looks up the Coupon and calculates the [Discount](#discount) to apply. Coupons can stack (if the platform allows) or be exclusive (only one per invoice). Expired or fully redeemed Coupons reject new redemption attempts.

**Code mapping:**

- Python: `Coupon` entity in `billing/domain/coupon.py`
 `Coupon` class in `packages/billing/src/domain/coupon.ts`

**Related terms:** [Promo Code](#promo-code), [Discount](#discount), [Invoice Line Item](#invoice-line-item), [Plan](#plan)

---

### Discount

**Definition:** The calculated price reduction applied to an [Invoice Line Item](#invoice-line-item) as a result of redeeming a [Coupon](#coupon) or [Promo Code](#promo-code). A Discount records: the original price, the discount amount, and the final price after reduction.

**Context:** Discounts are computed values, not standalone entities — they exist as part of an Invoice Line Item. A Discount references the Coupon that generated it (for audit). The calculation depends on the Coupon type: percentage discounts are applied to the line item total; fixed-amount discounts reduce the total by the specified amount (but never below zero). If multiple coupons apply, the order of application matters and is defined by platform rules (e.g., percentage first, then fixed).

**Code mapping:**

- Python: `Discount` value object in `billing/domain/discount.py`
 `Discount` interface in `packages/billing/src/domain/discount.ts`

**Related terms:** [Coupon](#coupon), [Promo Code](#promo-code), [Invoice Line Item](#invoice-line-item), [Money](#money)

---

### Platform Balance

**Definition:** A prepaid fund held within a [Billing Customer](#billing-customer)'s [Billing Account](#billing-account) that can be used as a [Payment Method](#payment-method) for any purchase on the platform. Platform Balance is funded by explicit top-ups (card charge, crypto deposit) and increased by [Credits](#credit) and [Refunds](#refund) that are returned to balance.

**Context:** Platform Balance acts as an internal wallet. Customers can top up their balance and use it for all payments without involving external payment methods each time. When a [Payment Intent](#payment-intent) is processed, the system checks Platform Balance first: if sufficient, the entire amount is deducted from the balance; if insufficient, the balance is used partially and the remainder is charged to another [Payment Method](#payment-method). Platform Balance is denominated in the customer's preferred [Currency](#currency). It is always non-negative — charges that would result in a negative balance are rejected.

**Code mapping:**

- Python: Balance tracked as a property on `BillingAccount` in `billing/domain/billing_account.py`
 Balance tracked as a property on `BillingAccount` in `packages/billing/src/domain/billing-account.ts`

**Related terms:** [Billing Account](#billing-account), [Payment Method Type](#payment-method-type), [Credit](#credit), [Payment Intent](#payment-intent), [Money](#money)

---

## 7. Master Payouts

### Master Payout

**Definition:** A monetary transfer from the platform to a [Master](./learning.md#master) for teaching services rendered. Calculated based on completed [Mentorships](./learning.md#mentorship), [Apprenticeship Sessions](./learning.md#apprenticeship-session), and/or enrollment fees — minus the [Platform Commission](#platform-commission).

**Context:** Master Payouts are the "outgoing" side of the billing flow. When a [Learner](./learning.md#learner) pays for a mentorship, the platform retains a [Platform Commission](#platform-commission) and the remainder is allocated to the Master's [Payout Account](#payout-account). Payouts are not instant — they follow the [Payout Schedule](#payout-schedule) and are subject to hold periods (to allow for refunds). Each payout creates a [Transaction](#transaction) of type `Payout` and emits a `PayoutCompleted` [Billing Event](#billing-event).

**Code mapping:**

- Python: `MasterPayout` entity in `billing/domain/master_payout.py`
 `MasterPayout` class in `packages/billing/src/domain/master-payout.ts`

**Related terms:** [Payout Schedule](#payout-schedule), [Payout Status](#payout-status), [Platform Commission](#platform-commission), [Payout Account](#payout-account), [Transaction](#transaction), [Billing Event](#billing-event)

**Not to be confused with:** [Payout](./partnership.md#payout) in the Partnership context — Partner payouts (referral commissions) are managed entirely within the Partnership context with its own [Partner Balance](./partnership.md#partner-balance) and payout logic. Master Payouts (teaching fees) are managed here in Billing.

---

### Payout Schedule

**Definition:** The cadence at which accumulated [Master Payout](#master-payout) earnings are disbursed to the [Master](./learning.md#master)'s [Payout Account](#payout-account). Values: `Weekly`, `Biweekly`, `Monthly`, `OnThreshold` (payout triggered when accumulated amount reaches a minimum).

**Context:** Payout Schedule is configured per Master (within platform-allowed options). The schedule determines when the system sweeps accumulated earnings and initiates the transfer. Each payout cycle: (1) calculates total earnings since last payout, (2) subtracts [Platform Commission](#platform-commission), (3) checks that the net amount meets the minimum payout threshold, (4) creates a Master Payout record, (5) submits to the [Payment Gateway](#payment-gateway) for disbursement. `OnThreshold` is useful for masters with irregular earnings — they get paid as soon as they reach the minimum rather than waiting for a fixed date.

**Code mapping:**

- Python: `PayoutSchedule` enum in `billing/domain/payout_schedule.py`
 `PayoutSchedule` union type in `packages/billing/src/domain/payout-schedule.ts`

**Related terms:** [Master Payout](#master-payout), [Platform Commission](#platform-commission), [Payout Account](#payout-account)

---

### Payout Status

**Definition:** An enum representing the current state of a [Master Payout](#master-payout). Values: `Pending` (calculated, awaiting processing), `Processing` (submitted to payment gateway/bank), `Completed` (funds transferred successfully), `Failed` (transfer rejected — wrong account, insufficient platform funds), `OnHold` (blocked by platform — pending review, refund window, or compliance check).

**Context:** Status transitions: `Pending` → `Processing` (submitted) → `Completed` | `Failed`. `Pending` → `OnHold` (flagged for review). `OnHold` → `Processing` (released) | `Cancelled` (payout cancelled, funds returned to master's accumulated balance). Failed payouts are retried automatically (up to a configured limit); after exhausting retries, the payout stays in `Failed` and requires admin intervention or updated [Payout Account](#payout-account) details.

**Code mapping:**

- Python: `PayoutStatus` enum in `billing/domain/payout_status.py`
 `PayoutStatus` union type in `packages/billing/src/domain/payout-status.ts`

**Related terms:** [Master Payout](#master-payout), [Payout Account](#payout-account), [Payment Gateway](#payment-gateway)

---

### Platform Commission

**Definition:** The percentage or fixed fee that the platform retains from each [Payment](#payment) made by a [Learner](./learning.md#learner) before the remainder is allocated as a [Master Payout](#master-payout). The commission is the platform's revenue from the marketplace.

**Context:** Platform Commission is configured globally (default rate) with optional per-[Master](./learning.md#master) overrides (e.g., top-rated masters get a lower commission rate as an incentive). The commission is calculated at payment time and recorded as a separate [Transaction](#transaction). Examples: "Platform takes 20% of each mentorship payment" — a $100 enrollment results in $80 allocated to the Master and $20 retained by the platform. Commission rates may vary by product (mentorship enrollment vs. apprenticeship session fees). Commission changes apply to future payments only, not retroactively.

**Code mapping:**

- Python: `PlatformCommission` value object in `billing/domain/platform_commission.py`
 `PlatformCommission` interface in `packages/billing/src/domain/platform-commission.ts`

**Related terms:** [Master Payout](#master-payout), [Payment](#payment), [Transaction](#transaction)

**Not to be confused with:** [Commission](./partnership.md#commission) in the Partnership context — Partnership Commissions are referral rewards earned by Partners for bringing new users. Platform Commission is the platform's cut from master-learner transactions.

---

### Payout Account

**Definition:** The financial destination where a [Master](./learning.md#master) receives their [Master Payouts](#master-payout). Contains: bank account details (for bank transfers), card details (for card payouts), or a crypto wallet address — depending on the master's preferred payout method.

**Context:** Each Master must configure a Payout Account before they can receive earnings. Sensitive details (full account numbers, wallet private keys) are stored securely — the domain holds only a tokenized reference and display-safe identifiers (last 4 digits, wallet address prefix). Payout Account verification may be required before the first payout (bank account micro-deposits, crypto address ownership proof). A Master can have multiple Payout Accounts but only one is active for disbursements at any time.

**Code mapping:**

- Python: `PayoutAccount` entity in `billing/domain/payout_account.py`
 `PayoutAccount` class in `packages/billing/src/domain/payout-account.ts`

**Related terms:** [Master Payout](#master-payout), [Payout Status](#payout-status), [Payment Gateway](#payment-gateway)

---

## Cross-Context Boundary Notes

The Billing & Payments bounded context interacts with other contexts through explicit contracts. The following table clarifies term boundaries:

| Billing Context Term | Other Context | Their Term | Relationship |
|---|---|---|---|
| `Billing Customer` | Auth | [`AuthUser`](./auth.md#authuser) | Linked via `IdentityId`. Billing owns financial data, payment methods, and transaction history; Auth owns credentials, sessions, and system-wide roles. |
| `Subscription` / `Plan` | Project | [`Member Limit`](./project.md#member-limit), [`Seat`](./project.md#seat), [`Project Quota`](./project.md#project-quota) | Billing defines plan limits (seats, storage, quotas) and charges for them. Project context stores limits locally (via ACL) and enforces them. Billing emits `SubscriptionCreated`, `PlanChanged` events; Project subscribes. |
| `Payment` | Learning | [`Enrollment`](./learning.md#enrollment), [`Mentorship Agreement`](./learning.md#mentorship-agreement) | Learning emits `EnrollmentPaymentRequested` with amount and mentorship details. Billing processes the payment and emits `PaymentCompleted` or `PaymentFailed`. Learning subscribes and activates/rejects the enrollment accordingly. |
| `Master Payout` | Learning | [`Master`](./learning.md#master), [`Mentorship`](./learning.md#mentorship) | Learning reports completed mentorships and sessions via events. Billing calculates the master's earnings, deducts [Platform Commission](#platform-commission), and executes the payout on schedule. |
| `Credit` (`ReferralBonus`) | Partnership | [`Referral Bonus`](./partnership.md#referral-bonus) | Partnership decides the bonus amount and recipient. Billing fulfills it by creating a Credit with `ReferralBonus` source on the referred user's account. Partnership emits `ReferralBonusGranted`; Billing subscribes. |
| `Coupon` | Partnership | [`Referral Bonus`](./partnership.md#referral-bonus) | Partnership may issue discount coupons for referred users. Partnership emits an event; Billing creates and associates the Coupon. |
| `Usage Record` | Project | [`Membership Event`](./project.md#membership-event), [`Capacity Event`](./project.md#capacity-event) | Project emits events when seat count changes or storage is consumed. Billing receives them and creates Usage Records for metering. |
| `Billing Event` | Monitoring | `Alert`, `Metric` | Billing emits financial events (`PaymentFailed`, `SubscriptionExpired`, `PayoutCompleted`). Monitoring context consumes them for dashboards, alerting, and business analytics. |

**Integration rules:**

- Other contexts MUST NOT import Billing domain models directly. Use events or API contracts.
- Billing MUST NOT contain business logic from other contexts. The rule "a learner cannot enroll without payment" is expressed as: Learning emits `EnrollmentPaymentRequested`, Billing processes it, Learning activates enrollment only on `PaymentCompleted`. Billing does not know what an Enrollment is.
- The Learning context MUST NOT access Billing's database to check payment status. Payment status flows via events.
- The Project context receives plan limits via `SubscriptionCreated` / `PlanChanged` events and stores them locally through its Anti-Corruption Layer (see [AGENTS.md 4.3](../AGENTS.md#43-context-mapping-карта-контекстов)). Project does NOT query Billing for current plan details.
- Partner payouts are NOT processed by Billing. The Partnership context manages its own [Partner Balance](./partnership.md#partner-balance), [Payout](./partnership.md#payout), and payout infrastructure independently. This separation exists because partner commissions have different calculation rules, hold periods, and compliance requirements than master teaching fees.
- All monetary values crossing context boundaries MUST use the [Money](#money) value object (amount in smallest unit + currency code). Never pass raw numbers.
- Sensitive payment data (card numbers, CVV, crypto keys) MUST NOT appear in domain events or cross-context contracts. Only tokenized references and display-safe identifiers (last 4 digits, masked wallet address) are permitted.
