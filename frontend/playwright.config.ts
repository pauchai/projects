import { defineConfig, devices } from "@playwright/test"

/**
 * Playwright E2E configuration.
 *
 * Prerequisites before running:
 *   1. docker compose --profile test up -d postgres-test
 *   2. DATABASE_URL="postgresql://collab_test:collab_test@localhost:5433/project_collaboration_test" \
 *      JWT_SECRET="dev-secret-change-me-in-production" \
 *      PYTHONPATH=src uvicorn project_collaboration.api.app:app --port 8000
 *
 * Then:
 *   cd frontend && npx playwright test
 */
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
    baseURL: "http://localhost:5173",
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

  // Vite dev server — Playwright starts it automatically if not already running
  webServer: {
    command: "npm run dev",
    port: 5173,
    reuseExistingServer: true,
    timeout: 30_000,
  },
})
