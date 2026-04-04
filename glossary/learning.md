# Learning & Mentorship — Ubiquitous Language Glossary

This glossary defines the authoritative vocabulary for the **Learning & Mentorship** bounded context. All code, documentation, API contracts, and team communication within this context MUST use these terms consistently.

**Bounded Context scope:** Master onboarding and verification, learner enrollment (free, paid, invite-based), 1-on-1 mentoring relationships, flexible learning programs (modules optional), apprenticeship on real client sites with remote supervision, learner lifecycle progression (Learner → Apprentice → Specialist), progress tracking, session evaluation, reviews and ratings.

**Mentoring model:** This is NOT a mass online course platform. The core model is **1-on-1 mentorship** where a verified Master guides a Learner through theory, then supervises their practical work on real client jobs (field apprenticeship). Masters can lead multiple learners simultaneously within a configurable capacity limit. Masters may be platform users who gained expertise or external experts invited to teach.

**Code mapping convention:**

- Python: `learning/domain/` for domain models, `learning/application/` for use cases, `learning/infrastructure/` for adapters
 `packages/learning/src/domain/`, `packages/learning/src/application/`, `packages/learning/src/infrastructure/`

**Cross-context dependencies:** This context references identities from the [Auth bounded context](./auth.md). Both [Master](#master) and [Learner](#learner) are linked to an [AuthUser](./auth.md#authuser) via `IdentityId`, but are separate domain models — Auth owns credentials and sessions, Learning owns mentoring relationships, progress, and professional verification.

---

## 1. Master Identity

### Master

**Definition:** A verified expert who mentors [Learners](#learner) through 1-on-1 educational relationships. A Master is the root teaching entity within this bounded context — they create [Learning Programs](#learning-program), conduct mentoring sessions, supervise [Apprenticeship Sessions](#apprenticeship-session) on real client sites, and evaluate learner performance.

**Context:** Every Master is linked to an [AuthUser](./auth.md#authuser) via `IdentityId`, but `Master` is a separate domain model — it does not inherit from or extend `AuthUser`. A user becomes a Master by passing [Master Verification](#master-verification). Masters can be both internal platform users (who gained expertise and want to teach) and external experts invited to the platform specifically to mentor. Each Master has a [Master Profile](#master-profile), one or more [Specializations](#specialization), a configurable [Master Capacity](#master-capacity), and a [Master Status](#master-status) that governs their ability to accept learners.

**Code mapping:**

- Python: `Master` aggregate root in `learning/domain/master.py`
 `Master` class in `packages/learning/src/domain/master.ts`

**Related terms:** [Master Profile](#master-profile), [Master Status](#master-status), [Specialization](#specialization), [Master Capacity](#master-capacity), [Master Verification](#master-verification), [Master Rating](#master-rating), [Mentorship](#mentorship)

**Not to be confused with:** [AuthUser](./auth.md#authuser) in the Auth context (owns credentials, sessions, system-wide roles), [Partner](./partnership.md#partner) in the Partnership context (owns referral relationships, commissions), or [Member](./project.md#member) in the Project context (owns project membership and project-scoped role). A single person may be all of these, but each context maintains its own model.

---

### Master Profile

**Definition:** Public-facing metadata associated with a [Master](#master): display name, avatar, bio, years of experience, portfolio (photos/videos of completed work), service geography, and links to professional certifications.

**Context:** Master Profile is separate from [AuthUser](./auth.md#authuser) profile data in the Auth context — Auth owns identity information (locale, timezone, email), Learning owns the professional teaching profile (specializations, portfolio, teaching history). The profile is displayed to potential [Learners](#learner) when they browse available masters. Profile completeness may affect search ranking and visibility on the platform.

**Code mapping:**

- Python: `MasterProfile` dataclass in `learning/domain/master_profile.py`
 `MasterProfile` interface in `packages/learning/src/domain/master-profile.ts`

**Related terms:** [Master](#master), [Specialization](#specialization), [Master Rating](#master-rating)

---

### Master Status

**Definition:** An enum representing the current lifecycle state of a [Master](#master). Values: `Pending Verification` (application submitted, awaiting review), `Verified` (approved to teach), `Suspended` (temporarily disabled — cannot accept new learners, existing mentorships paused), `Deactivated` (permanently removed from the teaching pool).

**Context:** Only `Verified` masters can create [Learning Programs](#learning-program), accept [Enrollments](#enrollment), and conduct [Apprenticeship Sessions](#apprenticeship-session). `Suspended` preserves the master's data and existing relationships but blocks all teaching activity — used for investigations, quality concerns, or temporary unavailability. `Deactivated` is the terminal state: the master's profile is hidden, active [Mentorships](#mentorship) must be transferred or terminated, and re-activation requires a new [Master Verification](#master-verification).

**Code mapping:**

- Python: `MasterStatus` enum in `learning/domain/master_status.py`
 `MasterStatus` union type in `packages/learning/src/domain/master-status.ts`

**Related terms:** [Master](#master), [Master Verification](#master-verification), [Mentorship](#mentorship)

---

### Specialization

**Definition:** A domain of professional expertise that a [Master](#master) is qualified to teach. Examples: plumbing, electrical work, HVAC, carpentry, welding, tile installation. A Master can hold multiple Specializations.

**Context:** Specializations are platform-managed categories (not free-text) to ensure consistency in search and matching. Each Specialization has a name, description, and an optional parent (for hierarchies: e.g., "Plumbing" → "Pipe Fitting", "Drain Repair"). Learners search for masters by Specialization. A Master's Specializations are verified during [Master Verification](#master-verification) and may be extended later with additional proof of qualification.

**Code mapping:**

- Python: `Specialization` entity in `learning/domain/specialization.py`
 `Specialization` class in `packages/learning/src/domain/specialization.ts`

**Related terms:** [Master](#master), [Master Profile](#master-profile), [Master Verification](#master-verification), [Learning Program](#learning-program)

---

### Master Capacity

**Definition:** The maximum number of [Learners](#learner) a [Master](#master) can mentor simultaneously through active [Mentorships](#mentorship). Configured by the Master within platform-defined bounds.

**Context:** Capacity prevents overloading a Master and ensures quality of mentoring. The platform sets an upper bound (e.g., 10 learners max); the Master can set a lower personal limit (e.g., 3). Capacity counts only `Active` [Mentorships](#mentorship) — `Paused` or `Completed` mentorships do not count. When capacity is reached, new [Enrollments](#enrollment) are blocked until a slot opens. Capacity changes emit a [Learning Event](#learning-event).

**Code mapping:**

- Python: `MasterCapacity` value object in `learning/domain/master_capacity.py`
 `MasterCapacity` branded type in `packages/learning/src/domain/master-capacity.ts`

**Related terms:** [Master](#master), [Mentorship](#mentorship), [Enrollment](#enrollment)

---

### Master Verification

**Definition:** The process of validating a candidate's professional qualifications before granting [Master](#master) status. Verification reviews submitted documents (certifications, licenses, diplomas), work experience evidence, and optionally a practical assessment.

**Context:** Verification is a domain concern of the Learning context, not Auth. Auth may verify identity documents (passport, ID); Learning verifies professional credentials (plumber's license, electrician certification, years of experience). Verification can be: `Pending` (documents submitted), `InReview` (assigned to a reviewer), `Approved` (Master becomes `Verified`), `Rejected` (with reason; candidate may reapply). The verification process may involve manual review by platform staff or automated checks against external credential databases.

**Code mapping:**

- Python: `MasterVerification` entity in `learning/domain/master_verification.py`
 `MasterVerification` class in `packages/learning/src/domain/master-verification.ts`

**Related terms:** [Master](#master), [Master Status](#master-status), [Specialization](#specialization)

**Not to be confused with:** Identity verification in the [Auth context](./auth.md) — Auth verifies "you are who you say you are" (identity), Learning verifies "you are qualified to teach this trade" (professional competence).

---

### Master Rating

**Definition:** An aggregated numerical score representing the quality of a [Master](#master) based on [Reviews](#review) submitted by [Learners](#learner). Calculated as a weighted average across all [Rating Criteria](#rating-criteria).

**Context:** Master Rating is displayed on the [Master Profile](#master-profile) and used for search ranking, platform recommendations, and quality thresholds (e.g., masters below 3.0 may be flagged for review). The rating is recalculated whenever a new [Review](#review) is submitted. Only reviews from learners with `Graduated` or `Active` [Learner Status](#learner-status) count toward the rating — reviews from `Dropped Out` learners may be weighted differently or excluded per platform policy.

**Code mapping:**

- Python: `MasterRating` value object in `learning/domain/master_rating.py`
 `MasterRating` value object in `packages/learning/src/domain/master-rating.ts`

**Related terms:** [Master](#master), [Review](#review), [Rating Criteria](#rating-criteria), [Aggregated Rating](#aggregated-rating)

---

## 2. Learner & Lifecycle

### Learner

**Definition:** A user who has enrolled in a mentoring relationship with a [Master](#master) to acquire practical skills. A Learner is the core student entity within this bounded context — they progress through a defined lifecycle from enrollment to graduation.

**Context:** Every Learner is linked to an [AuthUser](./auth.md#authuser) via `IdentityId`, but `Learner` is a separate domain model. A user becomes a Learner by [Enrolling](#enrollment) with a specific Master (or into a specific [Learning Program](#learning-program)). A single user can be a Learner under multiple Masters simultaneously (for different [Specializations](#specialization)). Each Learner has a [Learner Status](#learner-status) that tracks their progression, a [Learner Profile](#learner-profile) with accumulated progress, and one or more active [Mentorships](#mentorship).

**Code mapping:**

- Python: `Learner` entity in `learning/domain/learner.py`
 `Learner` class in `packages/learning/src/domain/learner.ts`

**Related terms:** [Learner Status](#learner-status), [Learner Profile](#learner-profile), [Enrollment](#enrollment), [Mentorship](#mentorship), [Learning Progress](#learning-progress)

**Not to be confused with:** [AuthUser](./auth.md#authuser) in Auth (owns credentials), [Member](./project.md#member) in Projects (owns project membership), or [Partner](./partnership.md#partner) in Partnership (owns referral relationships). A single person may be all of these simultaneously.

---

### Learner Status

**Definition:** An enum representing the current stage of a [Learner](#learner)'s lifecycle within a specific [Mentorship](#mentorship). Values: `Enrolled`, `Active`, `Apprentice`, `Specialist`, `Graduated`, `Dropped Out`.

**Context:** Status tracks the learner's progression through the mentoring journey:
- `Enrolled` — signed up but has not started learning yet (pending start date or payment confirmation).
- `Active` — actively working through the theoretical part of the [Learning Program](#learning-program).
- `Apprentice` — promoted to practical training; eligible for [Apprenticeship Sessions](#apprenticeship-session) on real client sites. Requires completing a minimum portion of theory and Master's approval.
- `Specialist` — completed the required apprenticeship sessions with satisfactory [Session Evaluations](#session-evaluation); capable of working independently. Still part of the program for final assessment.
- `Graduated` — successfully completed the entire program, met all [Completion Criteria](#completion-criteria), and received a [Certificate](#certificate).
- `Dropped Out` — left the program before completion (voluntary or forced by Master/platform).

Each transition is governed by [Learner Transition](#learner-transition) rules.

**Code mapping:**

- Python: `LearnerStatus` enum in `learning/domain/learner_status.py`
 `LearnerStatus` union type in `packages/learning/src/domain/learner-status.ts`

**Related terms:** [Learner](#learner), [Learner Transition](#learner-transition), [Mentorship](#mentorship), [Apprenticeship Session](#apprenticeship-session), [Graduation](#graduation)

---

### Learner Profile

**Definition:** An educational profile aggregating a [Learner](#learner)'s history across all [Mentorships](#mentorship): completed programs, [Specializations](#specialization) studied, total apprenticeship hours, certificates earned, and overall performance metrics.

**Context:** Learner Profile is a read model that spans multiple mentorships. While each [Mentorship](#mentorship) tracks progress within a specific Master-Learner relationship, the Learner Profile gives a holistic view. It is displayed to Masters considering new enrollment requests and may be shared publicly if the learner opts in. The profile is rebuilt from [Learning Events](#learning-event) and is eventually consistent.

**Code mapping:**

- Python: `LearnerProfile` dataclass in `learning/domain/learner_profile.py`
 `LearnerProfile` interface in `packages/learning/src/domain/learner-profile.ts`

**Related terms:** [Learner](#learner), [Mentorship](#mentorship), [Learning Progress](#learning-progress), [Certificate](#certificate)

---

### Enrollment

**Definition:** The process and resulting record of a [Learner](#learner) signing up for a [Mentorship](#mentorship) with a specific [Master](#master) (and optionally a specific [Learning Program](#learning-program)). Enrollment captures the join method, date, agreed terms, and initial status.

**Context:** Enrollment is the entry point into the mentoring relationship. It can be initiated in four ways (see [Enrollment Method](#enrollment-method)): free sign-up, paid purchase, invitation from the Master, or application with approval. For paid enrollments, the Learning context emits an `EnrollmentPaymentRequested` event; the Billing context processes payment and emits `PaymentCompleted`; Learning then activates the enrollment. Enrollment creates a [Mentorship](#mentorship) record with `Pending` [Mentorship Status](#mentorship-status).

**Code mapping:**

- Python: `Enrollment` entity in `learning/domain/enrollment.py`
 `Enrollment` class in `packages/learning/src/domain/enrollment.ts`

**Related terms:** [Enrollment Method](#enrollment-method), [Learner](#learner), [Master](#master), [Mentorship](#mentorship), [Learning Program](#learning-program)

---

### Enrollment Method

**Definition:** The mechanism by which a [Learner](#learner) gained access to a [Mentorship](#mentorship). Values: `Free` (open enrollment, no payment), `Paid` (enrollment requires payment processed via Billing), `InvitedByMaster` (Master sent a direct invitation), `ApprovedApplication` (Learner applied, Master reviewed and approved).

**Context:** Enrollment Method is recorded on the [Enrollment](#enrollment) and is immutable after creation. It determines the activation flow: `Free` and `InvitedByMaster` activate immediately; `Paid` waits for payment confirmation from Billing; `ApprovedApplication` waits for the Master's explicit approval. The method is also used in analytics to understand how learners discover and join programs.

**Code mapping:**

- Python: `EnrollmentMethod` enum in `learning/domain/enrollment_method.py`
 `EnrollmentMethod` union type in `packages/learning/src/domain/enrollment-method.ts`

**Related terms:** [Enrollment](#enrollment), [Mentorship](#mentorship)

---

### Learner Transition

**Definition:** A validated state change of a [Learner](#learner) from one [Learner Status](#learner-status) to another within a specific [Mentorship](#mentorship). Each transition enforces preconditions and emits a [Learning Event](#learning-event).

**Context:** Allowed transitions form a directed graph:
- `Enrolled` → `Active` (learning started, payment confirmed if applicable)
- `Active` → `Apprentice` (minimum theory completed, Master approved for field work)
- `Apprentice` → `Specialist` (minimum N apprenticeship sessions completed with satisfactory [Session Evaluations](#session-evaluation))
- `Specialist` → `Graduated` (all [Completion Criteria](#completion-criteria) met, final assessment passed)
- `Enrolled` | `Active` | `Apprentice` | `Specialist` → `Dropped Out` (voluntary or forced exit)

Invalid transitions (e.g., `Enrolled` → `Specialist`, `Graduated` → `Active`) are rejected by the domain model. Each transition may require the Master's explicit confirmation (e.g., promoting to `Apprentice` or `Specialist`).

**Code mapping:**

- Python: `LearnerTransition` domain service in `learning/domain/learner_transition.py`
 `LearnerTransition` domain service in `packages/learning/src/domain/learner-transition.ts`

**Related terms:** [Learner Status](#learner-status), [Session Evaluation](#session-evaluation), [Completion Criteria](#completion-criteria), [Learning Event](#learning-event)

---

### Graduation

**Definition:** The domain event and process marking the successful completion of a [Mentorship](#mentorship). Graduation is triggered when a [Learner](#learner) meets all [Completion Criteria](#completion-criteria) and transitions to the `Graduated` [Learner Status](#learner-status).

**Context:** Graduation may include: the Master submitting a final evaluation, the system verifying all criteria are met, automatic issuance of a [Certificate](#certificate), and emission of a `LearnerGraduated` [Learning Event](#learning-event). Graduation is a significant domain event — it may trigger actions in other contexts (e.g., the graduated learner can now register as a [Master](#master) themselves, or the Partnership context awards a commission for a completed mentorship).

**Code mapping:**

- Python: `GraduationService` domain service in `learning/domain/graduation_service.py`
 `GraduationService` domain service in `packages/learning/src/domain/graduation-service.ts`

**Related terms:** [Learner Status](#learner-status), [Learner Transition](#learner-transition), [Completion Criteria](#completion-criteria), [Certificate](#certificate), [Learning Event](#learning-event)

---

## 3. Learning Program & Content

### Learning Program

**Definition:** A structured educational plan created by a [Master](#master) that defines what a [Learner](#learner) will study and in what order. A Learning Program consists of a [Syllabus](#syllabus) organizing [Lessons](#lesson) and optionally [Modules](#module), plus [Completion Criteria](#completion-criteria) that define when the program is finished.

**Context:** Programs are the Master's main content asset. Each Master can create multiple programs (e.g., "Plumbing Fundamentals," "Advanced Pipe Fitting," "Residential Drain Systems"). Programs have a flexible structure — the Master decides whether to group lessons into modules or keep them flat. A Program is tied to one or more [Specializations](#specialization). Learners enroll into a program through a [Mentorship](#mentorship) with the program's author.

**Code mapping:**

- Python: `LearningProgram` entity in `learning/domain/learning_program.py`
 `LearningProgram` class in `packages/learning/src/domain/learning-program.ts`

**Related terms:** [Module](#module), [Lesson](#lesson), [Syllabus](#syllabus), [Program Status](#program-status), [Completion Criteria](#completion-criteria), [Master](#master), [Specialization](#specialization)

---

### Module

**Definition:** An optional grouping of [Lessons](#lesson) within a [Learning Program](#learning-program). Modules provide logical structure for larger programs (e.g., "Module 1: Safety Basics," "Module 2: Tools and Materials," "Module 3: Hands-On Techniques").

**Context:** Modules are optional — a Master may create a flat program with only lessons and no modules. When used, modules have an ordering within the program, a title, a description, and contain an ordered list of lessons. Module completion is tracked as part of [Learning Progress](#learning-progress). A module is considered complete when all its lessons are completed.

**Code mapping:**

- Python: `Module` entity in `learning/domain/module.py`
 `Module` class in `packages/learning/src/domain/module.ts`

**Related terms:** [Learning Program](#learning-program), [Lesson](#lesson), [Syllabus](#syllabus), [Learning Progress](#learning-progress)

---

### Lesson

**Definition:** The smallest unit of educational content within a [Learning Program](#learning-program). Each Lesson covers a single topic or skill and has a [Lesson Type](#lesson-type) that determines its format.

**Context:** Lessons are authored by the [Master](#master) and can contain: video recordings, written text with images, practical exercises, graded assignments, or quizzes. Each lesson belongs to either a [Module](#module) or directly to a Program (if modules are not used). Lessons have an ordering (position) that defines the recommended sequence. A lesson may have attached [Learning Materials](#learning-material) (PDFs, diagrams, checklists). Lesson completion by a Learner is tracked via [Lesson Completion](#lesson-completion).

**Code mapping:**

- Python: `Lesson` entity in `learning/domain/lesson.py`
 `Lesson` class in `packages/learning/src/domain/lesson.ts`

**Related terms:** [Lesson Type](#lesson-type), [Module](#module), [Learning Program](#learning-program), [Learning Material](#learning-material), [Lesson Completion](#lesson-completion)

---

### Lesson Type

**Definition:** An enum classifying the format of a [Lesson](#lesson)'s content. Values: `Video` (recorded video lesson), `Text` (written content with optional images), `Exercise` (hands-on practice without grading), `Assignment` (graded task submitted to the Master for evaluation), `Quiz` (automated assessment with questions and answers).

**Context:** Lesson Type determines how the lesson is presented, how completion is tracked, and whether it requires Master evaluation. `Video` and `Text` are marked complete when the learner finishes viewing/reading. `Exercise` is self-assessed. `Assignment` requires the Master to review and grade the submission. `Quiz` is auto-graded by the system. The Master chooses the type when creating the lesson.

**Code mapping:**

- Python: `LessonType` enum in `learning/domain/lesson_type.py`
 `LessonType` union type in `packages/learning/src/domain/lesson-type.ts`

**Related terms:** [Lesson](#lesson), [Lesson Completion](#lesson-completion)

---

### Program Status

**Definition:** An enum representing the publication state of a [Learning Program](#learning-program). Values: `Draft` (being created, not visible to learners), `Published` (available for enrollment), `Archived` (no longer available for new enrollments, existing mentorships continue).

**Context:** Only `Published` programs appear in search results and are available for [Enrollment](#enrollment). A Master can iterate on a `Draft` program as long as needed. `Archived` programs preserve content for learners who are still active in ongoing [Mentorships](#mentorship) but do not accept new enrollments. A program cannot be published without at least one [Lesson](#lesson) and defined [Completion Criteria](#completion-criteria).

**Code mapping:**

- Python: `ProgramStatus` enum in `learning/domain/program_status.py`
 `ProgramStatus` union type in `packages/learning/src/domain/program-status.ts`

**Related terms:** [Learning Program](#learning-program), [Enrollment](#enrollment), [Mentorship](#mentorship)

---

### Syllabus

**Definition:** The structured outline of a [Learning Program](#learning-program): an ordered tree of [Modules](#module) and [Lessons](#lesson), including prerequisites between them, estimated duration for each unit, and the recommended learning path.

**Context:** The Syllabus is the "table of contents" of a program. It is displayed to potential learners before enrollment and guides the learner through the program. Prerequisites define mandatory ordering (e.g., "Lesson 3 requires Lesson 1 and Lesson 2 to be completed first"). Estimated duration helps learners plan their time. The Master maintains the Syllabus; changes to a published program's syllabus apply to new learners, while existing learners may continue with the original structure (configurable per program).

**Code mapping:**

- Python: `Syllabus` value object in `learning/domain/syllabus.py`
 `Syllabus` interface in `packages/learning/src/domain/syllabus.ts`

**Related terms:** [Learning Program](#learning-program), [Module](#module), [Lesson](#lesson), [Learning Progress](#learning-progress)

---

### Learning Material

**Definition:** A supplementary resource attached to a [Lesson](#lesson): PDF documents, technical diagrams, checklists, tool lists, safety instructions, video recordings, or reference manuals.

**Context:** Materials are uploaded by the [Master](#master) and are accessible to enrolled [Learners](#learner) within the context of the lesson. They supplement the lesson content (not replace it). Materials have a file type, size, a display name, and an ordering within the lesson. They are stored in the infrastructure layer (object storage) and referenced by the domain via a `MaterialId`.

**Code mapping:**

- Python: `LearningMaterial` entity in `learning/domain/learning_material.py`
 `LearningMaterial` class in `packages/learning/src/domain/learning-material.ts`

**Related terms:** [Lesson](#lesson), [Master](#master)

---

## 4. Apprenticeship & Field Work

### Apprenticeship

**Definition:** The practical training phase of a [Mentorship](#mentorship) where a [Learner](#learner) with `Apprentice` [Learner Status](#learner-status) performs real work on actual client sites under the [Master](#master)'s supervision. An Apprenticeship encompasses all scheduled [Apprenticeship Sessions](#apprenticeship-session) for a given Mentorship.

**Context:** Apprenticeship is the defining feature of this domain — it distinguishes this platform from traditional online learning. The learner applies theoretical knowledge from the [Learning Program](#learning-program) to real-world tasks (e.g., a plumbing apprentice fixing a client's pipes). The Master supervises each session, potentially remotely, and evaluates the learner's performance. The Apprenticeship has its own progress tracking ([Apprenticeship Progress](#apprenticeship-progress)) separate from theoretical [Learning Progress](#learning-progress). Transitioning from `Apprentice` to `Specialist` [Learner Status](#learner-status) requires completing a minimum number of sessions with satisfactory evaluations.

**Code mapping:**

- Python: `Apprenticeship` entity in `learning/domain/apprenticeship.py`
 `Apprenticeship` class in `packages/learning/src/domain/apprenticeship.ts`

**Related terms:** [Apprenticeship Session](#apprenticeship-session), [Field Assignment](#field-assignment), [Supervision Mode](#supervision-mode), [Session Evaluation](#session-evaluation), [Apprenticeship Progress](#apprenticeship-progress), [Mentorship](#mentorship)

---

### Apprenticeship Session

**Definition:** A single scheduled instance of practical field work within an [Apprenticeship](#apprenticeship). Each session has a date, time, estimated duration, [Session Location](#session-location), assigned [Field Assignment](#field-assignment), and designated [Supervision Mode](#supervision-mode).

**Context:** Sessions are the atomic unit of apprenticeship. The Master (or Learner, with Master's approval) schedules sessions using the Master's [Availability Schedule](#availability-schedule). A session lifecycle: `Scheduled` → `InProgress` → `Completed` | `Cancelled` | `NoShow`. After completion, the Master submits a [Session Evaluation](#session-evaluation). Sessions are location-based — each session happens at a specific client site or workshop. The system tracks whether the learner arrived on time, completed the assigned work, and any issues that arose.

**Code mapping:**

- Python: `ApprenticeshipSession` entity in `learning/domain/apprenticeship_session.py`
 `ApprenticeshipSession` class in `packages/learning/src/domain/apprenticeship-session.ts`

**Related terms:** [Apprenticeship](#apprenticeship), [Field Assignment](#field-assignment), [Session Location](#session-location), [Supervision Mode](#supervision-mode), [Session Evaluation](#session-evaluation), [Availability Schedule](#availability-schedule), [Apprenticeship Event](#apprenticeship-event)

---

### Field Assignment

**Definition:** A specific task or set of tasks that a [Learner](#learner) must complete during an [Apprenticeship Session](#apprenticeship-session). Examples: "Replace kitchen faucet," "Install new electrical outlet," "Diagnose and repair leaking drain."

**Context:** Field Assignments define what the learner should accomplish on site. They are created by the [Master](#master) for each session and include: a description of the work, required tools and materials, safety precautions, expected outcomes, and evaluation criteria. Assignments connect the theoretical [Lessons](#lesson) to practical application — a Master may reference specific lessons as prerequisites for an assignment. The learner may submit evidence of completion (photos, videos, notes) that the Master reviews during [Session Evaluation](#session-evaluation).

**Code mapping:**

- Python: `FieldAssignment` value object in `learning/domain/field_assignment.py`
 `FieldAssignment` interface in `packages/learning/src/domain/field-assignment.ts`

**Related terms:** [Apprenticeship Session](#apprenticeship-session), [Session Evaluation](#session-evaluation), [Lesson](#lesson), [Master](#master)

---

### Session Location

**Definition:** The physical location where an [Apprenticeship Session](#apprenticeship-session) takes place. Includes: street address, city, optional geo-coordinates (latitude/longitude), and location type (client site, workshop, training facility).

**Context:** Most apprenticeship sessions happen at real client sites — this is the key differentiator of the platform. The learner travels to the location to perform the [Field Assignment](#field-assignment). Location data is used for: scheduling logistics, travel time estimation, and post-session verification (confirming the learner was at the correct site). Geo-coordinates are obtained through an external geocoding adapter via an Anti-Corruption Layer (see [AGENTS.md 4.3](../AGENTS.md#43-context-mapping-карта-контекстов)). Location data is privacy-sensitive and must be handled according to data protection policies.

**Code mapping:**

- Python: `SessionLocation` value object in `learning/domain/session_location.py`
 `SessionLocation` interface in `packages/learning/src/domain/session-location.ts`

**Related terms:** [Apprenticeship Session](#apprenticeship-session), [Supervision Mode](#supervision-mode)

---

### Supervision Mode

**Definition:** The method by which a [Master](#master) oversees a [Learner](#learner)'s work during an [Apprenticeship Session](#apprenticeship-session). Values: `OnSite` (Master is physically present at the location), `Remote` (Master monitors and guides in real-time via video call, photos, or chat), `Deferred` (Learner works independently, Master evaluates after the session based on submitted evidence).

**Context:** Supervision Mode is a critical concept — it reflects the reality that Masters cannot always be physically present at every job site. `OnSite` is typical for a learner's first sessions — the Master accompanies them to demonstrate and correct. `Remote` is the most common mode as the learner gains experience — the Master watches via video, answers questions, and provides guidance in real-time without traveling. `Deferred` is for advanced apprentices who can work independently — the Master reviews photos, notes, and results afterward. The Master chooses the mode when scheduling each session; it may evolve over the course of the apprenticeship as the learner's skills develop.

**Code mapping:**

- Python: `SupervisionMode` enum in `learning/domain/supervision_mode.py`
 `SupervisionMode` union type in `packages/learning/src/domain/supervision-mode.ts`

**Related terms:** [Apprenticeship Session](#apprenticeship-session), [Master](#master), [Session Evaluation](#session-evaluation)

---

### Session Evaluation

**Definition:** The [Master](#master)'s formal assessment of a [Learner](#learner)'s performance during a completed [Apprenticeship Session](#apprenticeship-session). Includes: a numerical score, a pass/fail verdict, written feedback, specific skill observations, and recommendations for improvement.

**Context:** Session Evaluations are the primary mechanism for tracking practical skill development. The Master submits an evaluation after each completed session. The evaluation covers: quality of work, adherence to safety protocols, problem-solving ability, communication, time management, and tool usage. Evaluations feed into [Apprenticeship Progress](#apprenticeship-progress) and determine eligibility for [Learner Transition](#learner-transition) to `Specialist` status. A minimum average evaluation score is typically required for promotion. Evaluations are visible to the learner for feedback and learning.

**Code mapping:**

- Python: `SessionEvaluation` entity in `learning/domain/session_evaluation.py`
 `SessionEvaluation` class in `packages/learning/src/domain/session-evaluation.ts`

**Related terms:** [Apprenticeship Session](#apprenticeship-session), [Master](#master), [Apprenticeship Progress](#apprenticeship-progress), [Learner Transition](#learner-transition)

---

### Apprenticeship Progress

**Definition:** An aggregated view of a [Learner](#learner)'s practical training performance across all [Apprenticeship Sessions](#apprenticeship-session) within a [Mentorship](#mentorship). Tracks: total sessions completed, average [Session Evaluation](#session-evaluation) score, sessions by [Supervision Mode](#supervision-mode), sessions by [Field Assignment](#field-assignment) type, and readiness for promotion to `Specialist`.

**Context:** Apprenticeship Progress is separate from theoretical [Learning Progress](#learning-progress) — it measures hands-on competence rather than content consumption. The Master uses this view to decide when a learner is ready to advance from `Apprentice` to `Specialist`. The platform may define minimum thresholds (e.g., "at least 10 sessions with average score ≥ 4.0 and at least 3 sessions in `Deferred` mode with passing evaluation").

**Code mapping:**

- Python: `ApprenticeshipProgress` value object in `learning/domain/apprenticeship_progress.py`
 `ApprenticeshipProgress` interface in `packages/learning/src/domain/apprenticeship-progress.ts`

**Related terms:** [Apprenticeship](#apprenticeship), [Apprenticeship Session](#apprenticeship-session), [Session Evaluation](#session-evaluation), [Learner Transition](#learner-transition), [Learning Progress](#learning-progress)

---

### Apprenticeship Event

**Definition:** A domain event emitted when a significant action occurs within an [Apprenticeship](#apprenticeship). A specialized subset of [Learning Events](#learning-event).

**Context:** Examples: `SessionScheduled` (new session planned), `SessionStarted` (learner checked in at location), `SessionCompleted` (work finished), `SessionCancelled` (session cancelled by Master or Learner), `SessionNoShow` (learner did not appear), `EvaluationSubmitted` (Master submitted session evaluation), `ApprenticePromotedToSpecialist` (learner met all apprenticeship requirements). Each event carries the `MentorshipId`, `LearnerId`, `MasterId`, `SessionId` (where applicable), and event-specific payload.

**Code mapping:**

- Python: `ApprenticeshipEvent` subclasses of `LearningEvent` in `learning/domain/events.py` (`SessionScheduledEvent`, `EvaluationSubmittedEvent`, etc.)
 Apprenticeship-specific types within `LearningEvent` union in `packages/learning/src/domain/events.ts`

**Related terms:** [Apprenticeship Session](#apprenticeship-session), [Session Evaluation](#session-evaluation), [Learning Event](#learning-event)

---

## 5. Progress & Completion

### Learning Progress

**Definition:** The overall progress of a [Learner](#learner) through the theoretical content of a [Learning Program](#learning-program) within a specific [Mentorship](#mentorship). Measured as the percentage of [Lessons](#lesson) completed, with optional per-[Module](#module) breakdown.

**Context:** Learning Progress tracks content consumption (lessons viewed, assignments submitted, quizzes passed), not practical skill development — that is tracked separately in [Apprenticeship Progress](#apprenticeship-progress). Progress is calculated as `completed lessons / total lessons * 100%`. For programs with modules, per-module progress is also available. Progress updates are emitted as [Progress Events](#progress-event). A minimum Learning Progress threshold is typically a prerequisite for the `Active` → `Apprentice` [Learner Transition](#learner-transition) (e.g., "complete at least 60% of theory before starting field work").

**Code mapping:**

- Python: `LearningProgress` value object in `learning/domain/learning_progress.py`
 `LearningProgress` interface in `packages/learning/src/domain/learning-progress.ts`

**Related terms:** [Lesson Completion](#lesson-completion), [Apprenticeship Progress](#apprenticeship-progress), [Learner](#learner), [Learning Program](#learning-program), [Progress Event](#progress-event)

---

### Lesson Completion

**Definition:** A record indicating that a [Learner](#learner) has finished a specific [Lesson](#lesson). Captures: the lesson ID, completion timestamp, and — for graded lessons ([Assignment](#lesson-type), [Quiz](#lesson-type)) — the submission result and score.

**Context:** Lesson Completion is the building block of [Learning Progress](#learning-progress). Different [Lesson Types](#lesson-type) have different completion rules: `Video` is complete when the learner finishes watching (or reaches a minimum watch percentage); `Text` is complete when the learner marks it as read; `Exercise` is self-marked; `Assignment` is complete when the Master grades the submission; `Quiz` is complete when the learner submits answers (auto-graded). A lesson can be completed only once per learner (no re-completions, though retakes of quizzes/assignments may create new records).

**Code mapping:**

- Python: `LessonCompletion` entity in `learning/domain/lesson_completion.py`
 `LessonCompletion` class in `packages/learning/src/domain/lesson-completion.ts`

**Related terms:** [Lesson](#lesson), [Lesson Type](#lesson-type), [Learning Progress](#learning-progress), [Progress Event](#progress-event)

---

### Program Completion

**Definition:** A record indicating that a [Learner](#learner) has successfully completed an entire [Learning Program](#learning-program) within a [Mentorship](#mentorship). Captures: the program ID, completion date, final evaluation from the Master, and whether a [Certificate](#certificate) was issued.

**Context:** Program Completion is the end-goal of a mentorship. It is triggered when all [Completion Criteria](#completion-criteria) are satisfied. Program Completion is a necessary (but not always sufficient) condition for [Graduation](#graduation) — the Master may require additional sign-off. Upon completion, the system automatically checks certificate eligibility and issues one if applicable. Program Completion emits a `ProgramCompleted` [Progress Event](#progress-event).

**Code mapping:**

- Python: `ProgramCompletion` entity in `learning/domain/program_completion.py`
 `ProgramCompletion` class in `packages/learning/src/domain/program-completion.ts`

**Related terms:** [Learning Program](#learning-program), [Completion Criteria](#completion-criteria), [Certificate](#certificate), [Graduation](#graduation), [Progress Event](#progress-event)

---

### Completion Criteria

**Definition:** A set of rules defined on a [Learning Program](#learning-program) that specify when the program is considered finished. Criteria may include: minimum percentage of [Lessons](#lesson) completed, minimum number of [Apprenticeship Sessions](#apprenticeship-session) with passing evaluations, minimum average [Session Evaluation](#session-evaluation) score, and passing a final assessment.

**Context:** Completion Criteria are configured by the [Master](#master) when creating the program. They are the single source of truth for automated [Program Completion](#program-completion) checks. The system evaluates criteria after each [Lesson Completion](#lesson-completion) or [Session Evaluation](#session-evaluation) submission. If all criteria are met, the program is marked complete. Criteria can be strict ("100% lessons + 10 sessions + average evaluation ≥ 4.0") or lenient ("80% lessons + 5 sessions"), depending on the Master's teaching philosophy.

**Code mapping:**

- Python: `CompletionCriteria` value object in `learning/domain/completion_criteria.py`
 `CompletionCriteria` interface in `packages/learning/src/domain/completion-criteria.ts`

**Related terms:** [Learning Program](#learning-program), [Program Completion](#program-completion), [Graduation](#graduation), [Lesson Completion](#lesson-completion), [Session Evaluation](#session-evaluation)

---

### Certificate

**Definition:** A formal digital document confirming that a [Learner](#learner) has completed a [Learning Program](#learning-program) or reached a specific milestone (e.g., `Specialist` [Learner Status](#learner-status)). Includes: learner name, program name, [Master](#master) name, [Specialization](#specialization), completion date, and a unique verifiable certificate ID.

**Context:** Certificates are automatically issued when [Completion Criteria](#completion-criteria) are met and [Graduation](#graduation) is confirmed. They may be verified externally via a public URL containing the certificate ID. Certificates are immutable once issued — if an error is found, the certificate is revoked and a new one is issued. The certificate PDF is generated by an infrastructure adapter (driven port) and stored in object storage. Certificate data (metadata) lives in the domain; the rendered document lives in infrastructure.

**Code mapping:**

- Python: `Certificate` entity in `learning/domain/certificate.py`
 `Certificate` class in `packages/learning/src/domain/certificate.ts`

**Related terms:** [Graduation](#graduation), [Completion Criteria](#completion-criteria), [Program Completion](#program-completion), [Learner](#learner), [Specialization](#specialization)

---

### Progress Event

**Definition:** A domain event emitted when a [Learner](#learner)'s progress changes. A specialized subset of [Learning Events](#learning-event).

**Context:** Examples: `LessonCompleted` (learner finished a lesson), `ModuleCompleted` (all lessons in a module finished), `ProgramCompleted` (all completion criteria met), `CertificateIssued` (certificate generated and available), `LearningProgressUpdated` (percentage changed). Each event carries the `MentorshipId`, `LearnerId`, `ProgramId`, and event-specific payload. Progress Events are consumed by the Learner's dashboard, the Master's monitoring view, and potentially the Billing context (e.g., milestone-based payments).

**Code mapping:**

- Python: `ProgressEvent` subclasses of `LearningEvent` in `learning/domain/events.py` (`LessonCompletedEvent`, `CertificateIssuedEvent`, etc.)
 Progress-specific types within `LearningEvent` union in `packages/learning/src/domain/events.ts`

**Related terms:** [Learning Progress](#learning-progress), [Lesson Completion](#lesson-completion), [Program Completion](#program-completion), [Certificate](#certificate), [Learning Event](#learning-event)

---

## 6. Reviews & Ratings

### Review

**Definition:** A written assessment submitted by a [Learner](#learner) about their experience with a [Master](#master) and/or a [Learning Program](#learning-program). A Review contains textual feedback and one or more numerical [Ratings](#rating) across defined [Rating Criteria](#rating-criteria).

**Context:** Reviews are submitted after the learner reaches `Graduated` or `Specialist` [Learner Status](#learner-status) — or upon dropping out (to capture negative experiences). Each Learner can submit one Review per [Mentorship](#mentorship). Reviews are visible on the [Master Profile](#master-profile) after passing [Review Moderation](#review-moderation). They serve both informational (helping future learners choose a Master) and quality control (identifying underperforming Masters) purposes.

**Code mapping:**

- Python: `Review` entity in `learning/domain/review.py`
 `Review` class in `packages/learning/src/domain/review.ts`

**Related terms:** [Rating](#rating), [Rating Criteria](#rating-criteria), [Review Moderation](#review-moderation), [Master Rating](#master-rating), [Learner](#learner), [Mentorship](#mentorship)

---

### Rating

**Definition:** A numerical score (typically 1–5) given by a [Learner](#learner) as part of a [Review](#review). Each Rating corresponds to a specific [Rating Criterion](#rating-criteria).

**Context:** A single Review contains multiple Ratings — one per criterion. Individual ratings are aggregated across all reviews to produce the [Aggregated Rating](#aggregated-rating) for each criterion and the overall [Master Rating](#master-rating). Ratings are integers (no half-stars) to simplify aggregation and comparison.

**Code mapping:**

- Python: `Rating` value object in `learning/domain/rating.py`
 `Rating` interface in `packages/learning/src/domain/rating.ts`

**Related terms:** [Review](#review), [Rating Criteria](#rating-criteria), [Aggregated Rating](#aggregated-rating), [Master Rating](#master-rating)

---

### Rating Criteria

**Definition:** The predefined dimensions along which a [Learner](#learner) evaluates a [Master](#master) in a [Review](#review). Values: `teaching_quality` (clarity of explanations, preparation of materials), `communication` (responsiveness, availability, feedback quality), `practical_preparation` (quality of apprenticeship supervision, real-world relevance), `availability` (schedule flexibility, punctuality, consistency).

**Context:** Rating Criteria are platform-defined (not per-Master) to ensure comparability across masters. They are displayed to the learner during review submission. Each criterion gets its own [Rating](#rating) score. The criteria are chosen to reflect the unique aspects of 1-on-1 mentorship with field apprenticeship — `practical_preparation` is particularly important and differentiates this from standard online course reviews.

**Code mapping:**

- Python: `RatingCriteria` enum in `learning/domain/rating_criteria.py`
 `RatingCriteria` union type in `packages/learning/src/domain/rating-criteria.ts`

**Related terms:** [Rating](#rating), [Review](#review), [Aggregated Rating](#aggregated-rating)

---

### Aggregated Rating

**Definition:** A computed average score for a [Master](#master) or a [Learning Program](#learning-program) across all submitted [Reviews](#review). Calculated per [Rating Criterion](#rating-criteria) and as an overall weighted average.

**Context:** Aggregated Rating is a read model, recalculated whenever a new [Review](#review) is submitted or moderated. It feeds the [Master Rating](#master-rating) displayed on the profile. The aggregation may be weighted: recent reviews carry more weight than old ones; reviews from `Graduated` learners may carry more weight than from `Dropped Out` learners. A minimum number of reviews (e.g., 3) is required before the aggregated rating is publicly displayed to avoid bias from a single review.

**Code mapping:**

- Python: `AggregatedRating` value object in `learning/domain/aggregated_rating.py`
 `AggregatedRating` interface in `packages/learning/src/domain/aggregated-rating.ts`

**Related terms:** [Rating](#rating), [Rating Criteria](#rating-criteria), [Master Rating](#master-rating), [Review](#review)

---

### Review Moderation

**Definition:** The process of checking a submitted [Review](#review) before it becomes publicly visible. Moderation filters spam, offensive language, personally identifiable information, and factually false claims.

**Context:** Moderation can be: automated (content filter, profanity check, PII detection), manual (platform staff review), or a combination. Reviews in moderation have status: `Pending` (submitted, awaiting check), `Approved` (passed, now visible), `Rejected` (blocked, with reason communicated to the author). The learner is notified of the moderation outcome. Rejected reviews do not count toward [Aggregated Rating](#aggregated-rating). Moderation rules are a platform-wide concern, not a per-Master setting.

**Code mapping:**

- Python: `ReviewModeration` entity in `learning/domain/review_moderation.py`
 `ReviewModeration` class in `packages/learning/src/domain/review-moderation.ts`

**Related terms:** [Review](#review), [Aggregated Rating](#aggregated-rating)

---

## 7. Mentoring Relationship

### Mentorship

**Definition:** The formal 1-on-1 relationship between a [Master](#master) and a [Learner](#learner), bound to a specific [Learning Program](#learning-program). Mentorship is the central orchestrating entity of this bounded context — it ties together enrollment, learning progress, apprenticeship, evaluations, and graduation into a single coherent lifecycle.

**Context:** A Mentorship is created when an [Enrollment](#enrollment) is activated. It encapsulates: who is teaching (Master), who is learning (Learner), what they are studying (Learning Program), the current status ([Mentorship Status](#mentorship-status)), agreed terms ([Mentorship Agreement](#mentorship-agreement)), and all progress data. A Learner can have multiple active Mentorships (with different Masters or different programs). A Master can have multiple active Mentorships up to their [Master Capacity](#master-capacity). Each Mentorship tracks its own [Learner Status](#learner-status) independently.

**Code mapping:**

- Python: `Mentorship` aggregate root in `learning/domain/mentorship.py`
 `Mentorship` class in `packages/learning/src/domain/mentorship.ts`

**Related terms:** [Master](#master), [Learner](#learner), [Learning Program](#learning-program), [Mentorship Status](#mentorship-status), [Mentorship Agreement](#mentorship-agreement), [Enrollment](#enrollment), [Learner Status](#learner-status)

---

### Mentorship Status

**Definition:** An enum representing the current state of a [Mentorship](#mentorship). Values: `Pending` (enrollment activated, awaiting start), `Active` (learning is in progress), `Paused` (temporarily suspended — e.g., learner on vacation, scheduling conflict), `Completed` (learner graduated or finished the program), `Terminated` (ended prematurely — by Master, Learner, or platform).

**Context:** Status governs what actions are permitted:
- `Pending` — Master and Learner can communicate and agree on schedule, but no lessons or sessions are tracked.
- `Active` — full functionality: lessons, assignments, apprenticeship sessions, evaluations.
- `Paused` — no new sessions can be scheduled, progress is frozen, but the relationship is preserved. Either party can request resumption.
- `Completed` — terminal successful state. Review can be submitted. Data preserved for reference.
- `Terminated` — terminal unsuccessful state. Reason is recorded. Review can still be submitted. Learner receives `Dropped Out` [Learner Status](#learner-status).

**Code mapping:**

- Python: `MentorshipStatus` enum in `learning/domain/mentorship_status.py`
 `MentorshipStatus` union type in `packages/learning/src/domain/mentorship-status.ts`

**Related terms:** [Mentorship](#mentorship), [Learner Status](#learner-status), [Review](#review)

---

### Mentorship Agreement

**Definition:** A formal agreement between a [Master](#master) and a [Learner](#learner) established at the start of a [Mentorship](#mentorship). Defines: the [Learning Program](#learning-program), expected schedule (sessions per week), estimated total duration, cost (if [Paid](#enrollment-method)), cancellation and refund policy, and mutual expectations.

**Context:** The Mentorship Agreement is accepted by both parties before the Mentorship transitions from `Pending` to `Active`. It serves as a reference for dispute resolution and sets clear expectations. For paid mentorships, the agreement includes pricing and payment schedule — the Learning context emits payment-related events that the Billing context processes. Agreements are immutable after acceptance; changes require creating an amendment (a new agreement version), acknowledged by both parties.

**Code mapping:**

- Python: `MentorshipAgreement` entity in `learning/domain/mentorship_agreement.py`
 `MentorshipAgreement` class in `packages/learning/src/domain/mentorship-agreement.ts`

**Related terms:** [Mentorship](#mentorship), [Master](#master), [Learner](#learner), [Enrollment Method](#enrollment-method)

---

### Availability Schedule

**Definition:** A [Master](#master)'s declared time slots when they are available for mentoring sessions and [Apprenticeship Sessions](#apprenticeship-session). Defines: recurring weekly availability (days and time ranges), one-off available or blocked dates, time zone, and buffer time between sessions.

**Context:** The Availability Schedule is maintained by the Master and is used when scheduling [Apprenticeship Sessions](#apprenticeship-session). Learners can only book sessions within available slots. The schedule may also indicate geographic availability (e.g., "available for on-site sessions within 50km of downtown" vs. "remote only on Fridays"). Buffer time between sessions accounts for travel when doing on-site supervision. The schedule is a living document — Masters update it as their availability changes.

**Code mapping:**

- Python: `AvailabilitySchedule` entity in `learning/domain/availability_schedule.py`
 `AvailabilitySchedule` class in `packages/learning/src/domain/availability-schedule.ts`

**Related terms:** [Master](#master), [Apprenticeship Session](#apprenticeship-session), [Master Capacity](#master-capacity)

---

### Learning Event

**Definition:** A domain event emitted when a significant action occurs within the Learning & Mentorship bounded context. Learning Events are the official contract for cross-context consumers and internal state tracking.

**Context:** Learning Events are the umbrella type for all domain events in this context. Subtypes include [Apprenticeship Events](#apprenticeship-event) and [Progress Events](#progress-event). Additional examples: `MentorshipStarted`, `MentorshipCompleted`, `MentorshipTerminated`, `MentorshipPaused`, `MentorshipResumed`, `LearnerStatusChanged`, `MasterVerified`, `MasterSuspended`, `EnrollmentCreated`, `EnrollmentPaymentRequested`. Events follow the Published Language pattern (see [AGENTS.md 4.3](../AGENTS.md#43-context-mapping-карта-контекстов)). Each event carries a timestamp, the actor's `IdentityId`, and event-specific payload.

**Code mapping:**

- Python: `LearningEvent` base dataclass in `learning/domain/events.py` with specific subclasses
 `LearningEvent` union type in `packages/learning/src/domain/events.ts` with specific types

**Related terms:** [Apprenticeship Event](#apprenticeship-event), [Progress Event](#progress-event), [Mentorship](#mentorship)

---

## Cross-Context Boundary Notes

The Learning & Mentorship bounded context interacts with other contexts through explicit contracts. The following table clarifies term boundaries:

| Learning Context Term | Other Context | Their Term | Relationship |
|---|---|---|---|
| `Master` | Auth | [`AuthUser`](./auth.md#authuser) | Linked via `IdentityId`. Learning owns specialization, verification status, teaching profile, and capacity; Auth owns credentials, sessions, and system-wide roles. |
| `Learner` | Auth | [`AuthUser`](./auth.md#authuser) | Linked via `IdentityId`. Learning owns learner status, progress, and mentorship data; Auth owns credentials and sessions. |
| `Master` / `Learner` | Project | [`Member`](./project.md#member) | A Master and Learner may both be Members of the same Project for collaboration purposes. Learning manages the educational relationship; Project manages workspace membership. The two contexts do not share models. |
| `Enrollment` (Paid) | Billing | `Payment`, `Invoice` | Learning emits `EnrollmentPaymentRequested` with amount and mentorship details. Billing processes payment and emits `PaymentCompleted`. Learning subscribes and activates the enrollment. Learning does NOT access Billing's database directly. |
| `Mentorship Agreement` (pricing) | Billing | `Subscription`, `Payment Schedule` | For recurring-payment mentorships, Billing manages the payment schedule. Learning defines the terms; Billing executes collection. |
| `Mentorship` / `Graduation` | Partnership | [`Referral`](./partnership.md#referral), [`Qualifying Event`](./partnership.md#qualifying-event) | A referral that leads to a paid Enrollment may trigger a commission in the Partnership context. Graduation may trigger an additional commission. Partnership subscribes to `EnrollmentCreated` and `LearnerGraduated` events. |
| `Master Verification` | Auth | Identity verification | Auth may verify identity documents (passport, ID). Learning verifies professional credentials (licenses, certifications, work experience) independently. The two verifications are complementary, not overlapping. |
| `Session Location` | External | Geocoding service | Location data is resolved through an external geocoding adapter (driven port) in Learning's infrastructure layer via an ACL. The domain model stores structured address data; geocoding is an infrastructure concern. |
| `Learning Event` | Monitoring | `Alert`, `Metric` | Learning emits lifecycle and progress events. Monitoring context consumes them for dashboards, alerting (e.g., "Master has 3 no-shows this month"), and platform analytics. |

**Integration rules:**

- Other contexts MUST NOT import Learning domain models directly. Use events or API contracts.
- The Learning context MUST NOT query the Billing database directly. Payment data arrives via domain events (`PaymentCompleted`, `RefundProcessed`), which Learning maps through its own Anti-Corruption Layer (see [AGENTS.md 4.3](../AGENTS.md#43-context-mapping-карта-контекстов)).
- Auth context MUST NOT contain Master verification logic. Auth verifies identity ("you are who you say you are"); Learning verifies professional competence ("you are qualified to teach plumbing"). These are separate concerns.
- The Project context MUST NOT know about Mentorships or Apprenticeships. If a Master and Learner collaborate in a Project, they do so as [Members](./project.md#member) — the Project context is unaware of their educational relationship.
- The Partnership context subscribes to Learning events (`EnrollmentCreated`, `LearnerGraduated`) to evaluate potential [Qualifying Events](./partnership.md#qualifying-event) for commission attribution. Learning does not know about referral commissions — it simply publishes events.
- [Session Location](#session-location) contains privacy-sensitive data (client addresses). It MUST NOT be exposed to contexts that do not need it. Events emitted to other contexts should include only the city/region, never the full address.
