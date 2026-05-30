/**
 * User Invite Code Generation
 *
 * Covers:
 *   API level:
 *   - POST /auth/invite-codes returns 201 with correct shape
 *   - max_uses is 1 (single-use)
 *   - generated code can be used to register a new user
 *   - generated code cannot be used twice
 *   - returns 401 when unauthenticated
 *
 *   UI level (profile page):
 *   - "Invite Someone" section is visible
 *   - clicking "Generate Invite Code" shows a code
 *   - "Copy" button copies the code to clipboard
 *   - generated code works for registration
 */

import { test, expect, BACKEND_URL } from "../../fixtures"
import { request as pwRequest } from "@playwright/test"
import { createUserWithPassword, login } from "../../helpers/seed"

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function uniqueEmail(): string {
  return `e2e-userinvite-${crypto.randomUUID().slice(0, 8)}@test.example`
}

/**
 * Register a fresh user and return an authenticated API context + token.
 * The context must be disposed by the caller.
 */
async function freshAuthenticatedApi(): Promise<{
  api: Awaited<ReturnType<typeof pwRequest.newContext>>
  token: string
}> {
  const anonApi = await pwRequest.newContext({ baseURL: BACKEND_URL })
  const user = await createUserWithPassword(anonApi)
  const token = await login(anonApi, user.email, user.password)
  await anonApi.dispose()

  const api = await pwRequest.newContext({
    baseURL: BACKEND_URL,
    extraHTTPHeaders: { Authorization: `Bearer ${token}` },
  })
  return { api, token }
}

// ---------------------------------------------------------------------------
// API tests
// ---------------------------------------------------------------------------

test.describe("POST /auth/invite-codes (API)", () => {
  test("returns 201 with code, expires_at and max_uses", async () => {
    const { api } = await freshAuthenticatedApi()

    const resp = await api.post("auth/invite-codes")

    expect(resp.status()).toBe(201)
    const body = (await resp.json()) as { code: string; expires_at: string; max_uses: number }
    expect(typeof body.code).toBe("string")
    expect(body.code.length).toBeGreaterThan(0)
    expect(typeof body.expires_at).toBe("string")
    expect(body.max_uses).toBe(1)

    await api.dispose()
  })

  test("generated code can be used to register a new user", async () => {
    const { api } = await freshAuthenticatedApi()
    const anonApi = await pwRequest.newContext({ baseURL: BACKEND_URL })

    const codeResp = await api.post("auth/invite-codes")
    expect(codeResp.status()).toBe(201)
    const { code } = (await codeResp.json()) as { code: string }

    const regResp = await anonApi.post("auth/register", {
      data: {
        email: uniqueEmail(),
        password: "ValidPass123!",
        display_name: "Invited E2E User",
        invite_code: code,
      },
    })
    expect(regResp.status()).toBe(201)

    await api.dispose()
    await anonApi.dispose()
  })

  test("generated code cannot be used twice", async () => {
    const { api } = await freshAuthenticatedApi()
    const anonApi = await pwRequest.newContext({ baseURL: BACKEND_URL })

    const codeResp = await api.post("auth/invite-codes")
    const { code } = (await codeResp.json()) as { code: string }

    // First use succeeds
    const first = await anonApi.post("auth/register", {
      data: {
        email: uniqueEmail(),
        password: "ValidPass123!",
        display_name: "First Invitee",
        invite_code: code,
      },
    })
    expect(first.status()).toBe(201)

    // Second use fails
    const second = await anonApi.post("auth/register", {
      data: {
        email: uniqueEmail(),
        password: "ValidPass123!",
        display_name: "Second Invitee",
        invite_code: code,
      },
    })
    expect(second.status()).toBe(422)

    await api.dispose()
    await anonApi.dispose()
  })

  test("returns 401 when not authenticated", async () => {
    const anonApi = await pwRequest.newContext({ baseURL: BACKEND_URL })

    const resp = await anonApi.post("auth/invite-codes")

    expect(resp.status()).toBe(401)
    await anonApi.dispose()
  })
})

// ---------------------------------------------------------------------------
// UI tests
// ---------------------------------------------------------------------------

test.describe("Profile page — invite section (UI)", () => {
  test("shows 'Invite Someone' section with generate button", async ({ outsiderPage }) => {
    await outsiderPage.goto("/profile")

    await expect(
      outsiderPage.getByText("Invite Someone"),
    ).toBeVisible({ timeout: 8_000 })

    await expect(
      outsiderPage.getByRole("button", { name: /generate invite code/i }),
    ).toBeVisible({ timeout: 8_000 })
  })

  test("clicking generate shows a code and expiry date", async ({ outsiderPage }) => {
    await outsiderPage.goto("/profile")

    await outsiderPage.getByRole("button", { name: /generate invite code/i }).click()

    // A <code> element with non-empty text appears
    const codeEl = outsiderPage.locator("code").last()
    await expect(codeEl).toBeVisible({ timeout: 8_000 })
    const codeText = await codeEl.textContent()
    expect(codeText?.trim().length).toBeGreaterThan(0)

    // Expiry date text appears
    await expect(
      outsiderPage.getByText(/expires/i),
    ).toBeVisible({ timeout: 8_000 })
  })

  test("Copy button changes label to 'Copied!' after click", async ({ outsiderPage }) => {
    await outsiderPage.goto("/profile")

    await outsiderPage.getByRole("button", { name: /generate invite code/i }).click()

    // Wait for the Copy button to appear
    const copyBtn = outsiderPage.getByRole("button", { name: /^copy$/i })
    await expect(copyBtn).toBeVisible({ timeout: 8_000 })

    await copyBtn.click()

    await expect(
      outsiderPage.getByRole("button", { name: /copied!/i }),
    ).toBeVisible({ timeout: 3_000 })
  })

  test("generated code registers a new user successfully", async ({ outsiderPage, browser }) => {
    await outsiderPage.goto("/profile")

    await outsiderPage.getByRole("button", { name: /generate invite code/i }).click()

    const codeEl = outsiderPage.locator("code").last()
    await expect(codeEl).toBeVisible({ timeout: 8_000 })
    const code = (await codeEl.textContent())?.trim() ?? ""
    expect(code.length).toBeGreaterThan(0)

    // Use the code to register in a fresh browser context
    const ctx = await browser.newContext({ storageState: undefined })
    const page = await ctx.newPage()

    await page.goto("/register")
    await page.getByLabel(/email/i).fill(uniqueEmail())
    await page.getByLabel(/display.?name/i).fill("UI-Invited User")
    await page.getByLabel(/^password$/i).fill("ValidPass123!")
    await page.getByLabel(/invite.?code/i).fill(code)
    await page.locator('button[type="submit"]').click()

    await expect(page).toHaveURL(/dashboard|\//, { timeout: 10_000 })

    await ctx.close()
  })
})
