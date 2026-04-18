/**
 * Update Profile — PATCH /auth/me UI tests.
 *
 * Covers the Edit Profile form on /profile:
 * - Change display name
 * - Change email (key scenario: Telegram user with synthetic email)
 * - Duplicate email is rejected with an inline error
 * - Cancel discards changes
 */

import { test, expect, BACKEND_URL } from "../../fixtures"
import { request as pwRequest } from "@playwright/test"

const ADMIN_SECRET = process.env.E2E_ADMIN_SECRET ?? "change-me"

/** Create a fresh unauthenticated API context and register a new user. */
async function createUser(email: string, displayName: string, password = "TestPass123!") {
  const api = await pwRequest.newContext({ baseURL: BACKEND_URL })
  // Obtain a fresh invite code before registering
  const invResp = await api.post("admin/invite-codes", {
    headers: { "X-Admin-Secret": ADMIN_SECRET },
    data: { count: 1 },
  })
  const invBody = (await invResp.json()) as { codes: { code: string }[] }
  const inviteCode = invBody.codes[0]?.code
  const res = await api.post("auth/register", {
    data: { email, password, display_name: displayName, invite_code: inviteCode },
  })
  await api.dispose()
  return res
}

/** Generate a unique test email. */
function uniqueEmail(): string {
  return `e2e-profile-${crypto.randomUUID().slice(0, 8)}@test.example`
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Open a fresh browser context, log in as a given user, navigate to /profile. */
async function loginAndOpenProfile(
  browser: import("@playwright/test").Browser,
  email: string,
  password: string,
) {
  const ctx = await browser.newContext({ storageState: undefined })
  const page = await ctx.newPage()

  await page.goto("/login")
  await page.getByLabel(/email/i).fill(email)
  await page.getByLabel(/password/i).fill(password)
  await page.locator('button[type="submit"]').click()
  await expect(page).not.toHaveURL(/\/login/, { timeout: 10_000 })

  await page.goto("/profile")
  await expect(page.getByRole("button", { name: /edit profile/i })).toBeVisible({ timeout: 8_000 })

  return { page, ctx }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

test.describe("Edit Profile form", () => {
  test("can change display name", async ({ browser }) => {
    const email = uniqueEmail()
    const password = "TestPass123!"
    await createUser(email, "Original Name", password)

    const { page, ctx } = await loginAndOpenProfile(browser, email, password)

    await page.getByRole("button", { name: /edit profile/i }).click()

    const nameInput = page.getByLabel(/display.?name/i)
    await nameInput.clear()
    await nameInput.fill("Updated Name")

    await page.getByRole("button", { name: /^save$/i }).click()

    // Form closes and new name is displayed
    await expect(page.getByRole("button", { name: /edit profile/i })).toBeVisible({ timeout: 8_000 })
    await expect(page.getByRole("heading", { name: "Updated Name" })).toBeVisible()

    await ctx.close()
  })

  test("can change email", async ({ browser }) => {
    const oldEmail = uniqueEmail()
    const newEmail = uniqueEmail()
    const password = "TestPass123!"
    await createUser(oldEmail, "Email Changer", password)

    const { page, ctx } = await loginAndOpenProfile(browser, oldEmail, password)

    await page.getByRole("button", { name: /edit profile/i }).click()

    const emailInput = page.getByLabel(/^email$/i)
    await emailInput.clear()
    await emailInput.fill(newEmail)

    await page.getByRole("button", { name: /^save$/i }).click()

    // Form closes and new email is visible
    await expect(page.getByRole("button", { name: /edit profile/i })).toBeVisible({ timeout: 8_000 })
    await expect(page.getByText(newEmail)).toBeVisible()

    await ctx.close()
  })

  test("shows inline error when email is already taken", async ({ browser }) => {
    const email1 = uniqueEmail()
    const email2 = uniqueEmail()
    const password = "TestPass123!"

    // Register two users
    await createUser(email1, "User One", password)
    await createUser(email2, "User Two", password)

    // Log in as user2 and try to claim user1's email
    const { page, ctx } = await loginAndOpenProfile(browser, email2, password)

    await page.getByRole("button", { name: /edit profile/i }).click()

    const emailInput = page.getByLabel(/^email$/i)
    await emailInput.clear()
    await emailInput.fill(email1)

    await page.getByRole("button", { name: /^save$/i }).click()

    // Inline error should appear, form stays open
    await expect(page.getByText(/already taken|already registered|email.*use/i)).toBeVisible({
      timeout: 8_000,
    })
    // Form is still open
    await expect(page.getByRole("button", { name: /^save$/i })).toBeVisible()

    await ctx.close()
  })

  test("cancel discards changes", async ({ browser }) => {
    const email = uniqueEmail()
    const password = "TestPass123!"
    await createUser(email, "Stable Name", password)

    const { page, ctx } = await loginAndOpenProfile(browser, email, password)

    await page.getByRole("button", { name: /edit profile/i }).click()

    const nameInput = page.getByLabel(/display.?name/i)
    await nameInput.clear()
    await nameInput.fill("Discarded Name")

    await page.getByRole("button", { name: /cancel/i }).click()

    // Original name is still shown, form closed
    await expect(page.getByRole("button", { name: /edit profile/i })).toBeVisible()
    await expect(page.getByRole("heading", { name: "Stable Name" })).toBeVisible()
    await expect(page.getByRole("heading", { name: "Discarded Name" })).not.toBeVisible()

    await ctx.close()
  })
})
