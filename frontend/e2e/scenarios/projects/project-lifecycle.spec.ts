/**
 * Project Lifecycle Scenarios
 *
 * Covers the full status lifecycle of a project:
 * draft → recruiting → active, plus search and filter on the list page.
 *
 * Users involved:
 *   - master:        creates, publishes, and activates projects
 *   - learner1:      searches and filters the public project list
 *   - unauthenticated: views the public project list
 */

import { test, expect } from "../../fixtures"
import { createProject, publishProject } from "../../helpers/seed"

test.describe("Project Lifecycle", () => {
  // ---------------------------------------------------------------------------
  // Create a project via UI
  // ---------------------------------------------------------------------------

  test("master creates a project via the UI form and it has status 'draft'", async ({
    masterPage,
  }) => {
    await masterPage.goto("/projects/new")

    await masterPage.locator("input#title").fill("E2E UI Project")
    await masterPage.getByRole("button", { name: "Create Project" }).click()

    // Should redirect to /projects/<projectId>
    await expect(masterPage).toHaveURL(/\/projects\/[0-9a-f-]+$/)
    await expect(masterPage.getByText("E2E UI Project")).toBeVisible()
    await expect(masterPage.getByText("draft")).toBeVisible()
  })

  // ---------------------------------------------------------------------------
  // Publish a project
  // ---------------------------------------------------------------------------

  test("master publishes a draft project and the status changes to 'recruiting'", async ({
    masterPage,
    masterRequest,
  }) => {
    const projectId = await createProject(masterRequest)

    await masterPage.goto(`/projects/${projectId}`)

    await expect(masterPage.getByText("draft")).toBeVisible()

    await masterPage.getByRole("button", { name: "Publish" }).click()

    await expect(masterPage.getByText("recruiting")).toBeVisible()
    await expect(masterPage.getByRole("button", { name: "Publish" })).not.toBeVisible()
  })

  // ---------------------------------------------------------------------------
  // Public project list
  // ---------------------------------------------------------------------------

  test("project list page is accessible without authentication", async ({ browser }) => {
    const ctx = await browser.newContext() // unauthenticated
    const page = await ctx.newPage()

    await page.goto("/")

    // Page loads — heading is visible (may be 0 projects in fresh env but page renders)
    await expect(page.getByRole("heading", { name: "Projects" })).toBeVisible()

    await ctx.close()
  })

  // ---------------------------------------------------------------------------
  // Search by keyword
  // ---------------------------------------------------------------------------

  test("learner1 can search projects by keyword and see matching results", async ({
    learner1Page,
    masterRequest,
  }) => {
    const projectId = await createProject(masterRequest)
    await publishProject(masterRequest, projectId)

    await learner1Page.goto("/")

    // The project title is "E2E Project <first 8 chars>"
    const keyword = `E2E Project ${projectId.slice(0, 8)}`
    await learner1Page.getByPlaceholder("Search by keyword...").fill(keyword)

    await expect(learner1Page.getByText(new RegExp(keyword))).toBeVisible()
  })

  // ---------------------------------------------------------------------------
  // Filter by status: Recruiting
  // ---------------------------------------------------------------------------

  test("learner1 filters projects by 'Recruiting' status and only sees recruiting projects", async ({
    learner1Page,
    masterRequest,
  }) => {
    const projectId = await createProject(masterRequest)
    await publishProject(masterRequest, projectId)

    await learner1Page.goto("/")

    await learner1Page.getByRole("button", { name: "Recruiting" }).click()

    // At least our project should appear in the list
    await expect(learner1Page.getByText(new RegExp(`E2E Project ${projectId.slice(0, 8)}`))).toBeVisible()
    // No projects with "draft" badge should be visible
    await expect(learner1Page.getByText("draft")).not.toBeVisible()
  })

  // ---------------------------------------------------------------------------
  // Activate a project
  // ---------------------------------------------------------------------------

  test("master activates a recruiting project and the status changes to 'active'", async ({
    masterPage,
    masterRequest,
  }) => {
    const projectId = await createProject(masterRequest)
    await publishProject(masterRequest, projectId)

    await masterPage.goto(`/projects/${projectId}`)

    await expect(masterPage.getByText("recruiting")).toBeVisible()

    await masterPage.getByRole("button", { name: "Activate" }).click()

    await expect(masterPage.getByText("active")).toBeVisible()
    await expect(masterPage.getByRole("button", { name: "Activate" })).not.toBeVisible()
  })
})
