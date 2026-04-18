/**
 * Linked Accounts Scenarios
 *
 * Tests for the security settings page.
 */

import { test, expect } from "../../fixtures"

test.describe("Linked Accounts", () => {
  test("security page loads and shows credentials section", async ({ masterPage }) => {
    await masterPage.goto("/settings/security")

    await expect(masterPage.getByText("Connected Sign-in Methods")).toBeVisible()
  })

  test("security page shows add sign-in method section", async ({ masterPage }) => {
    await masterPage.goto("/settings/security")

    await expect(masterPage.getByText("Add Sign-in Method")).toBeVisible()
  })
})