/**
 * TanStack Query hooks for user credentials: fetch, link Google, link Telegram.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useAuthStore } from "@/stores/auth-store"
import { getUserCredentials, linkGoogleAccount, linkTelegramAccount } from "@/api/credentials"
import * as authApi from "@/api/auth"
import { openOAuthPopup } from "@/hooks/use-auth"

/** Query key for user credentials */
export const CREDENTIALS_QUERY_KEY = ["auth", "credentials"] as const

/**
 * Fetch the current user's connected sign-in methods.
 * Only enabled when the user is authenticated.
 */
export function useUserCredentials() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  return useQuery({
    queryKey: CREDENTIALS_QUERY_KEY,
    queryFn: getUserCredentials,
    enabled: isAuthenticated,
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

/**
 * Link a Google account to the current user via popup OAuth flow.
 *
 * Flow:
 * 1. GET /auth/oauth/google/authorize → authorization_url + state
 * 2. Open popup window → user consents → code returned
 * 3. POST /auth/oauth/google/link with { code, state }
 * 4. Invalidate credentials query to refresh the UI
 */
export function useLinkGoogleAccount() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      // Step 1: Get authorization URL from backend
      const { authorization_url, state } = await authApi.getGoogleOAuthAuthorize()

      // Step 2: Open popup and wait for the authorization code
      const code = await openOAuthPopup(authorization_url)

      // Step 3: Send link request
      return linkGoogleAccount({ code, state })
    },
    onSuccess: () => {
      // Refresh credentials list to show the newly linked provider
      queryClient.invalidateQueries({ queryKey: CREDENTIALS_QUERY_KEY })
    },
  })
}

/**
 * Link a Telegram account to the current user.
 *
 * Flow:
 * 1. GET /auth/oauth/telegram/authorize → telegram_url + state
 * 2. Store state in localStorage, redirect user to Telegram
 * 3. User interacts with bot → bot sends auth link back
 * 4. User returns to callback page → code + state extracted
 * 5. POST /auth/oauth/telegram/link with { code, state }
 * 6. Invalidate credentials query to refresh the UI
 *
 * Note: Steps 1-3 happen in the initiator; steps 4-5 happen
 * on the callback page using `useLinkTelegramCallback`.
 */
export function useLinkTelegramInitiate() {
  return useMutation({
    mutationFn: async () => {
      // Get Telegram deep link from backend
      const { telegram_url, state } = await authApi.getTelegramOAuthAuthorize()

      // Store state and mark this as a linking flow (not login).
      // Use localStorage (not sessionStorage) because the Telegram link
      // opens in a new tab / Telegram's embedded browser.
      localStorage.setItem("telegram_oauth_state", state)
      localStorage.setItem("telegram_oauth_flow", "link")

      // Redirect to Telegram
      window.location.href = telegram_url
    },
  })
}

/**
 * Complete Telegram account linking after the user returns from Telegram.
 *
 * Called by the OAuth callback page when it detects a Telegram linking flow.
 */
export function useLinkTelegramCallback() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ code, state }: { code: string; state: string }) => {
      return linkTelegramAccount({ code, state })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CREDENTIALS_QUERY_KEY })
      localStorage.removeItem("telegram_oauth_state")
      localStorage.removeItem("telegram_oauth_flow")
    },
    onError: () => {
      localStorage.removeItem("telegram_oauth_state")
      localStorage.removeItem("telegram_oauth_flow")
    },
  })
}
