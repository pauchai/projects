/**
 * Custom Playwright fixtures.
 *
 * Provides pre-authenticated page instances for each test persona so
 * individual tests never have to go through the login UI.
 *
 * Usage in a spec file:
 *
 *   import { test, expect } from "../fixtures"
 *
 *   test("master sees dashboard link", async ({ masterPage }) => {
 *     await masterPage.goto("/cohorts")
 *     ...
 *   })
 *
 * Each fixture opens an isolated BrowserContext loaded with the
 * storageState produced by global-setup.ts and cleans up after the test.
 */

import path from "node:path"
import { fileURLToPath } from "node:url"
import { test as base, type BrowserContext, type Page, request as pwRequest } from "@playwright/test"

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const AUTH_DIR = path.join(__dirname, ".auth")

export const BACKEND_URL = "http://localhost:8000"

// ---------------------------------------------------------------------------
// Auth state paths (written by global-setup.ts)
// ---------------------------------------------------------------------------

function authFile(role: string) {
  return path.join(AUTH_DIR, `${role}.json`)
}

// ---------------------------------------------------------------------------
// Fixture types
// ---------------------------------------------------------------------------

type Persona = "master" | "learner1" | "learner2" | "outsider"

interface AuthFixtures {
  /** Page authenticated as the cohort master persona. */
  masterPage: Page
  /** Page authenticated as learner1. */
  learner1Page: Page
  /** Page authenticated as learner2. */
  learner2Page: Page
  /** Page authenticated as an outsider (no cohort membership). */
  outsiderPage: Page
  /**
   * A Playwright APIRequestContext authenticated as the master persona.
   * Useful for seeding data via the backend API within a test.
   */
  masterRequest: Awaited<ReturnType<typeof pwRequest.newContext>>
  /**
   * Helper that returns a pre-authenticated APIRequestContext for any persona.
   * Reads the token from the storageState JSON written by global-setup.
   */
  apiAs: (persona: Persona) => Promise<Awaited<ReturnType<typeof pwRequest.newContext>>>
}

// ---------------------------------------------------------------------------
// Page fixture factory
// ---------------------------------------------------------------------------

async function makeAuthPage(
  browser: Parameters<typeof base.extend>[0] extends infer T
    ? never
    : never,
  role: Persona,
  use: (p: Page) => Promise<void>,
  { browser: b }: { browser: import("@playwright/test").Browser },
) {
  const ctx: BrowserContext = await b.newContext({
    storageState: authFile(role),
  })
  const page = await ctx.newPage()
  await use(page)
  await ctx.close()
}

// ---------------------------------------------------------------------------
// Token extraction from storageState JSON
// ---------------------------------------------------------------------------

function tokenFromStorageState(role: Persona): string {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const state = JSON.parse(
    require("node:fs").readFileSync(authFile(role), "utf8"),
  ) as {
    origins: { origin: string; localStorage: { name: string; value: string }[] }[]
  }
  const entry = state.origins[0]?.localStorage.find((e) => e.name === "auth-storage")
  if (!entry) throw new Error(`No auth-storage entry for ${role}`)
  const parsed = JSON.parse(entry.value) as { state: { token: string } }
  return parsed.state.token
}

// ---------------------------------------------------------------------------
// Extended test object
// ---------------------------------------------------------------------------

export const test = base.extend<AuthFixtures>({
  masterPage: async ({ browser }, use) => {
    const ctx = await browser.newContext({ storageState: authFile("master") })
    const page = await ctx.newPage()
    await use(page)
    await ctx.close()
  },

  learner1Page: async ({ browser }, use) => {
    const ctx = await browser.newContext({ storageState: authFile("learner1") })
    const page = await ctx.newPage()
    await use(page)
    await ctx.close()
  },

  learner2Page: async ({ browser }, use) => {
    const ctx = await browser.newContext({ storageState: authFile("learner2") })
    const page = await ctx.newPage()
    await use(page)
    await ctx.close()
  },

  outsiderPage: async ({ browser }, use) => {
    const ctx = await browser.newContext({ storageState: authFile("outsider") })
    const page = await ctx.newPage()
    await use(page)
    await ctx.close()
  },

  masterRequest: async ({}, use) => {
    const token = tokenFromStorageState("master")
    const ctx = await pwRequest.newContext({
      baseURL: BACKEND_URL,
      extraHTTPHeaders: { Authorization: `Bearer ${token}` },
    })
    await use(ctx)
    await ctx.dispose()
  },

  apiAs: async ({}, use) => {
    const contexts: Awaited<ReturnType<typeof pwRequest.newContext>>[] = []
    const factory = async (persona: Persona) => {
      const token = tokenFromStorageState(persona)
      const ctx = await pwRequest.newContext({
        baseURL: BACKEND_URL,
        extraHTTPHeaders: { Authorization: `Bearer ${token}` },
      })
      contexts.push(ctx)
      return ctx
    }
    await use(factory)
    for (const ctx of contexts) await ctx.dispose()
  },
})

export { expect } from "@playwright/test"
