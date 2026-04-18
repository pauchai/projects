import { defineConfig, devices } from "@playwright/test"
import { config as loadEnv } from "dotenv"
import path from "node:path"
import { fileURLToPath } from "node:url"

// Load .env.e2e if it exists. Variables already set in the shell take priority
// (override: false), so inline env vars still work: E2E_BACKEND_URL=... npm run test:e2e
const __dirname = path.dirname(fileURLToPath(import.meta.url))
loadEnv({ path: path.join(__dirname, ".env.e2e"), override: false })

/**
 * Playwright E2E configuration.
 *
 * Copy frontend/.env.e2e.example → frontend/.env.e2e and edit as needed.
 * Then simply run:
 *   cd frontend && npm run test:e2e
 *
 * You can still override individual variables inline:
 *   E2E_BACKEND_URL=http://other-host/api npm run test:e2e
 *
 * See .env.e2e.example for all available variables and profile examples.
 */

const FRONTEND_URL = process.env.E2E_FRONTEND_URL ?? "http://localhost:5173"
const isLocalVite = FRONTEND_URL === "http://localhost:5173"

export default defineConfig({
  testDir: "./e2e",
  testMatch: "**/*.spec.ts",

  // Global setup: run migrations + register test personas
  globalSetup: "./e2e/global-setup.ts",

  // Fail the build on CI if there are accidental test.only calls
  forbidOnly: !!process.env.CI,

  // Retry once on CI to reduce flakiness from network timing
  retries: process.env.CI ? 1 : 0,

  // Run tests in parallel within each file; sequential between files by default
  workers: process.env.CI ? 1 : 2,

  reporter: [["html", { outputFolder: "playwright-report", open: "never" }], ["list"]],

  use: {
    baseURL: FRONTEND_URL,
    // Capture screenshot + trace on first retry to aid debugging
    screenshot: "only-on-failure",
    trace: "on-first-retry",
    // API calls go directly to the backend (same as Vite proxy target)
    extraHTTPHeaders: { "Content-Type": "application/json" },
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  // Vite dev server — only started when targeting the local Vite instance.
  // When E2E_FRONTEND_URL points to a Docker/Traefik host the frontend is
  // already running and webServer is omitted entirely.
  ...(isLocalVite && {
    webServer: {
      command: "npm run dev",
      port: 5173,
      reuseExistingServer: true,
      timeout: 30_000,
    },
  }),
})
