/**
 * Task Flow Scenarios — three users interact in sequence
 *
 * Covers the full practice task lifecycle from creation to peer review,
 * testing what each role sees and can do at every step.
 *
 * Users involved:
 *   - master: creates and activates the task
 *   - learner1: submits a solution to the task
 *   - learner2: submits a peer review on learner1's solution
 *   - learner1: verifies the submission shows up after submission
 */

import { test, expect } from "../fixtures"
import {
  createModule,
  formCohort,
  enrollLearner,
  activateCohort,
  createTask,
  activateTask,
  getUserId,
  setupActiveCohortWithTask,
} from "../helpers/seed"

test.describe("Task Flow", () => {
  // -------------------------------------------------------------------------
  // Master creates a task via UI
  // -------------------------------------------------------------------------

  test("master creates a task via the UI form and it appears in the task list", async ({
    masterPage,
    masterRequest,
  }) => {
    const learner1UserId = getUserId("learner1")
    const { moduleId, topicId } = await createModule(masterRequest)
    const cohortId = await formCohort(masterRequest, moduleId)
    await enrollLearner(masterRequest, cohortId, learner1UserId)
    await activateCohort(masterRequest, cohortId)

    await masterPage.goto(`/cohorts/${cohortId}`)

    // Switch to Tasks tab
    await masterPage.getByRole("button", { name: "tasks" }).click()

    // Open "New Task" form
    await masterPage.getByRole("button", { name: "+ Create Task" }).click()

    // Fill in task title
    const taskTitle = `E2E UI Task ${Date.now()}`
    await masterPage.getByPlaceholder("Task title").fill(taskTitle)

    // Select the topic from the dropdown
    await masterPage.locator("select").selectOption(topicId)

    // Submit
    await masterPage.getByRole("button", { name: "Create Task" }).click()

    // The new task should appear in the list
    await expect(masterPage.getByText(taskTitle)).toBeVisible()
    // Status badge should be "draft"
    await expect(masterPage.getByText("draft")).toBeVisible()
  })

  // -------------------------------------------------------------------------
  // Master activates a task via UI
  // -------------------------------------------------------------------------

  test("master activates a draft task and the status badge changes to 'active'", async ({
    masterPage,
    masterRequest,
  }) => {
    const learner1UserId = getUserId("learner1")
    const { moduleId, topicId } = await createModule(masterRequest)
    const cohortId = await formCohort(masterRequest, moduleId)
    await enrollLearner(masterRequest, cohortId, learner1UserId)
    await activateCohort(masterRequest, cohortId)
    await createTask(masterRequest, cohortId, topicId)

    await masterPage.goto(`/cohorts/${cohortId}`)
    await masterPage.getByRole("button", { name: "tasks" }).click()

    // The Activate button should be visible next to the draft task
    const activateBtn = masterPage.getByRole("button", { name: "Activate" })
    await expect(activateBtn).toBeVisible()
    await activateBtn.click()

    // Status should switch to "active"; Close button should appear
    await expect(masterPage.getByText("active")).toBeVisible()
    await expect(masterPage.getByRole("button", { name: "Close" })).toBeVisible()
  })

  // -------------------------------------------------------------------------
  // Learner1 submits a solution
  // -------------------------------------------------------------------------

  test("learner1 can submit a solution to an active task", async ({
    learner1Page,
    masterRequest,
    apiAs,
  }) => {
    const learner1Api = await apiAs("learner1")
    const { cohortId, taskId } = await setupActiveCohortWithTask(masterRequest, learner1Api)

    await learner1Page.goto(`/cohorts/${cohortId}`)
    await learner1Page.getByRole("button", { name: "tasks" }).click()

    // "Submit Solution" button should be visible for active task
    const submitBtn = learner1Page.getByRole("button", { name: "Submit Solution" })
    await expect(submitBtn).toBeVisible()
    await submitBtn.click()

    // A textarea should appear
    const solutionText = "My E2E solution content"
    await learner1Page.getByPlaceholder(/solution/i).fill(solutionText)

    // Confirm submit
    await learner1Page.getByRole("button", { name: "Submit" }).click()

    // After submission the task status for learner1 should reflect "submitted"
    // The solution area should show the submitted content or a status indicator
    await expect(learner1Page.getByText(/submitted/i).first()).toBeVisible()
  })

  // -------------------------------------------------------------------------
  // Learner2 submits a peer review
  // -------------------------------------------------------------------------

  test("learner2 can submit a peer review on learner1's solution", async ({
    learner2Page,
    masterRequest,
    apiAs,
  }) => {
    const learner1Api = await apiAs("learner1")
    const { cohortId, taskId } = await setupActiveCohortWithTask(masterRequest, learner1Api)

    // learner1 submits a solution via API so learner2 can review it
    const submissionId = crypto.randomUUID()
    const submissionsResp = await learner1Api.post(
      `/cohorts/${cohortId}/tasks/${taskId}/submissions`,
      { data: { submission_id: submissionId, content: "Learner1 solution for review" } },
    )
    if (!submissionsResp.ok()) {
      throw new Error(`Failed to submit solution: ${await submissionsResp.text()}`)
    }

    await learner2Page.goto(`/cohorts/${cohortId}`)
    await learner2Page.getByRole("button", { name: "tasks" }).click()

    // Learner2 should see the "Review" button for learner1's submission
    const reviewBtn = learner2Page.getByRole("button", { name: /review/i }).first()
    await expect(reviewBtn).toBeVisible()
    await reviewBtn.click()

    // Review form should open with criterion score inputs
    // The form has 3 criteria: correctness, clarity, completeness
    await expect(learner2Page.getByText(/correctness/i)).toBeVisible()

    // Submit the review
    await learner2Page.getByRole("button", { name: "Submit Review" }).click()

    // Review should be recorded — button should disappear or show confirmation
    await expect(learner2Page.getByRole("button", { name: "Submit Review" })).not.toBeVisible()
  })

  // -------------------------------------------------------------------------
  // Master can see submissions from both learners
  // -------------------------------------------------------------------------

  test("master sees task submissions from learners in the task list", async ({
    masterPage,
    masterRequest,
    apiAs,
  }) => {
    const learner1Api = await apiAs("learner1")
    const learner2Api = await apiAs("learner2")
    const { cohortId, taskId } = await setupActiveCohortWithTask(masterRequest, learner1Api)

    // Both learners submit solutions via API
    await learner1Api.post(`/cohorts/${cohortId}/tasks/${taskId}/submissions`, {
      data: { submission_id: crypto.randomUUID(), content: "Learner1 solution" },
    })
    await learner2Api.post(`/cohorts/${cohortId}/tasks/${taskId}/submissions`, {
      data: { submission_id: crypto.randomUUID(), content: "Learner2 solution" },
    })

    await masterPage.goto(`/cohorts/${cohortId}`)
    await masterPage.getByRole("button", { name: "tasks" }).click()

    const learner1UserId = getUserId("learner1")
    const learner2UserId = getUserId("learner2")

    // Master should see both learner user IDs in the submissions section
    await expect(masterPage.getByText(learner1UserId).first()).toBeVisible()
    await expect(masterPage.getByText(learner2UserId).first()).toBeVisible()
  })

  // -------------------------------------------------------------------------
  // Draft task is not submittable by learner
  // -------------------------------------------------------------------------

  test("learner1 does not see Submit Solution button on a draft task", async ({
    learner1Page,
    masterRequest,
  }) => {
    const learner1UserId = getUserId("learner1")
    const { moduleId, topicId } = await createModule(masterRequest)
    const cohortId = await formCohort(masterRequest, moduleId)
    await enrollLearner(masterRequest, cohortId, learner1UserId)
    await enrollLearner(masterRequest, cohortId, getUserId("learner2"))
    await activateCohort(masterRequest, cohortId)
    // Create the task but do NOT activate it (stays draft)
    await createTask(masterRequest, cohortId, topicId)

    await learner1Page.goto(`/cohorts/${cohortId}`)
    await learner1Page.getByRole("button", { name: "tasks" }).click()

    // Draft task — no Submit Solution button for learner
    await expect(
      learner1Page.getByRole("button", { name: "Submit Solution" }),
    ).not.toBeVisible()
  })
})
