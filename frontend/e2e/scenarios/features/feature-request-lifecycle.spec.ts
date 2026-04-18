/**
 * Feature Request Lifecycle Scenarios
 *
 * Covers creating a feature request, list visibility and filters,
 * and the full status lifecycle: submitted → planned → in_progress → done,
 * plus the reject transition.
 *
 * Users involved:
 *   - master:          creates and transitions feature requests
 *   - unauthenticated: views the public feature list, cannot submit
 */

import { test, expect } from "../../fixtures"
import { createFeatureRequest } from "../../helpers/seed"

test.describe("Feature Request Lifecycle", () => {
  // ---------------------------------------------------------------------------
  // Create via UI
  // ---------------------------------------------------------------------------

  test("master creates a feature request via the UI and it has status 'submitted'", async ({
    masterPage,
  }) => {
    await masterPage.goto("/features/new")

    await masterPage.locator("input#title").fill("E2E Feature Request")
    await masterPage.locator("textarea#description").fill("This is a description for the E2E feature request.")
    await masterPage.getByRole("button", { name: "Submit Request" }).click()

    // Should redirect to /features/<requestId>
    await expect(masterPage).toHaveURL(/\/features\/[0-9a-f-]+$/)
    await expect(masterPage.getByText("E2E Feature Request")).toBeVisible()
    // Status badge shows "Submitted"
    await expect(masterPage.getByText("Submitted")).toBeVisible()
  })

  // ---------------------------------------------------------------------------
  // Public list — no Submit button for unauthenticated users
  // ---------------------------------------------------------------------------

  test("feature list is visible without authentication and Submit Request button is hidden", async ({
    browser,
  }) => {
    const ctx = await browser.newContext() // unauthenticated
    const page = await ctx.newPage()

    await page.goto("/features")

    await expect(page.getByRole("heading", { name: "Feature Requests" })).toBeVisible()
    // The "Submit Request" button should not appear for unauthenticated users
    await expect(page.getByRole("link", { name: "Submit Request" })).not.toBeVisible()

    await ctx.close()
  })

  // ---------------------------------------------------------------------------
  // Filter by status
  // ---------------------------------------------------------------------------

  test("master filters feature requests by 'Submitted' status", async ({
    masterPage,
    masterRequest,
  }) => {
    const requestId = await createFeatureRequest(masterRequest)

    await masterPage.goto("/features")

    await masterPage.getByRole("button", { name: "Submitted" }).click()

    // Our newly created feature request should appear
    await expect(masterPage.getByText(new RegExp(`E2E Feature ${requestId.slice(0, 8)}`))).toBeVisible()
    // No "Planned" or "Done" badges should be visible
    await expect(masterPage.getByText("Planned")).not.toBeVisible()
    await expect(masterPage.getByText("Done")).not.toBeVisible()
  })

  // ---------------------------------------------------------------------------
  // Transition: submitted → planned
  // ---------------------------------------------------------------------------

  test("master transitions a feature request from 'submitted' to 'planned'", async ({
    masterPage,
    masterRequest,
  }) => {
    const requestId = await createFeatureRequest(masterRequest)

    await masterPage.goto(`/features/${requestId}`)

    await expect(masterPage.getByText("Submitted")).toBeVisible()

    await masterPage.getByRole("button", { name: "Plan" }).click()

    await expect(masterPage.getByText("Planned")).toBeVisible()
    await expect(masterPage.getByRole("button", { name: "Plan" })).not.toBeVisible()
  })

  // ---------------------------------------------------------------------------
  // Full lifecycle: submitted → planned → in_progress → done
  // ---------------------------------------------------------------------------

  test("master walks a feature request through the full lifecycle to 'done'", async ({
    masterPage,
    masterRequest,
  }) => {
    const requestId = await createFeatureRequest(masterRequest)

    await masterPage.goto(`/features/${requestId}`)

    // submitted → planned
    await masterPage.getByRole("button", { name: "Plan" }).click()
    await expect(masterPage.getByText("Planned")).toBeVisible()

    // planned → in_progress
    await masterPage.getByRole("button", { name: "Start Work" }).click()
    await expect(masterPage.getByText("In Progress")).toBeVisible()

    // in_progress → done
    await masterPage.getByRole("button", { name: "Mark Done" }).click()
    await expect(masterPage.getByText("Done")).toBeVisible()

    // No more transition buttons
    await expect(masterPage.getByRole("button", { name: "Mark Done" })).not.toBeVisible()
  })

  // ---------------------------------------------------------------------------
  // Reject transition
  // ---------------------------------------------------------------------------

  test("master rejects a feature request and the status changes to 'rejected'", async ({
    masterPage,
    masterRequest,
  }) => {
    const requestId = await createFeatureRequest(masterRequest)

    await masterPage.goto(`/features/${requestId}`)

    await masterPage.getByRole("button", { name: "Reject" }).click()

    await expect(masterPage.getByText("Rejected")).toBeVisible()
    // No further transitions available
    await expect(masterPage.getByRole("button", { name: "Reject" })).not.toBeVisible()
    await expect(masterPage.getByRole("button", { name: "Plan" })).not.toBeVisible()
  })
})
