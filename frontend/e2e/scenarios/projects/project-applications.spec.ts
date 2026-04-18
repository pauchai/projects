/**
 * Project Applications Scenarios
 *
 * Covers the full application management flow: applying, accepting/rejecting,
 * changing a member's role, and removing a member.
 *
 * Users involved:
 *   - master:   owns the project, reviews applications, manages members
 *   - learner1: applies to the project
 */

import { test, expect } from "../../fixtures"
import { createProject, publishProject, applyToProject, getUserId } from "../../helpers/seed"

test.describe("Project Applications", () => {
  // ---------------------------------------------------------------------------
  // Apply via UI
  // ---------------------------------------------------------------------------

  test("learner1 applies to a recruiting project via the UI", async ({
    learner1Page,
    masterRequest,
  }) => {
    const projectId = await createProject(masterRequest)
    await publishProject(masterRequest, projectId)

    await learner1Page.goto(`/projects/${projectId}`)

    // The "Apply to join" button is visible for recruiting projects
    await learner1Page.getByRole("button", { name: "Apply to join" }).click()

    // The application card appears - locate it and check submit button inside
    const appCard = learner1Page.locator("form").locator("..") // card containing the form
    await appCard.getByRole("button", { name: "Submit Application" }).click()

    // After submitting, wait for page to refresh and show confirmation
    await learner1Page.waitForURL(new RegExp(`/projects/${projectId}$`))
    // Either the confirmation shows OR the button is gone (different assertion)
    await expect(learner1Page.getByRole("button", { name: "Apply to join" })).not.toBeVisible()
  })

  // ---------------------------------------------------------------------------
  // Accept an application
  // ---------------------------------------------------------------------------

  test("master accepts a pending application and its status changes to 'accepted'", async ({
    masterPage,
    masterRequest,
    apiAs,
  }) => {
    const projectId = await createProject(masterRequest)
    await publishProject(masterRequest, projectId)

    const learner1Api = await apiAs("learner1")
    await applyToProject(learner1Api, projectId)

    await masterPage.goto(`/projects/${projectId}/applications`)

    // The pending application card should show learner1's userId
    const learner1UserId = getUserId("learner1")
    await expect(masterPage.getByText(learner1UserId)).toBeVisible()

    await masterPage.getByRole("button", { name: "Accept" }).click()

    // Badge should update to "accepted"
    await expect(masterPage.getByText("accepted")).toBeVisible()
  })

  // ---------------------------------------------------------------------------
  // Reject an application
  // ---------------------------------------------------------------------------

  test("master rejects a pending application and its status changes to 'rejected'", async ({
    masterPage,
    masterRequest,
    apiAs,
  }) => {
    const projectId = await createProject(masterRequest)
    await publishProject(masterRequest, projectId)

    const learner1Api = await apiAs("learner1")
    await applyToProject(learner1Api, projectId)

    await masterPage.goto(`/projects/${projectId}/applications`)

    await masterPage.getByRole("button", { name: "Reject" }).click()

    await expect(masterPage.getByText("rejected")).toBeVisible()
  })

  // ---------------------------------------------------------------------------
  // Change a member's role
  // ---------------------------------------------------------------------------

  test("master changes a member's role and the change is saved", async ({
    masterPage,
    masterRequest,
    apiAs,
  }) => {
    // Seed: publish project, apply, accept so learner1 becomes a member
    const projectId = await createProject(masterRequest)
    await publishProject(masterRequest, projectId)

    const learner1Api = await apiAs("learner1")
    const applicationId = await applyToProject(learner1Api, projectId)

    // Accept via API
    await masterRequest.post(`projects/${projectId}/applications/${applicationId}/accept`)

    await masterPage.goto(`/projects/${projectId}/applications`)

    // Find the member card - use exact text to avoid strict mode (appears in two places)
    const learner1UserId = getUserId("learner1")
    // Target the Members section only, not the application card that has same ID
    const membersSection = masterPage.locator("section").filter({ hasText: "Members" })
    const memberRow = membersSection.locator("div").filter({ hasText: learner1UserId }).first()

    const roleSelect = memberRow.locator("select")
    await roleSelect.selectOption("mentor")

    await memberRow.getByRole("button", { name: "Save" }).click()

    // After save the button should be disabled (roles match)
    await expect(memberRow.getByRole("button", { name: "Save" })).toBeDisabled()
  })

  // ---------------------------------------------------------------------------
  // Remove a member
  // ---------------------------------------------------------------------------

  test("master removes a member and they disappear from the members list", async ({
    masterPage,
    masterRequest,
    apiAs,
  }) => {
    const projectId = await createProject(masterRequest)
    await publishProject(masterRequest, projectId)

    const learner1Api = await apiAs("learner1")
    const applicationId = await applyToProject(learner1Api, projectId)
    await masterRequest.post(`projects/${projectId}/applications/${applicationId}/accept`)

    await masterPage.goto(`/projects/${projectId}/applications`)

    const learner1UserId = getUserId("learner1")
    // Target the Members section only
    const membersSection = masterPage.locator("section").filter({ hasText: "Members" })
    await expect(membersSection.getByText(learner1UserId)).toBeVisible()

    // Find the row with the Remove button in the Members section
    const memberRow = membersSection.locator("div").filter({ hasText: learner1UserId }).first()

    // Accept the confirm dialog automatically
    masterPage.once("dialog", (dialog) => dialog.accept())
    await memberRow.getByRole("button", { name: "Remove" }).click()

    await expect(membersSection.getByText(learner1UserId)).not.toBeVisible()
  })
})
