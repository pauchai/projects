/**
 * Playwright global setup.
 *
 * Runs once before all tests. Responsibilities:
 *   1. Apply Alembic migrations to the test database (clean slate).
 *   2. Register four test personas via the API (idempotent — ignores 409).
 *   3. Login each persona and save its Zustand auth state to e2e/.auth/<role>.json
 *      so individual tests can open a pre-authenticated page without going
 *      through the login UI.
 *
 * The storageState JSON format matches what Zustand `persist` writes under
 * the key "auth-storage" in localStorage.
 */

import { execSync } from "node:child_process"
import fs from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"
import { request } from "@playwright/test"

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const BACKEND_URL = (process.env.E2E_BACKEND_URL ?? "http://localhost:8000").replace(/\/?$/, "/")
const FRONTEND_URL = process.env.E2E_FRONTEND_URL ?? "http://localhost:5173"
const DATABASE_URL =
  process.env.E2E_DATABASE_URL ??
  "postgresql://collab_test:collab_test@localhost:5433/project_collaboration_test"
const AUTH_DIR = path.join(__dirname, ".auth")

/** Test personas used across all E2E scenarios. */
export const PERSONAS = {
  master: {
    email: "master@e2e.test",
    password: "e2epassword",
    display_name: "E2E Master",
  },
  learner1: {
    email: "learner1@e2e.test",
    password: "e2epassword",
    display_name: "E2E Learner One",
  },
  learner2: {
    email: "learner2@e2e.test",
    password: "e2epassword",
    display_name: "E2E Learner Two",
  },
  outsider: {
    email: "outsider@e2e.test",
    password: "e2epassword",
    display_name: "E2E Outsider",
  },
} as const

export type PersonaKey = keyof typeof PERSONAS

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Build the storageState JSON that Playwright injects into localStorage.
 * Mirrors the shape Zustand `persist` middleware writes under "auth-storage".
 */
function buildStorageState(
  token: string,
  userId: string,
  email: string,
  displayName: string,
) {
  const authValue = JSON.stringify({
    state: { token, userId, email, displayName, isAuthenticated: true },
    version: 0,
  })

  return {
    cookies: [],
    origins: [
      {
        origin: FRONTEND_URL,
        localStorage: [{ name: "auth-storage", value: authValue }],
      },
    ],
  }
}

// ---------------------------------------------------------------------------
// Global setup entry point
// ---------------------------------------------------------------------------

export default async function globalSetup() {
  // 1. Run Alembic migrations against the test DB for a clean slate.
  //    The backend must be pointed at postgres-test (port 5433) and this
  //    command runs in the project root where alembic.ini lives.
  const projectRoot = path.resolve(__dirname, "../../")
  console.log("\n[e2e] Running test DB migrations…")
  execSync(
    "python -m alembic downgrade base && python -m alembic upgrade head",
    {
      cwd: projectRoot,
      env: {
        ...process.env,
        DATABASE_URL,
        PYTHONPATH: "src",
      },
      stdio: "pipe",
    },
  )
  console.log("[e2e] Migrations done.")

  // 2. Ensure the .auth directory exists.
  fs.mkdirSync(AUTH_DIR, { recursive: true })

  // 3. For each persona: register (ignore 409) → login → save storageState.
  const apiContext = await request.newContext({ baseURL: BACKEND_URL })

  for (const [role, persona] of Object.entries(PERSONAS) as [PersonaKey, typeof PERSONAS[PersonaKey]][]) {
    // Register — a 409 means the user already exists (unexpected after full
    // downgrade, but guard just in case migrations were not fully reset).
    const registerResp = await apiContext.post("auth/register", {
      data: {
        email: persona.email,
        password: persona.password,
        display_name: persona.display_name,
      },
    })
    if (!registerResp.ok() && registerResp.status() !== 409 && registerResp.status() !== 422) {
      throw new Error(
        `[e2e] Failed to register ${role}: ${registerResp.status()} ${await registerResp.text()}`,
      )
    }

    // Login
    const loginResp = await apiContext.post("auth/login", {
      data: { email: persona.email, password: persona.password },
    })
    if (!loginResp.ok()) {
      throw new Error(
        `[e2e] Failed to login ${role}: ${loginResp.status()} ${await loginResp.text()}`,
      )
    }
    const { access_token: token } = await loginResp.json() as { access_token: string; token_type: string }

    // GET /auth/me to obtain userId
    const meResp = await apiContext.get("auth/me", {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!meResp.ok()) {
      throw new Error(`[e2e] Failed to fetch /me for ${role}: ${meResp.status()}`)
    }
    const { user_id: userId } = await meResp.json() as { user_id: string; email: string; display_name: string }

    // Save storageState
    const storageState = buildStorageState(token, userId, persona.email, persona.display_name)
    fs.writeFileSync(
      path.join(AUTH_DIR, `${role}.json`),
      JSON.stringify(storageState, null, 2),
    )
    console.log(`[e2e] Persona '${role}' ready (userId=${userId})`)
  }

  await apiContext.dispose()
  console.log("[e2e] Global setup complete.\n")
}
