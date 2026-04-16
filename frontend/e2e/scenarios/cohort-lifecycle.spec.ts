/**
 * Cohort Lifecycle Scenarios
 *
 * Covers the full UI journey from cohort creation to activation,
 * testing what different users see at each stage.
 *
 * Users involved:
 *   - master: creates the cohort, enrols learners, activates it
 *   - learner1: enrolled member, sees the cohort in their list
 */

import { test, expect } from "../fixtures"
import {
  createModule,
  formCohort,
  enrollLearner,
  getUserId,
} from "../helpers/seed"

test.describe("Cohort Lifecycle", () => {
  // -------------------------------------------------------------------------
  // Create a cohort via the UI
  // -------------------------------------------------------------------------

  test("master creates a cohort via the UI form and is redirected to its detail page", async ({
    masterPage,
    masterRequest,
  }) => {
    // Create a module first (cohort creation requires an existing module)
    const { moduleId } = await createModule(masterRequest)

    await masterPage.goto("/cohorts/new")

    // The form should show the module in the select
    const moduleSelect = masterPage.locator("select#moduleId")
    await expect(moduleSelect).toBeVisible()
    await moduleSelect.selectOption(moduleId)

    // Read the auto-generated cohort ID from the readonly input so we can
    // assert the URL after navigation
    const cohortIdInput = masterPage.locator("input#cohortId")
    const cohortId = await cohortIdInput.inputValue()

    await masterPage.getByRole("button", { name: "Create Cohort" }).click()

    // Should navigate to /cohorts/<cohortId>
    await expect(masterPage).toHaveURL(new RegExp(`/cohorts/${cohortId}`))
    // The cohort ID should be visible in the page header
    await expect(masterPage.getByText(cohortId)).toBeVisible()
    // Status badge should be "forming"
    await expect(masterPage.getByText("forming")).toBeVisible()
  })

  // -------------------------------------------------------------------------
  // Enrol a learner
  // -------------------------------------------------------------------------

  test("master enrols learner1 via the Enrol form and the member appears in the list", async ({
    masterPage,
    masterRequest,
  }) => {
    const learner1UserId = getUserId("learner1")
    const { moduleId } = await createModule(masterRequest)
    const cohortId = await formCohort(masterRequest, moduleId)

    await masterPage.goto(`/cohorts/${cohortId}`)

    // The Overview tab is active by default — Enrol form is visible
    const enrolInput = masterPage.getByPlaceholder("Learner user ID")
    await expect(enrolInput).toBeVisible()
    await enrolInput.fill(learner1UserId)
    await masterPage.getByRole("button", { name: "Enrol" }).click()

    // learner1's userId should appear in the members list
    await expect(masterPage.getByText(learner1UserId)).toBeVisible()
  })

  // -------------------------------------------------------------------------
  // Activate a cohort
  // -------------------------------------------------------------------------

  test("master activates the cohort and the status badge changes to 'active'", async ({
    masterPage,
    masterRequest,
  }) => {
    const learner1UserId = getUserId("learner1")
    const { moduleId } = await createModule(masterRequest)
    const cohortId = await formCohort(masterRequest, moduleId)
    await enrollLearner(masterRequest, cohortId, learner1UserId)

    await masterPage.goto(`/cohorts/${cohortId}`)

    // Should show "forming" badge initially
    await expect(masterPage.getByText("forming")).toBeVisible()

    await masterPage.getByRole("button", { name: "Activate" }).click()

    // Badge should switch to "active"
    await expect(masterPage.getByText("active")).toBeVisible()
    // "Activate" button should be gone; "Begin Completing" should appear
    await expect(masterPage.getByRole("button", { name: "Activate" })).not.toBeVisible()
    await expect(masterPage.getByRole("button", { name: "Begin Completing" })).toBeVisible()
  })

  // -------------------------------------------------------------------------
  // Learner view after enrolment
  // -------------------------------------------------------------------------

  test("learner1 sees the cohort in their cohort list after being enrolled and activated", async ({
    learner1Page,
    masterRequest,
  }) => {
    const learner1UserId = getUserId("learner1")
    const { moduleId } = await createModule(masterRequest)
    const cohortId = await formCohort(masterRequest, moduleId)
    await enrollLearner(masterRequest, cohortId, learner1UserId)

    // Even before activation, learner should see the cohort
    await learner1Page.goto("/cohorts")

    await expect(learner1Page.getByText(cohortId)).toBeVisible()
  })

  test("learner1 sees 'active' status badge after master activates the cohort", async ({
    learner1Page,
    masterRequest,
  }) => {
    const learner1UserId = getUserId("learner1")
    const { moduleId } = await createModule(masterRequest)
    const cohortId = await formCohort(masterRequest, moduleId)
    await enrollLearner(masterRequest, cohortId, learner1UserId)

    // Activate via API so we don't need the master page here
    await masterRequest.post(`/cohorts/${cohortId}/activate`)

    await learner1Page.goto(`/cohorts/${cohortId}`)

    await expect(learner1Page.getByText("active")).toBeVisible()
  })

  // -------------------------------------------------------------------------
  // Cancel a cohort
  // -------------------------------------------------------------------------

  test("master can cancel a forming cohort and the status changes to 'cancelled'", async ({
    masterPage,
    masterRequest,
  }) => {
    const { moduleId } = await createModule(masterRequest)
    const cohortId = await formCohort(masterRequest, moduleId)

    await masterPage.goto(`/cohorts/${cohortId}`)

    await masterPage.getByRole("button", { name: "Cancel" }).click()

    await expect(masterPage.getByText("cancelled")).toBeVisible()
    // All action buttons should be gone after cancellation
    await expect(masterPage.getByRole("button", { name: "Activate" })).not.toBeVisible()
    await expect(masterPage.getByRole("button", { name: "Cancel" })).not.toBeVisible()
  })
})
