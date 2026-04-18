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

// ---------------------------------------------------------------------------
// Register form
// ---------------------------------------------------------------------------

test.describe("Register form", () => {
  test("successful registration redirects to dashboard", async ({ browser }) => {
    const { page, ctx } = await freshPage(browser)

    await page.goto("/register")
    await page.getByLabel(/email/i).fill(uniqueEmail())
    await page.getByLabel(/display.?name/i).fill("E2E User")
    await page.getByLabel(/^password$/i).fill("ValidPass123!")

    await page.getByRole("button", { name: /register|sign up|create/i }).click()

    // After successful registration, should land on dashboard or home
    await expect(page).toHaveURL(/dashboard|\//, { timeout: 10_000 })

    await ctx.close()
  })

  test("shows error when email is already registered", async ({ browser }) => {
    const { page, ctx } = await freshPage(browser)

    // Register once via API
    const email = uniqueEmail()
    const api = await pwRequest.newContext({ baseURL: BACKEND_URL })
    await api.post("auth/register", {
      data: { email, password: "SomePass123!", display_name: "First" },
    })
    await api.dispose()

    // Try to register again via UI with same email
    await page.goto("/register")
    await page.getByLabel(/email/i).fill(email)
    await page.getByLabel(/display.?name/i).fill("Second")
    await page.getByLabel(/^password$/i).fill("AnotherPass123!")
    await page.getByRole("button", { name: /register|sign up|create/i }).click()

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
    await api.post("auth/register", {
      data: { email, password, display_name: "Login E2E User" },
    })
    await api.dispose()

    await page.goto("/login")
    await page.getByLabel(/email/i).fill(email)
    await page.getByLabel(/password/i).fill(password)
    await page.getByRole("button", { name: /log.?in|sign.?in/i }).click()

    await expect(page).toHaveURL(/dashboard|\//, { timeout: 10_000 })

    await ctx.close()
  })

  test("shows error for wrong password", async ({ browser }) => {
    const { page, ctx } = await freshPage(browser)

    // Create a user via API first
    const email = uniqueEmail()
    const api = await pwRequest.newContext({ baseURL: BACKEND_URL })
    await api.post("auth/register", {
      data: { email, password: "CorrectPass123!", display_name: "Wrong Pass User" },
    })
    await api.dispose()

    await page.goto("/login")
    await page.getByLabel(/email/i).fill(email)
    await page.getByLabel(/password/i).fill("WrongPassword999!")
    await page.getByRole("button", { name: /log.?in|sign.?in/i }).click()

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
    await page.getByRole("button", { name: /log.?in|sign.?in/i }).click()

    await expect(
      page.getByText(/invalid|incorrect|not found|no account/i),
    ).toBeVisible({ timeout: 8_000 })

    await ctx.close()
  })
})
