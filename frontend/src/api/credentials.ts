/**
 * Credentials API functions: list connected sign-in methods.
 */

import { get } from "./client"
import type { CredentialsListResponse } from "./types"

/** GET /auth/credentials — list all sign-in methods for the current user */
export function getUserCredentials(): Promise<CredentialsListResponse> {
  return get<CredentialsListResponse>("/auth/credentials")
}
