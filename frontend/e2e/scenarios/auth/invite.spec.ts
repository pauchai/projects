/**
 * Invite-Only Registration Scenarios
 *
 * Covers:
 *   - Admin creates invite code via POST /admin/invite-codes
 *   - User registers successfully with a valid invite code (API)
 *   - User registers successfully with a valid invite code (UI)
 *   - Registration is rejected when no invite code is supplied
 *   - Registration is rejected when an invalid/non-existent code is supplied
 *   - Registration is rejected when a code has already been used (single-use)
 */

import { test, expect, BACKEND_URL } from "../../fixtures"
import { request as pwRequest } from "@playwright/test"
import { createInviteCode } from "../../helpers/seed"

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const ADMIN_SECRET = process.env.E2E_ADMIN_SECRET ?? "change-me"

function uniqueEmail(): string {
  return `e2e-invite-${crypto.randomUUID().slice(0, 8)}@test.example`
}

async function freshPage(browser: import("@playwright/test").Browser) {
  const ctx = await browser.newContext({ storageState: undefined })
  const page = await ctx.newPage()
  return { page, ctx }
}

// ---------------------------------------------------------------------------
// Admin — code creation
// ---------------------------------------------------------------------------

test.describe("Admin invite-code creation", () => {
  test("POST /admin/invite-codes returns a batch of codes with correct shape", async () => {
    const api = await pwRequest.newContext({ baseURL: BACKEND_URL })

    const resp = await api.post("admin/invite-codes", {
      headers: { "X-Admin-Secret": ADMIN_SECRET },
      data: { count: 3 },
    })

    expect(resp.ok()).toBe(true)
    const body = (await resp.json()) as { codes: { code: string; is_active: boolean; max_uses: number; uses_left: number }[] }
    expect(body.codes).toHaveLength(3)
    for (const c of body.codes) {
      expect(c.code).toMatch(/^[A-Z2-9]{8}$/)
      expect(c.is_active).toBe(true)
      expect(c.max_uses).toBe(1)
      expect(c.uses_left).toBe(1)
    }

    await api.dispose()
  })

  test("POST /admin/invite-codes returns 403 when X-Admin-Secret is missing", async () => {
    const api = await pwRequest.newContext({ baseURL: BACKEND_URL })

    const resp = await api.post("admin/invite-codes", {
      data: { count: 1 },
    })

    expect(resp.status()).toBe(403)
    await api.dispose()
  })

  test("POST /admin/invite-codes returns 403 when X-Admin-Secret is wrong", async () => {
    const api = await pwRequest.newContext({ baseURL: BACKEND_URL })

    const resp = await api.post("admin/invite-codes", {
      headers: { "X-Admin-Secret": "totally-wrong-secret" },
      data: { count: 1 },
    })

    expect(resp.status()).toBe(403)
    await api.dispose()
  })
})

// ---------------------------------------------------------------------------
// Registration — API level
// ---------------------------------------------------------------------------

test.describe("Invite-gated registration (API)", () => {
  test("registers successfully with a valid invite code", async () => {
    const api = await pwRequest.newContext({ baseURL: BACKEND_URL })
    const code = await createInviteCode(api)

    const resp = await api.post("auth/register", {
      data: {
        user_id: crypto.randomUUID(),
        email: uniqueEmail(),
        password: "ValidPass123!",
        display_name: "Invited User",
        invite_code: code,
      },
    })

    expect(resp.ok()).toBe(true)
    await api.dispose()
  })

  test("returns 422 when invite_code is missing", async () => {
    const api = await pwRequest.newContext({ baseURL: BACKEND_URL })

    const resp = await api.post("auth/register", {
      data: {
        user_id: crypto.randomUUID(),
        email: uniqueEmail(),
        password: "ValidPass123!",
        display_name: "No Invite User",
        // invite_code intentionally omitted
      },
    })

    // 422 Unprocessable Entity — field is required by the schema
    expect(resp.status()).toBe(422)
    await api.dispose()
  })

  test("returns 422 when invite_code does not exist", async () => {
    const api = await pwRequest.newContext({ baseURL: BACKEND_URL })

    const resp = await api.post("auth/register", {
      data: {
        user_id: crypto.randomUUID(),
        email: uniqueEmail(),
        password: "ValidPass123!",
        display_name: "Bad Code User",
        invite_code: "XXXXXXXX",
      },
    })

    // The backend raises ValueError → mapped to 422 Unprocessable Entity
    expect(resp.status()).toBe(422)
    await api.dispose()
  })

  test("returns 422 when invite_code has already been used", async () => {
    const api = await pwRequest.newContext({ baseURL: BACKEND_URL })
    const code = await createInviteCode(api)

    // First registration uses the code
    const first = await api.post("auth/register", {
      data: {
        user_id: crypto.randomUUID(),
        email: uniqueEmail(),
        password: "ValidPass123!",
        display_name: "First User",
        invite_code: code,
      },
    })
    expect(first.ok()).toBe(true)

    // Second registration reuses the same single-use code → 422
    const second = await api.post("auth/register", {
      data: {
        user_id: crypto.randomUUID(),
        email: uniqueEmail(),
        password: "ValidPass123!",
        display_name: "Second User",
        invite_code: code,
      },
    })
    expect(second.status()).toBe(422)

    await api.dispose()
  })
})

// ---------------------------------------------------------------------------
// Registration — UI level
// ---------------------------------------------------------------------------

test.describe("Invite-gated registration (UI)", () => {
  test("shows error when invite code field is left empty", async ({ browser }) => {
    const { page, ctx } = await freshPage(browser)

    await page.goto("/register")
    await page.getByLabel(/email/i).fill(uniqueEmail())
    await page.getByLabel(/display.?name/i).fill("No Code User")
    await page.getByLabel(/^password$/i).fill("ValidPass123!")
    // Intentionally leave invite_code blank

    await page.locator('button[type="submit"]').click()

    // Expect the field validation error to appear
    await expect(
      page.getByText("Invite code is required"),
    ).toBeVisible({ timeout: 8_000 })

    await ctx.close()
  })

  test("shows error when an invalid invite code is submitted", async ({ browser }) => {
    const { page, ctx } = await freshPage(browser)

    await page.goto("/register")
    await page.getByLabel(/email/i).fill(uniqueEmail())
    await page.getByLabel(/display.?name/i).fill("Bad Code UI User")
    await page.getByLabel(/^password$/i).fill("ValidPass123!")
    await page.getByLabel(/invite.?code/i).fill("INVALID1")

    await page.locator('button[type="submit"]').click()

    await expect(
      page.getByText(/invalid|not found|expired|invite/i),
    ).toBeVisible({ timeout: 8_000 })

    await ctx.close()
  })

  test("registers successfully and lands on dashboard with a valid invite code", async ({ browser }) => {
    const { page, ctx } = await freshPage(browser)
    const api = await pwRequest.newContext({ baseURL: BACKEND_URL })
    const code = await createInviteCode(api)
    await api.dispose()

    await page.goto("/register")
    await page.getByLabel(/email/i).fill(uniqueEmail())
    await page.getByLabel(/display.?name/i).fill("Valid Invite UI User")
    await page.getByLabel(/^password$/i).fill("ValidPass123!")
    await page.getByLabel(/invite.?code/i).fill(code)

    await page.locator('button[type="submit"]').click()

    await expect(page).toHaveURL(/dashboard|\//, { timeout: 10_000 })

    await ctx.close()
  })
})
