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

    // The application form expands
    const submitBtn = learner1Page.getByRole("button", { name: "Submit Application" })
    await expect(submitBtn).toBeVisible()

    await submitBtn.click()

    // After applying the button disappears and a confirmation message appears
    await expect(learner1Page.getByText("You have already applied to this project.")).toBeVisible()
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

    // Find the member card for learner1 (non-owner) and change role to "mentor"
    const learner1UserId = getUserId("learner1")
    const memberCard = masterPage.locator("div").filter({ hasText: learner1UserId }).last()

    const roleSelect = memberCard.locator("select")
    await roleSelect.selectOption("mentor")

    await memberCard.getByRole("button", { name: "Save" }).click()

    // After save the button should be disabled (roles match) or show updated role
    await expect(memberCard.getByRole("button", { name: "Save" })).toBeDisabled()
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
    await expect(masterPage.getByText(learner1UserId)).toBeVisible()

    // Playwright: accept the confirm dialog automatically
    masterPage.once("dialog", (dialog) => dialog.accept())
    await masterPage.getByRole("button", { name: "Remove" }).click()

    await expect(masterPage.getByText(learner1UserId)).not.toBeVisible()
  })
})
