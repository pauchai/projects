/**
 * Earnings Page Scenarios
 *
 * Verifies the /me/earnings page renders correctly for authenticated users
 * and is inaccessible to unauthenticated users.
 *
 * Commissions are created only through the cohort graduation event chain
 * (requires ModuleCurator + cohort graduation), which is far too complex to
 * seed in an E2E test.  These tests therefore focus on:
 *   - Page structure and zero state (no commissions)
 *   - Route protection (unauthenticated redirect)
 *   - Release button is absent when there are no commissions
 *
 * Users involved:
 *   - master: authenticated user who visits the page
 *   - Unauthenticated: should be redirected to /login
 */

import { test, expect } from "../fixtures"

test.describe("Earnings Page", () => {
  // -------------------------------------------------------------------------
  // Page structure — authenticated user, zero commissions
  // -------------------------------------------------------------------------

  test("authenticated user sees the My Earnings heading and zero-state summary", async ({
    masterPage,
  }) => {
    await masterPage.goto("/me/earnings")

    // Page heading
    await expect(masterPage.getByRole("heading", { name: "My Earnings" })).toBeVisible()

    // Summary cards — both should display "0.00" when there are no commissions
    await expect(masterPage.getByText("Pending")).toBeVisible()
    await expect(masterPage.getByText("Released")).toBeVisible()
    await expect(masterPage.getByText("0.00").first()).toBeVisible()
  })

  test("authenticated user sees 'No commissions yet.' when there are no earnings", async ({
    masterPage,
  }) => {
    await masterPage.goto("/me/earnings")

    // Empty list message
    await expect(masterPage.getByText("No commissions yet.")).toBeVisible()
  })

  test("no Release button is shown when there are no commissions", async ({
    masterPage,
  }) => {
    await masterPage.goto("/me/earnings")

    await expect(masterPage.getByRole("button", { name: "Release" })).not.toBeVisible()
  })

  // -------------------------------------------------------------------------
  // Route protection
  // -------------------------------------------------------------------------

  test("unauthenticated user is redirected to /login when visiting /me/earnings", async ({
    browser,
  }) => {
    // Fresh context — no storageState means no auth token in localStorage
    const ctx = await browser.newContext()
    const page = await ctx.newPage()

    await page.goto("/me/earnings")

    await expect(page).toHaveURL(/\/login/)
    await ctx.close()
  })

  // -------------------------------------------------------------------------
  // Learner1 also has a zero state on their own earnings page
  // -------------------------------------------------------------------------

  test("learner1 also sees the My Earnings page with zero commissions", async ({
    learner1Page,
  }) => {
    await learner1Page.goto("/me/earnings")

    await expect(learner1Page.getByRole("heading", { name: "My Earnings" })).toBeVisible()
    await expect(learner1Page.getByText("No commissions yet.")).toBeVisible()
  })
})
