/**
 * Credentials API functions: list and link sign-in methods.
 */

import { get, post } from "./client"
import type { CredentialsListResponse, MessageResponse, OAuthCallbackRequest } from "./types"

/** GET /auth/credentials — list all sign-in methods for the current user */
export function getUserCredentials(): Promise<CredentialsListResponse> {
  return get<CredentialsListResponse>("/auth/credentials")
}

/** POST /auth/oauth/google/link — link Google account to the current user */
export function linkGoogleAccount(data: OAuthCallbackRequest): Promise<MessageResponse> {
  return post<MessageResponse>("/auth/oauth/google/link", data)
}

/** POST /auth/oauth/telegram/link — link Telegram account to the current user */
export function linkTelegramAccount(data: OAuthCallbackRequest): Promise<MessageResponse> {
  return post<MessageResponse>("/auth/oauth/telegram/link", data)
}
