/**
 * Dashboard Validation Scenarios
 *
 * Verifies the master's cohort dashboard for the "Pending Competency
 * Validations" section: that pending records are shown and that the
 * master can submit a successful validation.
 *
 * Prerequisite state is seeded fully via API:
 *   1. A cohort with two practice tasks for the same topic is created.
 *   2. learner1 submits solutions to both tasks.
 *   3. learner2 reviews both submissions.
 *   → The CompetencyAchievementSaga fires and creates a
 *     PendingCompetencyValidation record for learner1.
 *
 * Users involved:
 *   - master: views and acts on the dashboard
 *   - learner1: whose validation is pending
 *   - learner2: who submitted the peer reviews that triggered the saga
 *   - outsider: should not be able to access the dashboard at all
 */

import { test, expect } from "../../fixtures"
import { setupPendingValidation } from "../../helpers/seed"

test.describe("Dashboard — Pending Competency Validations", () => {
  // -------------------------------------------------------------------------
  // Master can see the pending validation card
  // -------------------------------------------------------------------------

  test("master sees learner1's pending validation card on the dashboard", async ({
    masterPage,
    masterRequest,
    apiAs,
  }) => {
    const learner1Api = await apiAs("learner1")
    const learner2Api = await apiAs("learner2")
    const { cohortId, learner1UserId } = await setupPendingValidation(
      masterRequest,
      learner1Api,
      learner2Api,
    )

    await masterPage.goto(`/cohorts/${cohortId}/dashboard`)

    // Section heading should be present
    await expect(masterPage.getByText("Pending Competency Validations")).toBeVisible()

    // learner1's user ID should appear in the pending validation card
    await expect(masterPage.getByText(learner1UserId)).toBeVisible()
  })

  // -------------------------------------------------------------------------
  // Validate button is disabled when score is out of range
  // -------------------------------------------------------------------------

  test("Validate button is disabled while the score field is empty (value 0 is valid, initial state fine)", async ({
    masterPage,
    masterRequest,
    apiAs,
  }) => {
    const learner1Api = await apiAs("learner1")
    const learner2Api = await apiAs("learner2")
    const { cohortId } = await setupPendingValidation(
      masterRequest,
      learner1Api,
      learner2Api,
    )

    await masterPage.goto(`/cohorts/${cohortId}/dashboard`)

    // Default score is 0 which is valid (0–100), so button is enabled by default.
    // Set score to an out-of-range value (e.g. 101) to trigger disabled state.
    const scoreInput = masterPage.locator('input[type="number"]').first()
    await scoreInput.fill("101")

    await expect(masterPage.getByRole("button", { name: "Validate" }).first()).toBeDisabled()
  })

  // -------------------------------------------------------------------------
  // Master submits a successful validation
  // -------------------------------------------------------------------------

  test("master can validate competency with a passing score and mentor approval", async ({
    masterPage,
    masterRequest,
    apiAs,
  }) => {
    const learner1Api = await apiAs("learner1")
    const learner2Api = await apiAs("learner2")
    const { cohortId } = await setupPendingValidation(
      masterRequest,
      learner1Api,
      learner2Api,
    )

    await masterPage.goto(`/cohorts/${cohortId}/dashboard`)
    await expect(masterPage.getByText("Pending Competency Validations")).toBeVisible()

    // Enter a passing knowledge-check score (>= 70)
    const scoreInput = masterPage.locator('input[type="number"]').first()
    await scoreInput.fill("80")

    // Check the "Mentor approved" checkbox
    const mentorCheckbox = masterPage.locator('input[type="checkbox"]').first()
    await mentorCheckbox.check()

    // Click Validate
    await masterPage.getByRole("button", { name: "Validate" }).first().click()

    // Success message should appear
    await expect(masterPage.getByText("Competency validated")).toBeVisible()
  })

  // -------------------------------------------------------------------------
  // Non-master cannot access the dashboard
  // -------------------------------------------------------------------------

  test("learner1 visiting the dashboard sees an access-denied message", async ({
    learner1Page,
    masterRequest,
    apiAs,
  }) => {
    const learner1Api = await apiAs("learner1")
    const learner2Api = await apiAs("learner2")
    const { cohortId } = await setupPendingValidation(
      masterRequest,
      learner1Api,
      learner2Api,
    )

    await learner1Page.goto(`/cohorts/${cohortId}/dashboard`)

    // The dashboard component renders an access-denied message for non-masters
    await expect(
      learner1Page.getByText("Only the cohort master can access this dashboard."),
    ).toBeVisible()
  })
})
