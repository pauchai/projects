/**
 * Seed helpers for E2E tests.
 *
 * Each function creates a specific domain object via the backend REST API
 * and returns its ID. All IDs are generated with crypto.randomUUID() so
 * tests are fully isolated even when run in parallel.
 *
 * Functions accept a Playwright `APIRequestContext` that is already
 * authenticated (use the `masterRequest` or `apiAs` fixtures).
 *
 * Example:
 *
 *   const moduleId = await createModule(masterRequest)
 *   const cohortId = await createCohort(masterRequest, moduleId)
 *   await enrollLearner(masterRequest, cohortId, learner1UserId)
 *   await activateCohort(masterRequest, cohortId)
 */

import fs from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"
import type { APIRequestContext } from "@playwright/test"

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const AUTH_DIR = path.join(__dirname, "../.auth")

// ---------------------------------------------------------------------------
// Read userId from a stored storageState file
// ---------------------------------------------------------------------------

export function getUserId(role: "master" | "learner1" | "learner2" | "outsider"): string {
  const raw = fs.readFileSync(path.join(AUTH_DIR, `${role}.json`), "utf8")
  const state = JSON.parse(raw) as {
    origins: { localStorage: { name: string; value: string }[] }[]
  }
  const entry = state.origins[0]?.localStorage.find((e) => e.name === "auth-storage")
  if (!entry) throw new Error(`No auth-storage entry for ${role}`)
  const parsed = JSON.parse(entry.value) as { state: { userId: string } }
  return parsed.state.userId
}

// ---------------------------------------------------------------------------
// Assertion helper — throw if response is not OK
// ---------------------------------------------------------------------------

async function assertOk(resp: Awaited<ReturnType<APIRequestContext["post"]>>, label: string) {
  if (!resp.ok()) {
    throw new Error(`[seed] ${label} failed: ${resp.status()} ${await resp.text()}`)
  }
}

// ---------------------------------------------------------------------------
// Module + Topic
// ---------------------------------------------------------------------------

/**
 * Create a module with one topic.
 * Returns `{ moduleId, topicId }`.
 */
export async function createModule(
  api: APIRequestContext,
): Promise<{ moduleId: string; topicId: string }> {
  const moduleId = crypto.randomUUID()
  const topicId = crypto.randomUUID()

  const modResp = await api.post("modules", {
    data: { module_id: moduleId, title: `E2E Module ${moduleId.slice(0, 8)}` },
  })
  await assertOk(modResp, `createModule(${moduleId})`)

  const topicResp = await api.post(`modules/${moduleId}/topics`, {
    data: {
      topic_id: topicId,
      title: "E2E Topic",
      position: 1,
      description: "Auto-generated topic for E2E tests",
    },
  })
  await assertOk(topicResp, `addTopic(${topicId})`)

  return { moduleId, topicId }
}

// ---------------------------------------------------------------------------
// Cohort
// ---------------------------------------------------------------------------

/** Form a new cohort (status: forming) and return its ID. */
export async function formCohort(
  api: APIRequestContext,
  moduleId: string,
): Promise<string> {
  const cohortId = crypto.randomUUID()
  const resp = await api.post("cohorts", {
    data: { cohort_id: cohortId, module_id: moduleId },
  })
  await assertOk(resp, `formCohort(${cohortId})`)
  return cohortId
}

/** Enrol a learner into a cohort. Returns the membership_id. */
export async function enrollLearner(
  api: APIRequestContext,
  cohortId: string,
  learnerId: string,
): Promise<string> {
  const membershipId = crypto.randomUUID()
  const resp = await api.post(`cohorts/${cohortId}/learners`, {
    data: { membership_id: membershipId, learner_id: learnerId },
  })
  await assertOk(resp, `enrollLearner(${learnerId} → ${cohortId})`)
  return membershipId
}

/** Activate a cohort (forming → active). */
export async function activateCohort(
  api: APIRequestContext,
  cohortId: string,
): Promise<void> {
  const resp = await api.post(`cohorts/${cohortId}/activate`)
  await assertOk(resp, `activateCohort(${cohortId})`)
}

// ---------------------------------------------------------------------------
// Practice Task
// ---------------------------------------------------------------------------

/** Create a practice task (status: draft) and return its task_id. */
export async function createTask(
  api: APIRequestContext,
  cohortId: string,
  topicId: string,
): Promise<string> {
  const taskId = crypto.randomUUID()
  const resp = await api.post(`cohorts/${cohortId}/tasks`, {
    data: {
      task_id: taskId,
      topic_id: topicId,
      title: `E2E Task ${taskId.slice(0, 8)}`,
      description: "Auto-generated task for E2E tests",
    },
  })
  await assertOk(resp, `createTask(${taskId})`)
  return taskId
}

/** Activate a practice task (draft → active). */
export async function activateTask(
  api: APIRequestContext,
  cohortId: string,
  taskId: string,
): Promise<void> {
  const resp = await api.post(`cohorts/${cohortId}/tasks/${taskId}/activate`)
  await assertOk(resp, `activateTask(${taskId})`)
}

/** Submit a solution to a task. Returns the submission_id. */
export async function submitSolution(
  api: APIRequestContext,
  cohortId: string,
  taskId: string,
): Promise<string> {
  const submissionId = crypto.randomUUID()
  const resp = await api.post(`cohorts/${cohortId}/tasks/${taskId}/submissions`, {
    data: { submission_id: submissionId, content: "E2E test solution content" },
  })
  await assertOk(resp, `submitSolution(${submissionId})`)
  return submissionId
}

/**
 * Submit a peer review on a submission. Returns the review_id.
 *
 * The reviewer must be an active cohort member and must NOT be the submission author.
 */
export async function submitReview(
  api: APIRequestContext,
  cohortId: string,
  taskId: string,
  submissionId: string,
): Promise<string> {
  const reviewId = crypto.randomUUID()
  const resp = await api.post(
    `cohorts/${cohortId}/tasks/${taskId}/submissions/${submissionId}/reviews`,
    {
      data: {
        review_id: reviewId,
        scores: [{ criterion: "code_quality", score: 4 }],
      },
    },
  )
  await assertOk(resp, `submitReview(${reviewId})`)
  return reviewId
}

// ---------------------------------------------------------------------------
// Compound setups
// ---------------------------------------------------------------------------

/**
 * Full active cohort with two enrolled learners and one active task.
 * Returns everything callers need to interact with the cohort in tests.
 */
export async function setupActiveCohortWithTask(
  masterApi: APIRequestContext,
  learner1Api: APIRequestContext,
): Promise<{
  moduleId: string
  topicId: string
  cohortId: string
  taskId: string
  learner1UserId: string
  learner2UserId: string
}> {
  const learner1UserId = getUserId("learner1")
  const learner2UserId = getUserId("learner2")

  const { moduleId, topicId } = await createModule(masterApi)
  const cohortId = await formCohort(masterApi, moduleId)
  await enrollLearner(masterApi, cohortId, learner1UserId)
  await enrollLearner(masterApi, cohortId, learner2UserId)
  await activateCohort(masterApi, cohortId)
  const taskId = await createTask(masterApi, cohortId, topicId)
  await activateTask(masterApi, cohortId, taskId)

  return { moduleId, topicId, cohortId, taskId, learner1UserId, learner2UserId }
}

/**
 * Active cohort without a task.
 * Used in scenarios that test cohort status UI or member visibility.
 */
export async function setupActiveCohort(
  masterApi: APIRequestContext,
): Promise<{ moduleId: string; cohortId: string; learner1UserId: string }> {
  const learner1UserId = getUserId("learner1")
  const { moduleId } = await createModule(masterApi)
  const cohortId = await formCohort(masterApi, moduleId)
  await enrollLearner(masterApi, cohortId, learner1UserId)
  await activateCohort(masterApi, cohortId)
  return { moduleId, cohortId, learner1UserId }
}

/**
 * Set up all prerequisites for a PendingCompetencyValidation to exist for learner1.
 *
 * The CompetencyAchievementSaga fires when:
 *   1. Learner has submitted to ALL practice tasks for the topic.
 *   2. Learner has received >= 2 peer reviews across those submissions.
 *
 * Strategy: create 2 tasks for the same topic → learner1 submits to both →
 * learner2 reviews both submissions.  After the second review the saga runs
 * and creates a PendingCompetencyValidation record for learner1.
 *
 * Returns `{ cohortId, topicId, learner1UserId }`.
 */
export async function setupPendingValidation(
  masterApi: APIRequestContext,
  learner1Api: APIRequestContext,
  learner2Api: APIRequestContext,
): Promise<{ cohortId: string; topicId: string; learner1UserId: string }> {
  const learner1UserId = getUserId("learner1")
  const learner2UserId = getUserId("learner2")

  const { moduleId, topicId } = await createModule(masterApi)
  const cohortId = await formCohort(masterApi, moduleId)
  await enrollLearner(masterApi, cohortId, learner1UserId)
  await enrollLearner(masterApi, cohortId, learner2UserId)
  await activateCohort(masterApi, cohortId)

  // Two tasks for the same topic — learner1 must submit to both to satisfy
  // "submitted to ALL practice tasks for this topic".
  const taskId1 = await createTask(masterApi, cohortId, topicId)
  const taskId2 = await createTask(masterApi, cohortId, topicId)
  await activateTask(masterApi, cohortId, taskId1)
  await activateTask(masterApi, cohortId, taskId2)

  // learner1 submits solutions to both tasks.
  const sub1 = await submitSolution(learner1Api, cohortId, taskId1)
  const sub2 = await submitSolution(learner1Api, cohortId, taskId2)

  // learner2 reviews both → total 2 reviews → triggers the saga.
  await submitReview(learner2Api, cohortId, taskId1, sub1)
  await submitReview(learner2Api, cohortId, taskId2, sub2)

  return { cohortId, topicId, learner1UserId }
}

// ---------------------------------------------------------------------------
// Project Collaboration
// ---------------------------------------------------------------------------

/**
 * Create a project (status: draft) and return its project_id.
 * The caller's API context becomes the project owner.
 */
export async function createProject(api: APIRequestContext): Promise<string> {
  const projectId = crypto.randomUUID()
  const resp = await api.post("projects", {
    data: {
      project_id: projectId,
      title: `E2E Project ${projectId.slice(0, 8)}`,
      description: "Auto-generated project for E2E tests",
      required_skills: [],
    },
  })
  await assertOk(resp, `createProject(${projectId})`)
  return projectId
}

/** Publish a project (draft → recruiting). */
export async function publishProject(
  api: APIRequestContext,
  projectId: string,
): Promise<void> {
  const resp = await api.post(`projects/${projectId}/publish`)
  await assertOk(resp, `publishProject(${projectId})`)
}

/**
 * Apply to a project and return the application_id.
 * The caller's API context becomes the applicant.
 */
export async function applyToProject(
  api: APIRequestContext,
  projectId: string,
): Promise<string> {
  const applicationId = crypto.randomUUID()
  const resp = await api.post(`projects/${projectId}/applications`, {
    data: {
      application_id: applicationId,
      desired_role: "member",
      motivation: "E2E test application",
    },
  })
  await assertOk(resp, `applyToProject(${applicationId} → ${projectId})`)
  return applicationId
}

// ---------------------------------------------------------------------------
// Feature Requests
// ---------------------------------------------------------------------------

/**
 * Submit a feature request (status: submitted) and return its request_id.
 * The caller's API context becomes the author.
 */
export async function createFeatureRequest(api: APIRequestContext): Promise<string> {
  const requestId = crypto.randomUUID()
  const resp = await api.post("features", {
    data: {
      request_id: requestId,
      title: `E2E Feature ${requestId.slice(0, 8)}`,
      description: "Auto-generated feature request for E2E tests",
    },
  })
  await assertOk(resp, `createFeatureRequest(${requestId})`)
  return requestId
}
