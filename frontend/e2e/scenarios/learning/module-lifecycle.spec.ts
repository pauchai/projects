/**
 * Module Lifecycle Scenarios
 *
 * Covers creating a module via the UI, verifying it appears in the list,
 * adding and removing topics, and unauthenticated access control.
 *
 * Users involved:
 *   - master: creates modules and manages topics
 *   - unauthenticated: redirected away from /modules
 */

import { test, expect } from "../../fixtures"
import { createModule } from "../../helpers/seed"

test.describe("Module Lifecycle", () => {
  // ---------------------------------------------------------------------------
  // Create a module via the UI
  // ---------------------------------------------------------------------------

  test("master creates a module via the UI form and is redirected to its detail page", async ({
    masterPage,
  }) => {
    await masterPage.goto("/modules/new")

    const titleInput = masterPage.locator("input#title")
    await expect(titleInput).toBeVisible()

    // Read the auto-generated moduleId from the readonly input
    const moduleIdInput = masterPage.locator("input#moduleId")
    const moduleId = await moduleIdInput.inputValue()

    await titleInput.fill("E2E Test Module")
    await masterPage.getByRole("button", { name: "Create Module" }).click()

    // Should navigate to /modules/<moduleId>
    await expect(masterPage).toHaveURL(new RegExp(`/modules/${moduleId}`))
    await expect(masterPage.getByText("E2E Test Module")).toBeVisible()
  })

  // ---------------------------------------------------------------------------
  // Module appears in list
  // ---------------------------------------------------------------------------

  test("new module appears in the modules list", async ({
    masterPage,
    masterRequest,
  }) => {
    const { moduleId } = await createModule(masterRequest)

    await masterPage.goto("/modules")

    // The module card should be rendered — look for the View button inside its card
    // The module title starts with "E2E Module" + first 8 chars of the id
    await expect(masterPage.getByText(new RegExp(`E2E Module ${moduleId.slice(0, 8)}`))).toBeVisible()
  })

  // ---------------------------------------------------------------------------
  // Add a topic via UI
  // ---------------------------------------------------------------------------

  test("master adds a topic via the Add Topic form and it appears in the topic list", async ({
    masterPage,
    masterRequest,
  }) => {
    const { moduleId } = await createModule(masterRequest)

    await masterPage.goto(`/modules/${moduleId}`)

    // Fill the Add Topic form
    await masterPage.locator("input#topicTitle").fill("UI-added Topic")
    await masterPage.locator("input#topicPosition").fill("2")
    await masterPage.getByRole("button", { name: "Add Topic" }).click()

    // Success message and topic should appear
    await expect(masterPage.getByText("Topic added.")).toBeVisible()
    await expect(masterPage.getByText("UI-added Topic")).toBeVisible()
  })

  // ---------------------------------------------------------------------------
  // Remove a topic via UI
  // ---------------------------------------------------------------------------

  test("master removes a topic and it disappears from the list", async ({
    masterPage,
    masterRequest,
  }) => {
    const { moduleId } = await createModule(masterRequest)

    await masterPage.goto(`/modules/${moduleId}`)

    // The seed helper already added one topic titled "E2E Topic"
    await expect(masterPage.getByText("E2E Topic")).toBeVisible()

    // Click the Remove button next to that topic
    // The Remove button is inside the list item that contains "E2E Topic"
    const topicItem = masterPage.locator("li").filter({ hasText: "E2E Topic" })
    await topicItem.getByRole("button", { name: "Remove" }).click()

    // Topic should disappear
    await expect(masterPage.getByText("E2E Topic")).not.toBeVisible()
  })

  // ---------------------------------------------------------------------------
  // Unauthenticated access control
  // ---------------------------------------------------------------------------

  test("unauthenticated user is redirected from /modules to /login", async ({ browser }) => {
    const ctx = await browser.newContext() // no storageState → unauthenticated
    const page = await ctx.newPage()

    await page.goto("/modules")

    await expect(page).toHaveURL(/\/login/)

    await ctx.close()
  })
})
