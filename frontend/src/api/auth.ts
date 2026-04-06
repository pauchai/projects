/**
 * Auth API functions: register, login, get current user.
 */

import { get, post } from "./client"
import type {
  LoginRequest,
  OAuthAvailableResponse,
  OAuthAuthorizeResponse,
  OAuthCallbackRequest,
  RegisterRequest,
  TokenResponse,
  UserResponse,
} from "./types"

/** POST /auth/register */
export function register(data: RegisterRequest): Promise<UserResponse> {
  return post<UserResponse>("/auth/register", data)
}

/** POST /auth/login */
export function login(data: LoginRequest): Promise<TokenResponse> {
  return post<TokenResponse>("/auth/login", data)
}

/** GET /auth/me — requires valid JWT */
export function getMe(): Promise<UserResponse> {
  return get<UserResponse>("/auth/me")
}

// ---------------------------------------------------------------------------
// OAuth
// ---------------------------------------------------------------------------

/** GET /auth/oauth/google/available — check if Google OAuth is configured */
export function getGoogleOAuthAvailable(): Promise<OAuthAvailableResponse> {
  return get<OAuthAvailableResponse>("/auth/oauth/google/available")
}

/** GET /auth/oauth/google/authorize — get authorization URL and state */
export function getGoogleOAuthAuthorize(): Promise<OAuthAuthorizeResponse> {
  return get<OAuthAuthorizeResponse>("/auth/oauth/google/authorize")
}

/** POST /auth/oauth/google/callback — exchange authorization code for JWT */
export function googleOAuthCallback(data: OAuthCallbackRequest): Promise<TokenResponse> {
  return post<TokenResponse>("/auth/oauth/google/callback", data)
}
