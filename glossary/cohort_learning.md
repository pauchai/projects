# Cohort Learning — Ubiquitous Language Glossary

This glossary defines the authoritative vocabulary for the **Cohort Learning** bounded context. All code, documentation, API contracts, and team communication within this context MUST use these terms consistently.

**Bounded Context scope:** Cohort-based group learning, progressive learner advancement (Learner → Topic Expert → Module Curator → Master), hybrid reward system (reputation-based and monetary), peer-assisted mentoring, and coordination with the [Learning & Mentorship](./learning.md), [Projects & Members](./project.md), and [Partnership & Referral Program](./partnership.md) bounded contexts.

**Context role:** This is a **self-contained bounded context** that owns cohort lifecycle, learner progression, competency validation, peer review, and the hybrid reward system. It communicates with other contexts through domain events and API contracts via **Anti-Corruption Layers** — no context imports another's domain models directly. When workspace infrastructure is needed (V2+), this context acts as a **Customer** to the Projects context (Supplier) following the Customer–Supplier pattern.

**MVP scope:** Version 1.0 operates with a single [Module](#module-progression), a single active [Cohort](#learning-cohort) per module, and one [Master](./learning.md#master) per cohort. Project integration (workspace, membership sync) is deferred to V2. The architecture explicitly supports future evolution to multiple modules, parallel cohorts, project integration, internships, and a module marketplace.

**Code mapping convention:**

- Python: `cohort_learning/domain/` for domain models, `cohort_learning/application/` for use cases, `cohort_learning/infrastructure/` for adapters

**Cross-context dependencies:** This context references identities from the [Auth bounded context](./auth.md) via `IdentityId`. It publishes domain events that may be consumed by [Partnership & Referral Program](./partnership.md), [Learning & Mentorship](./learning.md), [Projects & Members](./project.md), and [Billing](./billing.md). Each context maintains its own domain models — no shared aggregates.

---

## 1. Cohort & Group Learning

### Learning Cohort

**Definition:** A time-bounded group of 5–15 [Learners](./learning.md#learner) who study a single [Module](#module-progression) together under the guidance of a [Master](./learning.md#master). A Learning Cohort is the primary organizational unit for group-based education in this context.

**Context:** A Cohort is formed when a Master opens enrollment for a module and enough learners sign up. Each Cohort has a [Cohort Status](#cohort-status), a start date, an end date (estimated), and a linked [Learning Project](#learning-project) that serves as the shared workspace. Learners within a Cohort progress through [Topics](#topic) at their own pace but share the same workspace, participate in [Peer Review](#peer-review), and can help each other. A Cohort is always supervised by exactly one Master in V1 (future versions may support co-teaching).

**Code mapping:**

- Python: `LearningCohort` aggregate root in `cohort_learning/domain/learning_cohort.py`

**Related terms:** [Cohort Status](#cohort-status), [Cohort Membership](#cohort-membership), [Learning Project](#learning-project), [Module Progression](#module-progression), [Topic](#topic)

**Not to be confused with:** A [Learning Program](./learning.md#learning-program) in the Learning context (a full syllabus created by a Master — a Cohort studies one module of a program), or a [Project](./project.md#project) in the Projects context (a general-purpose workspace — a Learning Project is a Project with educational semantics applied by the Cohort Learning context).

---

### Cohort Status

**Definition:** An enum representing the current lifecycle phase of a [Learning Cohort](#learning-cohort). Values: `Forming`, `Active`, `Completing`, `Graduated`, `Cancelled`.

**Context:** Status governs which operations are permitted:
- `Forming` — enrollment is open, the Master is assembling the group. The [Learning Project](#learning-project) is created but in [Draft](./project.md#draft-state) state. Learners can join but formal learning has not started.
- `Active` — learning is in progress. The Learning Project is [Active](./project.md#active-state). Learners work through [Topics](#topic), submit [Practice Tasks](#practice-task), and participate in [Peer Review](#peer-review). [Topic Expert](#topic-expert) promotions can occur.
- `Completing` — the module end date is approaching or all learners have finished. Final assessments and evaluations are in progress.
- `Graduated` — the Cohort has completed the module. The Learning Project transitions to [Completed](./project.md#completed-state). [Module Curators](#module-curator) may be promoted from graduating learners. A `CohortGraduated` [Domain Event](#domain-event) is emitted.
- `Cancelled` — the Cohort was disbanded before completion (insufficient enrollment, Master unavailable). Learners are notified and may transfer to another Cohort.

**Code mapping:**

- Python: `CohortStatus` enum in `cohort_learning/domain/cohort_status.py`

**Related terms:** [Learning Cohort](#learning-cohort), [Domain Event](#domain-event)

---

### Cohort Membership

**Definition:** The relationship entity that binds a [Learner](./learning.md#learner) to a [Learning Cohort](#learning-cohort). Encapsulates the learner's current [Cohort Role](#cohort-role), join date, and progress within the cohort.

**Context:** Cohort Membership is a first-class domain concept. It is created when a learner enrolls into a cohort and tracks their journey through the module. Each Membership maps to a [Membership](./project.md#membership) in the linked [Learning Project](#learning-project) — the ACL ensures role synchronization (e.g., when a learner becomes a [Topic Expert](#topic-expert), their Project role is updated accordingly). A learner can be a member of only one active Cohort at a time in V1.

**Code mapping:**

- Python: `CohortMembership` entity in `cohort_learning/domain/cohort_membership.py`

**Related terms:** [Learning Cohort](#learning-cohort), [Cohort Role](#cohort-role), [Learning Project](#learning-project)

---

### Cohort Role

**Definition:** An enum that classifies a participant's level of responsibility and access within a [Learning Cohort](#learning-cohort). Values: `Learner`, `Topic Expert`, `Module Curator`, `Master`.

**Context:** Cohort Roles represent the progressive advancement within the educational process. Unlike static [Project Roles](./project.md#project-role), Cohort Roles are **earned through demonstrated competency** and change over the lifecycle of a cohort and beyond:
- `Learner` — the default role. Working through topics, submitting tasks, participating in peer review.
- `Topic Expert` — earned by demonstrating mastery of a specific [Topic](#topic). Can help other learners with that topic, validate [Practice Tasks](#practice-task), and participate as a [Peer Helper](#peer-helper). See [Topic Expert](#topic-expert) for full details.
- `Module Curator` — earned after completing the entire module with satisfactory results. Can curate future cohorts, create practice tasks, and evaluate topic mastery. See [Module Curator](#module-curator) for full details.
- `Master` — the cohort's teacher. Creates the module, leads the cohort, evaluates learners, and promotes Topic Experts and Module Curators.

Each Cohort Role maps to a [Project Role](./project.md#project-role) in the linked Learning Project via the [Role Mapping](#role-mapping).

**Code mapping:**

- Python: `CohortRole` enum in `cohort_learning/domain/cohort_role.py`

**Related terms:** [Cohort Membership](#cohort-membership), [Topic Expert](#topic-expert), [Module Curator](#module-curator), [Role Mapping](#role-mapping)

---

### Role Mapping

**Definition:** A configuration that defines how [Cohort Roles](#cohort-role) translate to [Project Roles](./project.md#project-role) in the linked [Learning Project](#learning-project). The Role Mapping is enforced by the Anti-Corruption Layer when synchronizing membership between contexts.

**Context:** Default mapping:

| Cohort Role | Project Role | Project Permissions |
|---|---|---|
| `Learner` | [Viewer](./project.md#viewer-role) | `view_content` |
| `Topic Expert` | [Member](./project.md#member-role) | `view_content`, `edit_content` |
| `Module Curator` | [Member](./project.md#member-role) | `view_content`, `edit_content` |
| `Master` | [Owner](./project.md#owner) | All permissions |

Role Mapping is unidirectional: changes in Cohort Role trigger Project Role updates, never the reverse. The Cohort Learning context owns this mapping; the Projects context is unaware of educational semantics.

**Code mapping:**

- Python: `RoleMapping` value object in `cohort_learning/domain/role_mapping.py`

**Related terms:** [Cohort Role](#cohort-role), [Learning Project](#learning-project)

---

## 2. Module & Topic Structure

### Module Progression

**Definition:** The structured, ordered sequence of [Topics](#topic) that a [Learning Cohort](#learning-cohort) studies. A Module Progression defines what learners must complete, in what order, and what constitutes mastery of each topic.

**Context:** In V1, a module is a flat ordered list of Topics. Each Topic contains [Practice Tasks](#practice-task) and has a [Topic Competency](#topic-competency) threshold that determines when a learner has mastered it. Module Progression is the simplified equivalent of a [Learning Program](./learning.md#learning-program) — it replaces the complex Lesson/Module hierarchy from the Learning context with a lighter, task-based structure optimized for cohort-based group learning. A module is authored by the [Master](./learning.md#master) and versioned — changes to a module create a new version, while active Cohorts continue with their original version.

**Code mapping:**

- Python: `ModuleProgression` entity in `cohort_learning/domain/module_progression.py`

**Related terms:** [Topic](#topic), [Learning Cohort](#learning-cohort), [Topic Competency](#topic-competency), [Practice Task](#practice-task)

**Not to be confused with:** [Module](./learning.md#module) in the Learning context (an optional grouping of Lessons — our Module Progression is a standalone educational unit), or [Learning Program](./learning.md#learning-program) (a full multi-module curriculum — our Module Progression is a single module within such a curriculum).

---

### Topic

**Definition:** A discrete unit of knowledge within a [Module Progression](#module-progression). Each Topic covers a single concept or skill (e.g., "React Hooks," "REST API Design," "Database Normalization") and has associated [Practice Tasks](#practice-task) and a [Topic Competency](#topic-competency) threshold.

**Context:** Topics are ordered within a module and may have prerequisites (a learner must demonstrate [Topic Competency](#topic-competency) in Topic A before starting Topic B). Each Topic has: a title, a description, attached [Learning Materials](./learning.md#learning-material) (theory — PDFs, videos, articles), and one or more Practice Tasks (practical application). A learner's progress through a Topic is measured by completing its Practice Tasks and passing the competency validation. When a learner achieves Topic Competency, they become eligible for [Topic Expert](#topic-expert) status for that specific topic.

**Code mapping:**

- Python: `Topic` entity in `cohort_learning/domain/topic.py`

**Related terms:** [Module Progression](#module-progression), [Practice Task](#practice-task), [Topic Competency](#topic-competency), [Topic Expert](#topic-expert)

---

### Topic Competency

**Definition:** A validated confirmation that a [Learner](./learning.md#learner) has demonstrated sufficient understanding and practical skill in a specific [Topic](#topic). Topic Competency is the gateway to the [Topic Expert](#topic-expert) role.

**Context:** Competency is assessed through a multi-step [Competency Validation](#competency-validation) process: completing all required [Practice Tasks](#practice-task) for the topic, passing an automated knowledge check (quiz or test), and receiving a satisfactory [Peer Review](#peer-review) on submitted work. The [Master](./learning.md#master) or an existing [Module Curator](#module-curator) provides the final approval. Topic Competency is topic-specific and version-specific — competency in "React Hooks v1" does not automatically grant competency in "React Hooks v2" if the topic content changed significantly.

**Code mapping:**

- Python: `TopicCompetency` entity in `cohort_learning/domain/topic_competency.py`

**Related terms:** [Topic](#topic), [Topic Expert](#topic-expert), [Competency Validation](#competency-validation), [Practice Task](#practice-task)

---

### Competency Validation

**Definition:** The structured process of confirming that a [Learner](./learning.md#learner) has achieved [Topic Competency](#topic-competency) in a specific [Topic](#topic). Validation involves multiple steps to ensure genuine understanding, not just task completion.

**Context:** Validation steps (all must pass):
1. **Task Completion** — all required [Practice Tasks](#practice-task) for the topic are submitted and approved.
2. **Knowledge Check** — an automated quiz covering the topic's theoretical concepts. Minimum passing score is configurable per topic (default: 70%).
3. **Peer Review** — at least one [Practice Task](#practice-task) submission reviewed positively by a peer ([Topic Expert](#topic-expert) from the same or previous cohort, or a [Module Curator](#module-curator)).
4. **Mentor Approval** — the [Master](./learning.md#master) or a [Module Curator](#module-curator) confirms readiness based on overall performance.

Validation is recorded as a `TopicCompetencyAchieved` [Domain Event](#domain-event). If validation fails at any step, the learner receives feedback and can retry after addressing the gaps.

**Code mapping:**

- Python: `CompetencyValidation` domain service in `cohort_learning/domain/competency_validation.py`

**Related terms:** [Topic Competency](#topic-competency), [Practice Task](#practice-task), [Peer Review](#peer-review), [Topic Expert](#topic-expert)

---

## 3. Partner Progression

### Topic Expert

**Definition:** A [Learner](./learning.md#learner) who has achieved [Topic Competency](#topic-competency) in one or more [Topics](#topic) and is authorized to help other learners with those specific topics. A Topic Expert is the first level of the partner progression: Learner → **Topic Expert** → [Module Curator](#module-curator) → [Master](./learning.md#master).

**Context:** Topic Expert status is earned per-topic — a learner can be a Topic Expert in "React Hooks" while still a regular learner in "State Management." The status is granted immediately upon passing [Competency Validation](#competency-validation) for the topic. Topic Experts serve as [Peer Helpers](#peer-helper): they answer questions, review practice tasks, and provide guidance to learners studying the topics they've mastered. Topic Expert is a **within-cohort and cross-cohort** role — experts from graduated cohorts can return to help new cohorts with their mastered topics.

**Code mapping:**

- Python: `TopicExpert` entity in `cohort_learning/domain/topic_expert.py`

**Related terms:** [Topic Competency](#topic-competency), [Peer Helper](#peer-helper), [Module Curator](#module-curator), [Cohort Role](#cohort-role), [Expert Reward](#expert-reward)

**Not to be confused with:** [Specialist](./learning.md#learner-status) in the Learning context (a lifecycle stage indicating completion of apprenticeship — Topic Expert is a teaching role, not a lifecycle stage). Also distinct from [Master](./learning.md#master) (who creates and leads programs — a Topic Expert only assists within topics they've mastered).

---

### Peer Helper

**Definition:** The active operational role of a [Topic Expert](#topic-expert) when they are assisting other learners. A Peer Helper answers questions, reviews [Practice Task](#practice-task) submissions, and provides guidance within the scope of their mastered [Topics](#topic).

**Context:** Peer Helper is not a separate status — it is the activity mode of a Topic Expert. A Topic Expert becomes a Peer Helper whenever they engage in helping activities. The system tracks Peer Helper activity for [Expert Rewards](#expert-reward) and [Helper Metrics](#helper-metrics): number of learners helped, questions answered, tasks reviewed, and satisfaction ratings from helped learners. Peer Helper rights are limited to the expert's mastered topics — they cannot review tasks or answer questions on topics where they lack [Topic Competency](#topic-competency).

**Code mapping:**

- Python: `PeerHelper` value object in `cohort_learning/domain/peer_helper.py`

**Related terms:** [Topic Expert](#topic-expert), [Expert Reward](#expert-reward), [Helper Metrics](#helper-metrics), [Peer Review](#peer-review)

---

### Helper Metrics

**Definition:** An aggregated view of a [Peer Helper](#peer-helper)'s activity and effectiveness. Tracks: total learners helped, questions answered, [Practice Tasks](#practice-task) reviewed, average satisfaction rating from helped learners, and response time.

**Context:** Helper Metrics serve three purposes: (1) determining eligibility for [Expert Rewards](#expert-reward), (2) qualifying for [Module Curator](#module-curator) promotion, and (3) building a reputation score that persists across cohorts. Metrics are calculated from [Domain Events](#domain-event) and stored as a read model. A minimum Helper Metrics threshold (e.g., "helped at least 3 learners with average satisfaction ≥ 4.0") is a prerequisite for Module Curator promotion.

**Code mapping:**

- Python: `HelperMetrics` value object in `cohort_learning/domain/helper_metrics.py`

**Related terms:** [Peer Helper](#peer-helper), [Expert Reward](#expert-reward), [Module Curator](#module-curator)

---

### Module Curator

**Definition:** A graduated [Learner](./learning.md#learner) who has completed an entire [Module Progression](#module-progression), achieved [Topic Competency](#topic-competency) across all topics, demonstrated effective [Peer Helper](#peer-helper) activity, and been promoted by the [Master](./learning.md#master) to curate future [Learning Cohorts](#learning-cohort). A Module Curator is the second level of the partner progression: Learner → [Topic Expert](#topic-expert) → **Module Curator** → [Master](./learning.md#master).

**Context:** Module Curator is the bridge between learner and teacher. Curators take on significant responsibilities: they can lead new Cohorts under the Master's supervision, create and modify [Practice Tasks](#practice-task), validate [Topic Competency](#topic-competency) for new learners, and manage [Learning Projects](#learning-project) as Project [Members](./project.md#member-role). A Module Curator is the first level that earns [Monetary Rewards](#monetary-reward) — they receive a commission from the fees paid by learners in cohorts they curate. Curator status is module-specific: a curator for "Frontend Basics" is not automatically a curator for "Backend Architecture." Promotion requires the Master's explicit approval and is recorded as a `CuratorPromoted` [Domain Event](#domain-event).

**Code mapping:**

- Python: `ModuleCurator` entity in `cohort_learning/domain/module_curator.py`

**Related terms:** [Topic Expert](#topic-expert), [Learning Cohort](#learning-cohort), [Curator Promotion](#curator-promotion), [Monetary Reward](#monetary-reward), [Cohort Role](#cohort-role)

**Not to be confused with:** [Master](./learning.md#master) in the Learning context (who creates programs and has full teaching authority — a Curator operates within the Master's program and under the Master's oversight), or [Owner](./project.md#owner) in the Projects context (who has full control over a project — a Curator has elevated but limited project permissions).

---

### Curator Promotion

**Definition:** The validated process of advancing a [Topic Expert](#topic-expert) to [Module Curator](#module-curator) status. Promotion is a significant milestone that unlocks teaching responsibilities and [Monetary Rewards](#monetary-reward).

**Context:** Promotion requirements (all must be met):
1. **Module Completion** — the learner has completed the entire [Module Progression](#module-progression) and achieved [Topic Competency](#topic-competency) in all topics.
2. **Peer Helper Track Record** — [Helper Metrics](#helper-metrics) meet the minimum threshold: helped ≥ 3 learners, average satisfaction ≥ 4.0/5.0, reviewed ≥ 5 practice tasks.
3. **Teaching Trial** — successfully assisted 2–3 learners through at least one topic under the Master's supervision. The Master evaluates teaching quality, patience, and accuracy.
4. **Master Approval** — the [Master](./learning.md#master) explicitly approves the promotion based on overall assessment.

Promotion is irreversible under normal circumstances (a Curator can be suspended for quality issues but not demoted back to Topic Expert). Upon promotion, the Curator's [Cohort Role](#cohort-role) is updated, their [Project Role](./project.md#project-role) is synchronized via [Role Mapping](#role-mapping), and a `CuratorPromoted` [Domain Event](#domain-event) is emitted — this event is consumed by the [Partnership context](./partnership.md) to initialize the Curator's partner rewards profile.

**Code mapping:**

- Python: `CuratorPromotionService` domain service in `cohort_learning/domain/curator_promotion.py`

**Related terms:** [Module Curator](#module-curator), [Topic Expert](#topic-expert), [Helper Metrics](#helper-metrics), [Domain Event](#domain-event)

---

### Master Graduation

**Definition:** The long-term progression path by which a [Module Curator](#module-curator) can become a full [Master](./learning.md#master) in the [Learning & Mentorship](./learning.md) context. This is the final step in the partner progression: Learner → Topic Expert → Module Curator → **Master**.

**Context:** Master Graduation is NOT part of the V1 MVP — it is documented here as an architectural placeholder to ensure the MVP design does not block this future evolution. The path involves: curating multiple cohorts with high satisfaction ratings, demonstrating ability to create original educational content, passing [Master Verification](./learning.md#master-verification) in the Learning context, and potentially creating new modules for the [Module Marketplace](#module-marketplace-placeholder). When implemented, Master Graduation will emit a `CuratorBecameMaster` domain event that triggers Master creation in the Learning context.

**Related terms:** [Module Curator](#module-curator), [Master](./learning.md#master), [Master Verification](./learning.md#master-verification), [Module Marketplace Placeholder](#module-marketplace-placeholder)

---

## 4. Hybrid Reward System

### Expert Reward

**Definition:** A non-monetary incentive granted to a [Topic Expert](#topic-expert) for [Peer Helper](#peer-helper) activity. Expert Rewards recognize and motivate helping behavior at the early stages of the partner progression.

**Context:** Expert Rewards are the first tier of the [Hybrid Reward System](#hybrid-reward-system-overview) — they are entirely non-monetary and serve to build engagement before the learner reaches [Module Curator](#module-curator) level. Reward types:
- **Experience Points (XP)** — earned per helping action (question answered, task reviewed, guidance provided). XP accumulates on the learner's [Learner Profile](./learning.md#learner-profile) and is visible to Masters and other learners.
- **Topic Expert Badge** — a visual indicator on the learner's profile showing mastered topics. Displayed in the cohort workspace and on the platform.
- **Reputation Score** — a composite metric derived from [Helper Metrics](#helper-metrics) and peer satisfaction ratings. Persists across cohorts.
- **Learning Credits** — discounts on future module enrollments, earned through sustained helping activity (e.g., 5% discount per 10 learners helped, up to 50%).

Expert Rewards are tracked in this context and displayed on the learner's profile. They are NOT processed through the [Partnership](./partnership.md) or [Billing](./billing.md) contexts — they are internal to the learning ecosystem.

**Code mapping:**

- Python: `ExpertReward` entity in `cohort_learning/domain/expert_reward.py`

**Related terms:** [Topic Expert](#topic-expert), [Peer Helper](#peer-helper), [Helper Metrics](#helper-metrics), [Hybrid Reward System Overview](#hybrid-reward-system-overview)

---

### Monetary Reward

**Definition:** A financial incentive available to [Module Curators](#module-curator) and above. Monetary Rewards are the second tier of the [Hybrid Reward System](#hybrid-reward-system-overview) and represent the bridge between educational volunteering and the [Partnership & Referral Program](./partnership.md).

**Context:** Monetary Rewards begin at Module Curator level and are processed through the Partnership context's commission infrastructure. Reward structure:
- **Curation Commission** — a percentage (5–15%, configurable per module) of the enrollment fees paid by learners in cohorts that the Curator leads or co-leads. Processed as a [Qualifying Event](./partnership.md#qualifying-event) in the Partnership context.
- **Quality Bonus** — an additional bonus for maintaining high satisfaction ratings (e.g., average ≥ 4.5/5.0 over 10+ learners). Calculated per cohort upon graduation.
- **Referral Commission** — when a Curator's recommendation leads to a new learner enrolling, the standard [Partnership referral commission](./partnership.md#commission) applies.

Monetary Rewards are subject to the [Hold Period](./partnership.md#hold-period) and [Payout](./partnership.md#payout) rules defined in the Partnership context. This context emits `CurationCommissionEarned` and `QualityBonusEarned` events; the Partnership context processes them as Qualifying Events.

**Code mapping:**

- Python: `MonetaryReward` value object in `cohort_learning/domain/monetary_reward.py`

**Related terms:** [Module Curator](#module-curator), [Hybrid Reward System Overview](#hybrid-reward-system-overview), [Commission](./partnership.md#commission), [Qualifying Event](./partnership.md#qualifying-event)

---

### Hybrid Reward System Overview

**Definition:** The dual-track incentive structure that motivates educational participation through a combination of non-monetary ([Expert Rewards](#expert-reward)) and monetary ([Monetary Rewards](#monetary-reward)) incentives, calibrated to the participant's progression level.

**Context:** The reward system is designed to create a self-sustaining learning ecosystem where advanced learners are incentivized to teach newcomers:

| Progression Level | Non-Monetary Rewards | Monetary Rewards |
|---|---|---|
| **Learner** | XP for task completion, participation badges | None |
| **Topic Expert** | XP for helping, Topic Expert badges, reputation score, learning credits (discounts) | None |
| **Module Curator** | All above + Curator certificate, priority access to new modules | Curation commission (5–15%), quality bonus, referral commission |
| **Master** (future) | All above + Master badge, platform showcase | Program creation revenue, multi-level referral commissions |

The system deliberately withholds monetary rewards until the Module Curator level to ensure that early helping behavior is driven by intrinsic motivation (learning by teaching, reputation building) rather than financial incentives. This produces higher-quality helpers and reduces gaming.

**Related terms:** [Expert Reward](#expert-reward), [Monetary Reward](#monetary-reward), [Topic Expert](#topic-expert), [Module Curator](#module-curator), [Partnership & Referral Program](./partnership.md)

---

### Reward Ledger

**Definition:** An append-only record of all [Expert Rewards](#expert-reward) and [Monetary Rewards](#monetary-reward) earned by a participant. Each entry captures: timestamp, participant `IdentityId`, reward type, amount (XP, credits, or monetary value), triggering action, and associated cohort/topic.

**Context:** The Reward Ledger is the single source of truth for non-monetary reward balances (XP, credits). Monetary reward entries are mirrored — the authoritative financial ledger is the [Commission Ledger](./partnership.md#commission-ledger) in the Partnership context. The Reward Ledger in this context serves as a unified view for the learner's dashboard, showing both non-monetary and monetary rewards in one place. Entries are immutable once recorded.

**Code mapping:**

- Python: `RewardLedger` entity in `cohort_learning/domain/reward_ledger.py`, `RewardEntry` value object

**Related terms:** [Expert Reward](#expert-reward), [Monetary Reward](#monetary-reward), [Commission Ledger](./partnership.md#commission-ledger)

---

## 5. Project Coordination

### Learning Project

**Definition:** A [Project](./project.md#project) in the Projects context that has been designated as the shared workspace for a [Learning Cohort](#learning-cohort). A Learning Project is a regular Project with educational semantics applied by the Cohort Learning context — the Projects context is unaware of its educational purpose.

**Context:** A Learning Project is automatically created when a [Learning Cohort](#learning-cohort) transitions from `Forming` to `Active` status. The creation is orchestrated by this context: it calls the Projects context's API to create a Project, then maps Cohort members to Project members via [Role Mapping](#role-mapping). The Learning Project contains [Practice Tasks](#practice-task), learning materials, and [Peer Review](#peer-review) workflows. When the Cohort graduates, the Learning Project transitions to [Completed](./project.md#completed-state), preserving all content for reference. The Learning Project's [Project Settings](./project.md#project-settings) are configured by the Master through this context, not directly through the Projects context.

**Code mapping:**

- Python: `LearningProject` entity in `cohort_learning/domain/learning_project.py`

**Related terms:** [Learning Cohort](#learning-cohort), [Practice Task](#practice-task), [Role Mapping](#role-mapping), [Project](./project.md#project)

**Not to be confused with:** [Project](./project.md#project) in the Projects context — a Learning Project IS a Project at the infrastructure level, but with additional educational semantics managed by the Cohort Learning context. The Projects context sees it as a regular Project; only this context knows its educational purpose.

---

### Practice Task

**Definition:** A task within a [Learning Project](#learning-project) that requires a learner to apply knowledge from a specific [Topic](#topic). Practice Tasks are the primary mechanism for hands-on learning and [Topic Competency](#topic-competency) assessment.

**Context:** Practice Tasks are created by the [Master](./learning.md#master) or [Module Curator](#module-curator) and are scoped to a specific Topic. Each task has: a description, acceptance criteria, attached template materials (checklists, starter code, diagrams), difficulty level, and estimated completion time. Task types:
- **Individual Task** — completed independently by each learner.
- **Pair Task** — completed by two learners collaboratively (assigned by the Master or self-selected).
- **Group Task** — completed by a subset of the cohort (3–5 learners).

Practice Tasks follow a submission and review flow: Learner submits → [Peer Review](#peer-review) → [Topic Expert](#topic-expert) or [Module Curator](#module-curator) validates → Master approves (optional for routine tasks). Task completion is tracked as a `PracticeTaskCompleted` [Domain Event](#domain-event) and feeds into [Topic Competency](#topic-competency) assessment.

**Code mapping:**

- Python: `PracticeTask` entity in `cohort_learning/domain/practice_task.py`

**Related terms:** [Learning Project](#learning-project), [Topic](#topic), [Peer Review](#peer-review), [Topic Competency](#topic-competency)

---

### Peer Review

**Definition:** The process by which cohort members evaluate each other's [Practice Task](#practice-task) submissions. Peer Review serves both educational (learning by reviewing) and operational (scaling assessment beyond the Master) purposes.

**Context:** Peer Review is structured:
- **Reviewer assignment** — automatic (round-robin within the cohort) or voluntary (learners pick tasks to review). [Topic Experts](#topic-expert) are prioritized as reviewers for their mastered topics.
- **Review criteria** — each Practice Task defines specific review criteria aligned with the topic's learning objectives. Reviewers score each criterion and provide written feedback.
- **Review validation** — reviews by regular Learners are advisory; reviews by Topic Experts or [Module Curators](#module-curator) carry validation weight toward [Topic Competency](#topic-competency).
- **Review quality** — reviewers receive XP ([Expert Reward](#expert-reward)) for reviews. Low-quality reviews (flagged by the task author or Master) reduce the reviewer's reputation score.

Peer Review activity is a key input for [Helper Metrics](#helper-metrics) and [Curator Promotion](#curator-promotion) eligibility.

**Code mapping:**

- Python: `PeerReview` entity in `cohort_learning/domain/peer_review.py`

**Related terms:** [Practice Task](#practice-task), [Topic Expert](#topic-expert), [Helper Metrics](#helper-metrics), [Expert Reward](#expert-reward)

---

### Progress Synchronization

**Definition:** The bidirectional data flow between this context and the [Learning](./learning.md) and [Projects](./project.md) contexts that keeps educational progress consistent across all three systems.

**Context:** Synchronization flows:
- **Projects → Cohort Learning:** When a Practice Task is completed in the Learning Project (tracked as a task completion in the Projects context), a `TaskCompletedEvent` is consumed by this context and mapped to [Topic Competency](#topic-competency) progress.
- **Cohort Learning → Learning:** When a learner achieves Topic Competency or completes the Module, this context emits events that the Learning context consumes to update [Learning Progress](./learning.md#learning-progress) and [Learner Status](./learning.md#learner-status).
- **Cohort Learning → Projects:** When a learner's [Cohort Role](#cohort-role) changes (e.g., promoted to Topic Expert), this context updates the corresponding [Project Role](./project.md#project-role) through the Projects context's API.

All synchronization passes through the Anti-Corruption Layer. In case of eventual consistency delays, the Cohort Learning context is the source of truth for educational progress; the Projects context is the source of truth for workspace operations.

**Code mapping:**

- Python: `ProgressSyncService` application service in `cohort_learning/application/progress_sync_service.py`

**Related terms:** [Learning Project](#learning-project), [Topic Competency](#topic-competency), [Role Mapping](#role-mapping)

---

## 6. Cross-Context Events

### Domain Event

**Definition:** A domain event emitted by the Cohort Learning context when a significant educational or progression action occurs. Domain Events are the official contract for cross-context consumers.

**Context:** Domain Events bridge bounded contexts and are the primary mechanism for loose coupling. Events follow the Published Language pattern (see [AGENTS.md 4.3](../AGENTS.md#43-context-mapping-карта-контекстов)). Each event carries a timestamp, the actor's `IdentityId`, and event-specific payload.

**Events emitted by this context:**

| Event | Trigger | Consumers |
|---|---|---|
| `CohortFormed` | Cohort transitions to `Active` | Projects (create Learning Project), Learning (track enrollment) |
| `CohortGraduated` | All learners completed or cohort end date reached | Projects (complete Learning Project), Learning (update learner statuses), Partnership (commission calculation) |
| `CohortCancelled` | Cohort disbanded before completion | Projects (archive Learning Project), Learning (notify learners) |
| `TopicCompetencyAchieved` | Learner passes Competency Validation | Learning (update progress), this context (evaluate Expert promotion) |
| `TopicExpertPromoted` | Learner achieves Topic Expert status | Projects (update role), this context (enable Peer Helper) |
| `CuratorPromoted` | Topic Expert promoted to Module Curator | Projects (update role), Partnership (initialize rewards profile), Learning (update profile) |
| `PracticeTaskCompleted` | Learner completes a Practice Task | Learning (update progress), this context (evaluate competency) |
| `PeerReviewSubmitted` | Cohort member submits a practice task review | This context (update Helper Metrics, calculate rewards) |
| `CurationCommissionEarned` | Curator's cohort completes, commission calculated | Partnership (accrue commission) |
| `QualityBonusEarned` | Curator achieves high satisfaction threshold | Partnership (accrue bonus) |
| `ExpertRewardGranted` | Topic Expert earns XP, badge, or credits | This context (update Reward Ledger) |

**Events consumed by this context:**

| Event | Source Context | Action |
|---|---|---|
| `TaskCompletedEvent` | Projects | Map to Practice Task completion, update Topic progress |
| `MemberJoinedEvent` | Projects | Verify Cohort Membership consistency |
| `MemberRemovedEvent` | Projects | Update Cohort Membership (learner left) |
| `ProjectCompletedEvent` | Projects | Verify Cohort graduation consistency |
| `LessonCompletedEvent` | Learning | Update Module Progression progress |
| `EnrollmentCreatedEvent` | Learning | Initialize Cohort Membership |

**Code mapping:**

- Python: domain event dataclasses in `cohort_learning/domain/events.py`, inheriting from `shared_kernel.events.DomainEvent`

**Related terms:** [Learning Cohort](#learning-cohort), [Topic Expert](#topic-expert), [Module Curator](#module-curator), [Progress Synchronization](#progress-synchronization)

---

### Domain Saga

**Definition:** A multi-step workflow that coordinates actions across the Learning, Projects, and Cohort Learning contexts to accomplish a complex business process. Each saga is triggered by a [Domain Event](#domain-event) and may emit further events.

**Context:** V1 defines the following sagas:

**1. Cohort Activation Saga:**
`CohortFormed` → Create Learning Project (Projects) → Add Members (Projects) → Notify Learners (Learning) → Start progress tracking (Cohort Learning)

**2. Competency Achievement Saga:**
`PracticeTaskCompleted` → Check all topic tasks complete → Run knowledge check → Evaluate peer reviews → Request mentor approval → Emit `TopicCompetencyAchieved` → Evaluate Topic Expert eligibility → Emit `TopicExpertPromoted` (if qualified)

**3. Cohort Graduation Saga:**
All learners complete or end date reached → Emit `CohortGraduated` → Complete Learning Project (Projects) → Update Learner Statuses (Learning) → Calculate Curator commissions (Cohort Learning) → Emit `CurationCommissionEarned` (Partnership) → Evaluate Curator promotion eligibility for graduates

**4. Curator Promotion Saga:**
Master approves promotion → Validate requirements (module completion, helper metrics, teaching trial) → Emit `CuratorPromoted` → Update Project Role (Projects) → Initialize Partner rewards profile (Partnership) → Grant Curator certificate (Cohort Learning)

Sagas are implemented as event-driven orchestrations in the application layer. Each step is idempotent and compensatable — if a step fails, compensating actions restore consistency.

**Code mapping:**

- Python: saga implementations in `cohort_learning/application/sagas/`

**Related terms:** [Domain Event](#domain-event), [Learning Cohort](#learning-cohort), [Curator Promotion](#curator-promotion), [Progress Synchronization](#progress-synchronization)

---

## 7. MVP Boundary Rules & Evolution Path

### V1 MVP Constraints

**Definition:** The explicit limitations of the first version of Cohort Learning, documented to prevent scope creep and to define clear boundaries for development.

**Context:** V1 operates under the following constraints:

| Constraint | V1 Limitation | Future Evolution |
|---|---|---|
| **Modules per Master** | 1 active module | Multiple modules, module versioning |
| **Cohorts per module** | 1 active cohort at a time | Parallel cohorts, cohort scheduling |
| **Learners per cohort** | 5–15 | Configurable, potentially larger for popular modules |
| **Cohort Role progression** | Linear: Learner → Topic Expert → Module Curator | Cross-module expertise, simultaneous Expert + Learner |
| **Master involvement** | Active: creates module, leads cohort, approves promotions | Delegated: Curators lead cohorts with minimal Master oversight |
| **Monetary rewards** | Curator commission only (flat percentage) | Tiered commissions, bonuses, revenue sharing |
| **Partnership integration** | Curator commission as Qualifying Event | Full multi-level referral integration |
| **Project integration** | 1 Learning Project per Cohort | Multiple projects per Cohort, real client project integration |
| **Curator assignment** | Master manually approves Curators | Automated qualification + Master confirmation |
| **Cross-cohort help** | Topic Experts from graduated cohorts can help new cohorts | Formal cross-cohort mentoring programs |

These constraints are enforced in the domain layer — the code explicitly prevents operations that exceed V1 limits (e.g., creating a second active cohort for the same module returns a domain error).

---

### Module Marketplace Placeholder

**Definition:** An architectural placeholder for the future Module Marketplace — a system where [Module Curators](#module-curator) and [Masters](./learning.md#master) can create, share, and monetize reusable educational modules.

**Context:** The Module Marketplace is NOT implemented in V1 but is referenced throughout this glossary to ensure the MVP design supports future evolution. Key future capabilities:
- Curators create derivative modules based on their teaching experience.
- Masters publish modules for other Masters/Curators to license and teach.
- Revenue sharing between module creators and module teachers.
- Module rating and quality assurance.
- Module versioning and deprecation.

The V1 architecture supports this by making [Module Progression](#module-progression) a first-class entity with clear ownership (Master), versioning (immutable once a Cohort starts), and separation from the Cohort lifecycle.

**Related terms:** [Module Progression](#module-progression), [Module Curator](#module-curator), [Master Graduation](#master-graduation)

---

### Evolution Milestones

**Definition:** Planned capability expansions beyond V1, documented to guide architectural decisions and prevent premature optimization.

**Context:**

**Version 2.0 — Multi-Module Learning:**
- Multiple modules per Master, parallel cohorts.
- Cross-module expertise: a learner can be a Topic Expert in Module A while studying Module B.
- Enhanced reward tiers: tiered commissions based on Curator performance.
- Automated competency validation with reduced Master oversight.
- Internship Projects: a separate mechanism for advanced learners to work on supervised real-world projects outside the cohort structure. Distinct from Learning Projects (which are cohort workspaces) — internships bridge learning and professional practice.

**Version 3.0 — Ecosystem & Marketplace:**
- Module Marketplace: Curators create and sell modules.
- Master Graduation: Curators become full Masters.
- Real project integration: advanced learners work on client projects.
- Multi-level partnership: Curators recruit new Curators, earning multi-level commissions through the [Partnership](./partnership.md) context's [Referral Chain](./partnership.md#referral-chain).

**Version 4.0 — Enterprise & Scale:**
- Corporate learning programs: organizations enroll teams.
- AI-assisted competency validation and personalized learning paths.
- Cross-platform module federation: modules from external providers.

**Related terms:** [V1 MVP Constraints](#v1-mvp-constraints), [Module Marketplace Placeholder](#module-marketplace-placeholder), [Master Graduation](#master-graduation)

---

## Cross-Context Boundary Notes

The Cohort Learning bounded context coordinates with three other contexts. The following table clarifies term boundaries and ownership:

| Cohort Learning Term | Other Context | Their Term | Relationship |
|---|---|---|---|
| `Learning Cohort` | Learning | [`Mentorship`](./learning.md#mentorship) | A Cohort is a group learning analog of the 1-on-1 Mentorship. Learning owns the Master–Learner relationship; Cohort Learning owns the cohort structure and group dynamics. A Cohort may create Mentorship records in Learning for progress tracking. |
| `Learning Cohort` | Project | [`Project`](./project.md#project) | Each Cohort maps to one Learning Project. Cohort Learning owns educational semantics; Project owns workspace infrastructure (members, permissions, content). |
| `Cohort Role` | Project | [`Project Role`](./project.md#project-role) | Cohort Roles are mapped to Project Roles via Role Mapping. Cohort Learning owns role progression logic; Project enforces workspace permissions. Role changes flow from Cohort Learning to Project, never the reverse. |
| `Cohort Membership` | Project | [`Membership`](./project.md#membership) | Each Cohort Membership corresponds to a Project Membership. Cohort Learning creates/updates Project Memberships via the Projects API when learners join or are promoted. |
| `Practice Task` | Project | Task (project content) | Practice Tasks are represented as content within the Learning Project. Cohort Learning defines educational semantics (topic association, competency weight); Project provides storage and collaboration infrastructure. |
| `Topic Competency` | Learning | [`Learning Progress`](./learning.md#learning-progress) | Topic Competency in Cohort Learning maps to lesson/module completion in Learning. Cohort Learning emits events that Learning consumes to update its progress tracking. |
| `Module Curator` | Learning | [`Master`](./learning.md#master) (future) | A Module Curator is a proto-Master — they curate within the Master's program. Future Master Graduation elevates them to full Master status in the Learning context. |
| `Module Curator` | Partnership | [`Partner`](./partnership.md#partner) | When a Curator earns monetary rewards, Cohort Learning emits events that Partnership processes as Qualifying Events. Partnership owns financial ledger and payouts; Cohort Learning owns educational qualification. |
| `Expert Reward` (XP, credits) | — | — | Owned entirely by the Cohort Learning context. Not shared with other contexts. Displayed on the learner's dashboard via a read model. |
| `Monetary Reward` | Partnership | [`Commission`](./partnership.md#commission), [`Qualifying Event`](./partnership.md#qualifying-event) | Cohort Learning calculates commission eligibility and emits events. Partnership processes the financial transaction. The two contexts do not share domain models. |
| `Peer Review` | Project | Task review/comment | Peer Reviews are stored as structured content within the Learning Project. Cohort Learning adds educational semantics (competency validation weight, reviewer qualification check). |

**Cross-context rules:**

- The Learning context MUST NOT know about Cohorts, Cohort Roles, or Topic Experts. These are concepts owned by the Cohort Learning context. Learning sees learners progressing through programs via standard [Learning Events](./learning.md#learning-event).
- The Projects context MUST NOT know about educational purpose, topics, competency, or rewards. It provides workspace infrastructure. When this context needs to create a Project or update a Membership, it calls the Projects context's API — never manipulates Project data directly.
- The Partnership context MUST NOT know about Topics, Competency, or Peer Reviews. It receives `CurationCommissionEarned` and `QualityBonusEarned` events and processes them as generic [Qualifying Events](./partnership.md#qualifying-event). The educational logic behind these events is opaque to Partnership.
- The Cohort Learning context MUST NOT access the databases of Learning, Projects, or Partnership directly. All communication is through domain events and API contracts via Anti-Corruption Layers (see [AGENTS.md 4.3](../AGENTS.md#43-context-mapping-карта-контекстов)).
- Role synchronization between [Cohort Role](#cohort-role) and [Project Role](./project.md#project-role) is **unidirectional**: Cohort Learning → Projects. The Projects context never triggers Cohort Role changes.
- [Monetary Rewards](#monetary-reward) are calculated by this context but **owned and processed** by the Partnership context. This context emits the qualifying event; Partnership handles hold periods, fraud checks, ledger entries, and payouts.
- When a [Module Curator](#module-curator) is promoted, this context emits a single `CuratorPromoted` event. Multiple consumers react independently: Projects updates the role, Partnership initializes the rewards profile, Learning updates the learner profile. Consumers are decoupled — failure in one does not block others (eventual consistency).
