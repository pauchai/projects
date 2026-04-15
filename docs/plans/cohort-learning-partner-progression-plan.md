# Cohort Learning — Partner Progression System Implementation Plan

## Executive Summary

This plan covers the implementation of the **Partner Progression System** and **Hybrid Reward System** for the Cohort Learning bounded context. These features represent the core business value proposition: transforming learners into teaching partners through a structured progression path with both non-monetary and monetary incentives.

---

## Current State Analysis

### ✅ Already Implemented (MVP Core - Peer Review System)

**Commit:** `feat/cohort-learning-domain` (4 commits, 1089 tests passing)

**Domain Layer:**
- `LearningCohort`, `CohortMembership`, `CohortRole`, `CohortStatus`
- `ModuleProgression`, `Topic`, `TopicCompetency` (basic)
- `PracticeTask`, `TaskSubmission`, `PeerReview`
- `ReviewScore`, `TaskStatus`, `ReviewStatus`
- Domain Events (basic lifecycle events)

**Application Layer:**
- Cohort management: Form, Activate, Change Status, Enrol/Remove Learners
- Practice Tasks: Create, Activate, Close, Submit Solution
- Peer Review: Submit Review, Get Cohort Tasks

**Infrastructure Layer:**
- PostgreSQL repositories (SQLAlchemy imperative mapping)
- Alembic migrations
- Integration tests

**API Layer:**
- Cohort endpoints (6 endpoints)
- Practice Task endpoints (6 endpoints)

---

## 🚧 Missing Components (Per Glossary)

### 1. Partner Progression System ⭐⭐⭐ **CRITICAL**
**Missing entities:**
- `TopicExpert` entity — earned per-topic expertise status
- `PeerHelper` value object — active helping role
- `HelperMetrics` value object — helping activity aggregation
- `ModuleCurator` entity — module curation authority
- `CompetencyValidation` domain service — multi-step validation
- `CuratorPromotionService` domain service — promotion orchestration

**Missing use cases:**
- `ValidateTopicCompetencyUseCase`
- `PromoteToTopicExpertUseCase`
- `RecordHelperActivityUseCase`
- `PromoteToModuleCuratorUseCase`
- `GetHelperMetricsUseCase`

**Business value:** 🔥🔥🔥 Foundation of the partner ecosystem

---

### 2. Hybrid Reward System ⭐⭐ **HIGH**
**Missing components:**
- `ExpertReward` entity — XP, badges, credits
- `MonetaryReward` value object — commission, bonuses
- `RewardLedger` entity — append-only reward log

**Missing use cases:**
- `GrantExpertRewardUseCase`
- `CalculateCurationCommissionUseCase`
- `GetRewardBalanceUseCase`

**Missing events:**
- `ExpertRewardGranted`
- `CurationCommissionEarned`
- `QualityBonusEarned`

**Business value:** 🔥🔥 Gamification and monetization

---

### 3. Domain Sagas ⭐ **MEDIUM**
**Missing sagas:**
- Competency Achievement Saga (task → validation → expert promotion)
- Cohort Graduation Saga (completion → commission calc → role sync)
- Curator Promotion Saga (qualification → approval → cross-context sync)

**Business value:** 🔥 Cross-context coordination (deferred until other contexts ready)

---

### 4. Learning Project Integration 🚫 **V2 DEFERRED**
**Missing components:**
- `LearningProject` entity
- `RoleMapping` value object
- `ProgressSyncService`
- Anti-Corruption Layer for Projects context

**Reason:** Glossary explicitly marks as V2. Focus on partner progression first.

---

## Implementation Roadmap

### Phase A: Partner Progression Foundation ✅ **START HERE**

#### Stage 1: Domain Layer (Topic Expert)
**Scope:** Topic-level expertise and validation

**Files to create:**
- `src/cohort_learning/domain/topic_expert.py` — TopicExpert entity
- `src/cohort_learning/domain/peer_helper.py` — PeerHelper value object
- `src/cohort_learning/domain/helper_metrics.py` — HelperMetrics value object
- `src/cohort_learning/domain/competency_validation.py` — CompetencyValidation service

**Domain rules:**
- Topic Expert status is earned per-topic (one learner can be expert in Topic A, learner in Topic B)
- Competency validation requires: all tasks completed, knowledge check passed, peer review received, mentor approval
- Helper metrics track: learners helped, questions answered, tasks reviewed, average satisfaction, response time
- Expert status granted immediately upon passing validation

**Tests:** 20-25 unit tests (TDD)

---

#### Stage 2: Domain Layer (Module Curator)
**Scope:** Module-level curation and promotion

**Files to create:**
- `src/cohort_learning/domain/module_curator.py` — ModuleCurator entity
- `src/cohort_learning/domain/curator_promotion.py` — CuratorPromotionService

**Domain rules:**
- Curator promotion requires: module completion, helper metrics threshold (≥3 learners helped, ≥4.0 satisfaction), teaching trial, master approval
- Curator status is module-specific (not cross-module in V1)
- Promotion is irreversible under normal circumstances
- Curator can create/modify practice tasks, validate competency, lead cohorts under master supervision

**Tests:** 15-20 unit tests

---

#### Stage 3: Application Layer (Competency & Progression)
**Scope:** Use cases for validation and promotion

**Files to create:**
- `src/cohort_learning/application/validate_topic_competency.py`
- `src/cohort_learning/application/promote_to_topic_expert.py`
- `src/cohort_learning/application/record_helper_activity.py`
- `src/cohort_learning/application/get_helper_metrics.py`
- `src/cohort_learning/application/promote_to_module_curator.py`

**Authorization rules:**
- Validate competency: Master or Module Curator only
- Promote to Expert: Master or Module Curator only (automatic if validation passed)
- Record helper activity: triggered by domain events (PeerReviewSubmitted, etc.)
- Promote to Curator: Master only

**Tests:** 25-30 application tests (with FakeUnitOfWork)

---

#### Stage 4: Infrastructure Layer
**Scope:** Persistence for new entities

**Files to create:**
- `src/cohort_learning/infrastructure/orm.py` — add TopicExpert, ModuleCurator mappings
- `src/cohort_learning/infrastructure/sql_topic_expert_repository.py`
- `src/cohort_learning/infrastructure/sql_module_curator_repository.py`
- `migrations/versions/{hash}_add_partner_progression_tables.py` — Alembic migration

**Database schema:**
```sql
CREATE TABLE topic_experts (
    expert_id VARCHAR(255) PRIMARY KEY,
    learner_id VARCHAR(255) NOT NULL,
    topic_id VARCHAR(255) NOT NULL,
    cohort_id VARCHAR(255) NOT NULL,
    validated_at TIMESTAMPTZ NOT NULL,
    validator_id VARCHAR(255) NOT NULL,
    UNIQUE (learner_id, topic_id)
);

CREATE TABLE helper_metrics (
    learner_id VARCHAR(255) PRIMARY KEY,
    cohort_id VARCHAR(255) NOT NULL,
    learners_helped INT NOT NULL DEFAULT 0,
    questions_answered INT NOT NULL DEFAULT 0,
    tasks_reviewed INT NOT NULL DEFAULT 0,
    average_satisfaction DECIMAL(3,2),
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE module_curators (
    curator_id VARCHAR(255) PRIMARY KEY,
    learner_id VARCHAR(255) NOT NULL,
    module_id VARCHAR(255) NOT NULL,
    promoted_at TIMESTAMPTZ NOT NULL,
    promoted_by VARCHAR(255) NOT NULL,
    UNIQUE (learner_id, module_id)
);
```

**Tests:** 15-20 integration tests (with test database)

---

#### Stage 5: API Layer
**Scope:** REST endpoints for progression

**Files to modify/create:**
- `src/cohort_learning/api/schemas.py` — add request/response models
- `src/cohort_learning/api/routes/progression.py` — NEW router

**Endpoints:**
- `POST /cohorts/{cohort_id}/members/{learner_id}/validate-competency` — validate topic
- `POST /cohorts/{cohort_id}/members/{learner_id}/promote-expert` — promote to expert
- `POST /cohorts/{cohort_id}/members/{learner_id}/promote-curator` — promote to curator
- `GET /cohorts/{cohort_id}/helper-metrics` — get helper stats for all members
- `GET /cohorts/{cohort_id}/topic-experts` — list experts by topic

**Tests:** 10-15 API integration tests

---

### Phase B: Non-Monetary Rewards ⭐⭐

#### Stage 6: Domain Layer (Expert Rewards)
**Scope:** XP, badges, learning credits

**Files to create:**
- `src/cohort_learning/domain/expert_reward.py` — ExpertReward entity
- `src/cohort_learning/domain/reward_ledger.py` — RewardLedger entity
- `src/cohort_learning/domain/reward_entry.py` — RewardEntry value object

**Reward types:**
- **Experience Points (XP)** — per helping action (configurable points per action type)
- **Topic Expert Badge** — visual indicator on profile
- **Reputation Score** — composite from HelperMetrics + satisfaction
- **Learning Credits** — discounts on future enrollments (5% per 10 learners helped, max 50%)

**Domain rules:**
- Rewards are immutable once granted (append-only ledger)
- XP and credits accumulate across cohorts
- Badges are earned once per topic
- Reputation score recalculates on every helper activity

**Tests:** 15-20 unit tests

---

#### Stage 7: Application Layer (Reward Management)
**Scope:** Grant rewards, view balances

**Files to create:**
- `src/cohort_learning/application/grant_expert_reward.py`
- `src/cohort_learning/application/get_reward_balance.py`
- `src/cohort_learning/application/event_handlers/reward_auto_grant.py` — event listeners

**Auto-reward triggers:**
- `PeerReviewSubmitted` → +10 XP for reviewer (if review quality > threshold)
- `TopicExpertPromoted` → Topic Expert Badge granted
- `HelperMetricsUpdated` → Reputation score recalculated
- Every 10 learners helped → +5% learning credits (up to 50%)

**Tests:** 20-25 application tests

---

#### Stage 8: Infrastructure Layer (Rewards)
**Scope:** Persistence and event handlers

**Files to create:**
- `src/cohort_learning/infrastructure/sql_reward_ledger_repository.py`
- `migrations/versions/{hash}_add_reward_ledger_table.py`

**Database schema:**
```sql
CREATE TABLE reward_ledger (
    entry_id VARCHAR(255) PRIMARY KEY,
    learner_id VARCHAR(255) NOT NULL,
    cohort_id VARCHAR(255),
    reward_type VARCHAR(50) NOT NULL, -- 'xp', 'badge', 'credits', 'reputation'
    amount INT,                        -- XP points or credit percentage
    metadata JSONB,                    -- badge_topic_id, action_details
    granted_at TIMESTAMPTZ NOT NULL,
    triggering_event VARCHAR(255)      -- event type that triggered reward
);

CREATE INDEX idx_reward_learner ON reward_ledger (learner_id);
CREATE INDEX idx_reward_type ON reward_ledger (reward_type);
```

**Tests:** 10-15 integration tests

---

#### Stage 9: API Layer (Rewards)
**Scope:** Reward dashboard endpoints

**Files to modify/create:**
- `src/cohort_learning/api/routes/rewards.py` — NEW router

**Endpoints:**
- `GET /me/rewards` — current user's reward balance (XP, credits, badges, reputation)
- `GET /me/rewards/history` — reward ledger entries
- `GET /cohorts/{cohort_id}/leaderboard` — XP leaderboard for cohort

**Tests:** 8-12 API integration tests

---

### Phase C: Monetary Rewards Integration ⭐ **DEFERRED**

**Reason:** Requires Partnership bounded context to be implemented first.

**When to implement:**
- After Partnership context exists
- After commission calculation logic defined
- After hold period and payout rules established

**What to implement:**
- `MonetaryReward` value object
- `CalculateCurationCommissionUseCase`
- Domain events: `CurationCommissionEarned`, `QualityBonusEarned`
- Event publisher to Partnership context

---

### Phase D: Domain Sagas ⭐ **DEFERRED**

**Reason:** Requires cross-context integration (Projects, Learning, Partnership).

**When to implement:**
- After Learning Project Integration (V2)
- After Partnership context exists
- After event bus infrastructure is ready

**What to implement:**
- Competency Achievement Saga
- Cohort Graduation Saga
- Curator Promotion Saga

---

## TDD Workflow

All stages follow strict RED-GREEN-REFACTOR cycle:

1. **Domain tests first** — write failing tests for domain logic
2. **Domain implementation** — make tests pass with minimal code
3. **Application tests** — test use cases with FakeUnitOfWork
4. **Application implementation** — orchestrate domain + ports
5. **Infrastructure tests** — test repositories with test database
6. **Infrastructure implementation** — SQLAlchemy ORM + repositories
7. **API tests** — test endpoints with TestClient
8. **API implementation** — FastAPI routes + schemas

**Commit strategy:**
- Commit after each GREEN stage (domain → app → infra → API)
- Use conventional commits: `feat(cohort-learning): add topic expert validation`

---

## Acceptance Criteria

### Phase A Completion:
- [ ] Learners can achieve Topic Competency through validation
- [ ] Topic Experts can be promoted (per-topic)
- [ ] Helper Metrics are tracked automatically
- [ ] Module Curators can be promoted (master approval required)
- [ ] All new entities persisted to database
- [ ] REST endpoints for validation and promotion
- [ ] All tests passing (target: +100 tests, total ~1190)

### Phase B Completion:
- [ ] XP granted automatically on peer review submission
- [ ] Topic Expert Badges awarded on promotion
- [ ] Learning Credits accumulate per helping activity
- [ ] Reputation score calculated from HelperMetrics
- [ ] Reward Ledger is append-only and immutable
- [ ] Users can view their reward balance via API
- [ ] Cohort leaderboard displays XP rankings
- [ ] All tests passing (target: +80 tests, total ~1270)

---

## Risk Mitigation

### Risk: Over-engineering for V1
**Mitigation:** Explicitly defer Learning Project Integration and Sagas to V2. Focus on core progression only.

### Risk: Cross-context dependencies blocking progress
**Mitigation:** Use domain events as contracts, implement ACL placeholders for future Partnership integration.

### Risk: Helper Metrics calculation complexity
**Mitigation:** Start with simple counters (learners helped, tasks reviewed). Add weighted scores and satisfaction ratings in V2.

### Risk: Reward gaming (XP farming)
**Mitigation:** Implement quality checks: peer reviews require minimum quality score, satisfaction ratings from helped learners, fraud detection in V2.

---

## Success Metrics

- **Test coverage:** >90% for domain layer, >80% for application layer
- **API response time:** <200ms for all endpoints (p95)
- **Database schema:** Normalized, indexed, migration tested
- **Code quality:** Passes `ruff check`, no `Any` types, strict type hints

---

## Next Steps

1. **Immediate:** Merge current `feat/cohort-learning-domain` branch to `main`
2. **Create new branch:** `feat/cohort-learning-partner-progression`
3. **Start Phase A, Stage 1:** Topic Expert domain layer (TDD)
4. **Iterate:** Domain → Application → Infrastructure → API per stage
5. **Review after Stage 5:** Assess progress, adjust plan if needed

---

**Status:** Ready to begin Phase A  
**Estimated effort:** Phase A = 3-5 days, Phase B = 2-3 days  
**Target completion:** Phase A+B within 1 week

---

**Author:** OpenCode Agent  
**Date:** April 15, 2026  
**Version:** 1.0
