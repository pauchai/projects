/**
 * Access Control Scenarios
 *
 * Verifies that routes are properly guarded and different user roles
 * see the correct UI (or are blocked from it).
 *
 * Users involved:
 *   - Unauthenticated (no storageState)
 *   - outsider (authenticated but not a cohort member)
 *   - learner1 (active cohort member)
 *   - master (cohort creator)
 */

import { test, expect } from "../fixtures"
import {
  setupActiveCohort,
  getUserId,
} from "../helpers/seed"

test.describe("Access Control", () => {
  // -------------------------------------------------------------------------
  // Unauthenticated user
  // -------------------------------------------------------------------------

  test("unauthenticated user is redirected to /login when accessing /cohorts", async ({
    browser,
  }) => {
    // No storageState — fresh context with empty localStorage
    const ctx = await browser.newContext()
    const page = await ctx.newPage()

    await page.goto("/cohorts")

    await expect(page).toHaveURL(/\/login/)
    await ctx.close()
  })

  test("unauthenticated user is redirected to /login when accessing /cohorts/new", async ({
    browser,
  }) => {
    const ctx = await browser.newContext()
    const page = await ctx.newPage()

    await page.goto("/cohorts/new")

    await expect(page).toHaveURL(/\/login/)
    await ctx.close()
  })

  // -------------------------------------------------------------------------
  // Master vs learner: Dashboard link visibility
  // -------------------------------------------------------------------------

  test("master sees Dashboard button on their cohort page", async ({
    masterPage,
    masterRequest,
  }) => {
    const { cohortId } = await setupActiveCohort(masterRequest)

    await masterPage.goto(`/cohorts/${cohortId}`)

    // The Dashboard link is only rendered for the cohort master
    await expect(masterPage.getByRole("link", { name: "Dashboard" })).toBeVisible()
  })

  test("learner does not see Dashboard button on a cohort they belong to", async ({
    learner1Page,
    masterRequest,
  }) => {
    const { cohortId } = await setupActiveCohort(masterRequest)

    await learner1Page.goto(`/cohorts/${cohortId}`)

    await expect(learner1Page.getByRole("link", { name: "Dashboard" })).not.toBeVisible()
  })

  // -------------------------------------------------------------------------
  // Master: cohort action buttons by status
  // -------------------------------------------------------------------------

  test("master sees Activate button when cohort is forming", async ({
    masterPage,
    masterRequest,
  }) => {
    // Need a forming cohort — formCohort without activating
    const learner1UserId = getUserId("learner1")
    const { formCohort, enrollLearner, createModule } = await import("../helpers/seed")
    const { moduleId } = await createModule(masterRequest)
    const cohortId = await formCohort(masterRequest, moduleId)
    await enrollLearner(masterRequest, cohortId, learner1UserId)

    await masterPage.goto(`/cohorts/${cohortId}`)

    await expect(masterPage.getByRole("button", { name: "Activate" })).toBeVisible()
  })

  test("master sees Begin Completing button when cohort is active", async ({
    masterPage,
    masterRequest,
  }) => {
    const { cohortId } = await setupActiveCohort(masterRequest)

    await masterPage.goto(`/cohorts/${cohortId}`)

    await expect(masterPage.getByRole("button", { name: "Begin Completing" })).toBeVisible()
  })

  // -------------------------------------------------------------------------
  // Outsider visibility
  // -------------------------------------------------------------------------

  test("outsider can navigate to a cohort page without crashing", async ({
    outsiderPage,
    masterRequest,
  }) => {
    const { cohortId } = await setupActiveCohort(masterRequest)

    // The page should load (protected route passes because outsider is authenticated)
    await outsiderPage.goto(`/cohorts/${cohortId}`)

    // The cohort ID should appear somewhere on the page (header renders it)
    await expect(outsiderPage.getByText(cohortId)).toBeVisible()
  })

  test("outsider does not see Enrol form (only master sees it while forming)", async ({
    outsiderPage,
    masterRequest,
  }) => {
    const learner1UserId = getUserId("learner1")
    const { formCohort, enrollLearner, createModule } = await import("../helpers/seed")
    const { moduleId } = await createModule(masterRequest)
    const cohortId = await formCohort(masterRequest, moduleId)
    await enrollLearner(masterRequest, cohortId, learner1UserId)

    await outsiderPage.goto(`/cohorts/${cohortId}`)

    await expect(outsiderPage.getByPlaceholder("Learner user ID")).not.toBeVisible()
  })

  // -------------------------------------------------------------------------
  // Dashboard route — only master
  // -------------------------------------------------------------------------

  test("master can open /cohorts/:id/dashboard", async ({
    masterPage,
    masterRequest,
  }) => {
    const { cohortId } = await setupActiveCohort(masterRequest)

    await masterPage.goto(`/cohorts/${cohortId}/dashboard`)

    // Dashboard page renders the cohort ID in a heading or card
    await expect(masterPage.getByText(cohortId)).toBeVisible()
  })
})
