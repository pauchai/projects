/**
 * Auth UI Scenarios — Register and Login forms.
 *
 * These tests exercise the browser UI flows directly.
 * API-level auth tests live in auth.spec.ts.
 */

import { test, expect, BACKEND_URL } from "../../fixtures"
import { request as pwRequest } from "@playwright/test"

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const ADMIN_SECRET = process.env.E2E_ADMIN_SECRET ?? "change-me"

/** Create a fresh unauthenticated browser context + page. */
async function freshPage(browser: import("@playwright/test").Browser) {
  const ctx = await browser.newContext({ storageState: undefined })
  const page = await ctx.newPage()
  return { page, ctx }
}

/** Generate a unique test email. */
function uniqueEmail(): string {
  return `e2e-ui-${crypto.randomUUID().slice(0, 8)}@test.example`
}

/** Obtain a single-use invite code from the admin endpoint. */
async function freshInviteCode(api: import("@playwright/test").APIRequestContext): Promise<string> {
  const resp = await api.post("admin/invite-codes", {
    headers: { "X-Admin-Secret": ADMIN_SECRET },
    data: { count: 1 },
  })
  if (!resp.ok()) throw new Error(`[auth-ui] createInviteCode failed: ${resp.status()} ${await resp.text()}`)
  const body = (await resp.json()) as { codes: { code: string }[] }
  const code = body.codes[0]?.code
  if (!code) throw new Error("[auth-ui] createInviteCode: no code in response")
  return code
}

// ---------------------------------------------------------------------------
// Register form
// ---------------------------------------------------------------------------

test.describe("Register form", () => {
  test("successful registration redirects to dashboard", async ({ browser }) => {
    const { page, ctx } = await freshPage(browser)
    const api = await pwRequest.newContext({ baseURL: BACKEND_URL })
    const inviteCode = await freshInviteCode(api)
    await api.dispose()

    await page.goto("/register")
    await page.getByLabel(/email/i).fill(uniqueEmail())
    await page.getByLabel(/display.?name/i).fill("E2E User")
    await page.getByLabel(/^password$/i).fill("ValidPass123!")
    await page.getByLabel(/invite.?code/i).fill(inviteCode)

    await page.locator('button[type="submit"]').click()

    // After successful registration, should land on dashboard or home
    await expect(page).toHaveURL(/dashboard|\//, { timeout: 10_000 })

    await ctx.close()
  })

  test("shows error when email is already registered", async ({ browser }) => {
    const { page, ctx } = await freshPage(browser)

    // Register once via API with a fresh invite code
    const email = uniqueEmail()
    const api = await pwRequest.newContext({ baseURL: BACKEND_URL })
    const inviteCode1 = await freshInviteCode(api)
    await api.post("auth/register", {
      data: { email, password: "SomePass123!", display_name: "First", invite_code: inviteCode1 },
    })

    // Second registration attempt via UI needs its own invite code
    const inviteCode2 = await freshInviteCode(api)
    await api.dispose()

    // Try to register again via UI with same email
    await page.goto("/register")
    await page.getByLabel(/email/i).fill(email)
    await page.getByLabel(/display.?name/i).fill("Second")
    await page.getByLabel(/^password$/i).fill("AnotherPass123!")
    await page.getByLabel(/confirm.?password/i).fill("AnotherPass123!")
    await page.getByLabel(/invite.?code/i).fill(inviteCode2)
    await page.locator('button[type="submit"]').click()

    // Should stay on register page and show an error
    await expect(page.getByText(/already registered|already taken|email.*exist/i)).toBeVisible({
      timeout: 8_000,
    })

    await ctx.close()
  })
})

// ---------------------------------------------------------------------------
// Login form
// ---------------------------------------------------------------------------

test.describe("Login form", () => {
  test("successful login redirects to dashboard", async ({ browser }) => {
    const { page, ctx } = await freshPage(browser)

    // Create a user via API first
    const email = uniqueEmail()
    const password = "LoginPass123!"
    const api = await pwRequest.newContext({ baseURL: BACKEND_URL })
    const inviteCode = await freshInviteCode(api)
    await api.post("auth/register", {
      data: { email, password, display_name: "Login E2E User", invite_code: inviteCode },
    })
    await api.dispose()

    await page.goto("/login")
    await page.getByLabel(/email/i).fill(email)
    await page.getByLabel(/password/i).fill(password)
    await page.locator('button[type="submit"]').click()

    await expect(page).toHaveURL(/dashboard|\//, { timeout: 10_000 })

    await ctx.close()
  })

  test("shows error for wrong password", async ({ browser }) => {
    const { page, ctx } = await freshPage(browser)

    // Create a user via API first
    const email = uniqueEmail()
    const api = await pwRequest.newContext({ baseURL: BACKEND_URL })
    const inviteCode = await freshInviteCode(api)
    await api.post("auth/register", {
      data: { email, password: "CorrectPass123!", display_name: "Wrong Pass User", invite_code: inviteCode },
    })
    await api.dispose()

    await page.goto("/login")
    await page.getByLabel(/email/i).fill(email)
    await page.getByLabel(/password/i).fill("WrongPassword999!")
    await page.locator('button[type="submit"]').click()

    await expect(
      page.getByText(/invalid|incorrect|wrong|password/i),
    ).toBeVisible({ timeout: 8_000 })

    await ctx.close()
  })

  test("shows error for non-existent email", async ({ browser }) => {
    const { page, ctx } = await freshPage(browser)

    await page.goto("/login")
    await page.getByLabel(/email/i).fill("nobody-exists@test.example")
    await page.getByLabel(/password/i).fill("SomePass123!")
    await page.locator('button[type="submit"]').click()

    await expect(
      page.getByText(/invalid|incorrect|not found|no account/i),
    ).toBeVisible({ timeout: 8_000 })

    await ctx.close()
  })
})
