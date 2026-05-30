/** Auth API — minimal: only login. */

import { post } from "./client"
import type { LoginRequest, TokenResponse } from "./types"

/** POST /auth/login */
export function login(data: LoginRequest): Promise<TokenResponse> {
  return post<TokenResponse>("/auth/login", data)
}
