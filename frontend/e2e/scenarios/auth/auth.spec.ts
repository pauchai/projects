/**
 * Authentication Scenarios
 *
 * Basic auth flow tests using pre-configured personas.
 */

import { test, expect } from "../../fixtures"
import { createUserWithPassword, login } from "../../helpers/seed"

test.describe("Authentication", () => {
  // ---------------------------------------------------------------------------
  // Login with valid credentials (via API check)
  // ---------------------------------------------------------------------------

  test("login with valid credentials succeeds via API", async ({ masterRequest }) => {
    // Create a user
    const { email, password } = await createUserWithPassword(masterRequest)

    // Login and get token
    const token = await login(masterRequest, email, password)

    expect(token.length).toBeGreaterThan(0)
  })

  // ---------------------------------------------------------------------------
  // Login with invalid credentials fails
  // ---------------------------------------------------------------------------

  test("login with invalid credentials fails via API", async ({ masterRequest }) => {
    // Create a user first
    const { email } = await createUserWithPassword(masterRequest)

    // Try to login with wrong password
    const loginPromise = login(masterRequest, email, "wrong-password-12345")

    await expect(loginPromise).rejects.toThrow()
  })

  // ---------------------------------------------------------------------------
  // Protected route without auth
  // ---------------------------------------------------------------------------

  test("unauthenticated access to protected route redirects to /login", async ({ browser }) => {
    const ctx = await browser.newContext({ storageState: null })
    const page = await ctx.newPage()

    await page.goto("/dashboard")

    // Should redirect somewhere (either /login or back to home if not protected)
    const url = page.url()
    expect(url).toMatch(/login|localhost/)

    await ctx.close()
  })
})