/**
 * Auth API functions: register, login, get current user.
 */

import { get, patch, post } from "./client"
import type {
  LoginRequest,
  MessageResponse,
  OAuthAvailableResponse,
  OAuthAuthorizeResponse,
  OAuthCallbackRequest,
  ReferralsListResponse,
  RegisterRequest,
  SetPasswordRequest,
  TelegramAuthorizeResponse,
  TokenResponse,
  UpdateProfileRequest,
  UserInviteCodeResponse,
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

/** POST /auth/local/set-password — set password for authenticated user */
export function setPassword(data: SetPasswordRequest): Promise<MessageResponse> {
  return post<MessageResponse>("/auth/local/set-password", data)
}

/** GET /auth/me — requires valid JWT.
 *  @param token - Explicit JWT to use instead of reading from the auth store.
 */
export function getMe(token?: string): Promise<UserResponse> {
  return get<UserResponse>("/auth/me", undefined, token)
}

/** PATCH /auth/me — update email and/or display_name for the authenticated user. */
export function updateProfile(data: UpdateProfileRequest): Promise<UserResponse> {
  return patch<UserResponse>("/auth/me", data)
}

/** GET /auth/referrals — list users invited by the current user. */
export function getReferrals(): Promise<ReferralsListResponse> {
  return get<ReferralsListResponse>("/auth/referrals")
}

/** POST /auth/invite-codes — generate a new invite code for the current user. */
export function createInviteCode(): Promise<UserInviteCodeResponse> {
  return post<UserInviteCodeResponse>("/auth/invite-codes", {})
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

// ---------------------------------------------------------------------------
// Telegram OAuth
// ---------------------------------------------------------------------------

/** GET /auth/oauth/telegram/available — check if Telegram OAuth is configured */
export function getTelegramOAuthAvailable(): Promise<OAuthAvailableResponse> {
  return get<OAuthAvailableResponse>("/auth/oauth/telegram/available")
}

/** GET /auth/oauth/telegram/authorize — get Telegram deep link URL and state */
export function getTelegramOAuthAuthorize(): Promise<TelegramAuthorizeResponse> {
  return get<TelegramAuthorizeResponse>("/auth/oauth/telegram/authorize")
}

/** POST /auth/oauth/telegram/callback — exchange authorization code for JWT */
export function telegramOAuthCallback(data: OAuthCallbackRequest): Promise<TokenResponse> {
  return post<TokenResponse>("/auth/oauth/telegram/callback", data)
}
