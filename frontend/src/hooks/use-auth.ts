/**
 * TanStack Query hooks for auth operations.
 *
 * Provides useMutation hooks for register/login and a useQuery hook for
 * fetching the current user profile.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useAuthStore } from "@/stores/auth-store"
import * as authApi from "@/api/auth"
import type { LoginRequest, RegisterRequest } from "@/api/types"

/** Query key for current user profile */
export const ME_QUERY_KEY = ["auth", "me"] as const

/** Query key for Google OAuth availability */
export const GOOGLE_OAUTH_AVAILABLE_KEY = ["auth", "oauth", "google", "available"] as const

/** Query key for Telegram OAuth availability */
export const TELEGRAM_OAUTH_AVAILABLE_KEY = ["auth", "oauth", "telegram", "available"] as const

/**
 * Fetch current user profile (GET /auth/me).
 * Only enabled when the user is authenticated.
 */
export function useMe() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  return useQuery({
    queryKey: ME_QUERY_KEY,
    queryFn: authApi.getMe,
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

/**
 * Register a new user.
 * On success, automatically logs in by calling the login mutation.
 */
export function useRegister() {
  const setAuth = useAuthStore((s) => s.setAuth)

  return useMutation({
    mutationFn: async (data: RegisterRequest) => {
      const user = await authApi.register(data)
      // Auto-login after registration
      const tokenResp = await authApi.login({
        email: data.email,
        password: data.password,
      })
      return { user, token: tokenResp.access_token }
    },
    onSuccess: ({ user, token }) => {
      setAuth(token, user.user_id, user.email, user.display_name)
    },
  })
}

/**
 * Login with email and password.
 * On success, stores the token and fetches user profile to populate the store.
 */
export function useLogin() {
  const setAuth = useAuthStore((s) => s.setAuth)
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: LoginRequest) => {
      const tokenResp = await authApi.login(data)
      // Temporarily store token so getMe() can use it
      useAuthStore.getState().setAuth(tokenResp.access_token, "", "", "")
      const user = await authApi.getMe()
      return { user, token: tokenResp.access_token }
    },
    onSuccess: ({ user, token }) => {
      setAuth(token, user.user_id, user.email, user.display_name)
      queryClient.setQueryData(ME_QUERY_KEY, user)
    },
    onError: () => {
      // If login fails after partial state update, clear auth
      useAuthStore.getState().logout()
    },
  })
}

/**
 * Logout: clear auth store and invalidate queries.
 */
export function useLogout() {
  const logout = useAuthStore((s) => s.logout)
  const queryClient = useQueryClient()

  return () => {
    logout()
    queryClient.removeQueries({ queryKey: ME_QUERY_KEY })
    queryClient.clear()
  }
}

// ---------------------------------------------------------------------------
// Google OAuth
// ---------------------------------------------------------------------------

/**
 * Check whether Google OAuth is available (backend has credentials configured).
 * Cached for 10 minutes; fires once on mount.
 */
export function useGoogleOAuthAvailable() {
  return useQuery({
    queryKey: GOOGLE_OAUTH_AVAILABLE_KEY,
    queryFn: authApi.getGoogleOAuthAvailable,
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}

/**
 * Popup-based Google OAuth login.
 *
 * Flow:
 * 1. Call GET /authorize → get authorization_url + state
 * 2. Open authorization_url in a popup window
 * 3. Wait for popup to redirect to our callback page with ?code=...&state=...
 * 4. POST code + state to /callback → receive JWT
 * 5. Fetch user profile (GET /auth/me) and store auth
 */
export function useGoogleLogin() {
  const setAuth = useAuthStore((s) => s.setAuth)
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      // Step 1: Get authorization URL from backend
      const { authorization_url, state } = await authApi.getGoogleOAuthAuthorize()

      // Step 2: Open popup and wait for the authorization code
      const code = await openOAuthPopup(authorization_url)

      // Step 3: Exchange code for JWT
      const tokenResp = await authApi.googleOAuthCallback({ code, state })

      // Step 4: Temporarily store token so getMe() can use it
      useAuthStore.getState().setAuth(tokenResp.access_token, "", "", "")
      const user = await authApi.getMe()

      return { user, token: tokenResp.access_token }
    },
    onSuccess: ({ user, token }) => {
      setAuth(token, user.user_id, user.email, user.display_name)
      queryClient.setQueryData(ME_QUERY_KEY, user)
    },
    onError: () => {
      // If login fails after partial state update, clear auth
      useAuthStore.getState().logout()
    },
  })
}

// ---------------------------------------------------------------------------
// Telegram OAuth
// ---------------------------------------------------------------------------

/**
 * Check whether Telegram OAuth is available (backend has bot configured).
 * Cached for 10 minutes; fires once on mount.
 */
export function useTelegramOAuthAvailable() {
  return useQuery({
    queryKey: TELEGRAM_OAUTH_AVAILABLE_KEY,
    queryFn: authApi.getTelegramOAuthAvailable,
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}

/**
 * Redirect-based Telegram OAuth login.
 *
 * Flow:
 * 1. Call GET /authorize → get telegram_url + state
 * 2. Store state in sessionStorage for later validation
 * 3. Redirect user to Telegram deep link (opens Telegram app/web)
 * 4. User interacts with bot → bot sends auth link back
 * 5. User clicks auth link → /oauth/callback page handles code exchange
 */
export function useTelegramLogin() {
  return useMutation({
    mutationFn: async () => {
      // Step 1: Get Telegram deep link from backend
      const { telegram_url, state } = await authApi.getTelegramOAuthAuthorize()

      // Step 2: Store state for validation when the user returns
      sessionStorage.setItem("telegram_oauth_state", state)

      // Step 3: Redirect to Telegram (opens Telegram app)
      window.location.href = telegram_url
    },
  })
}

/**
 * Exchange a Telegram authorization code + state for a JWT.
 *
 * Called by the OAuth callback page when it detects Telegram state
 * in sessionStorage. This completes the auth flow after the user
 * clicks the link sent by the bot.
 */
export function useTelegramCallback() {
  const setAuth = useAuthStore((s) => s.setAuth)
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ code, state }: { code: string; state: string }) => {
      // Exchange code + state for JWT
      const tokenResp = await authApi.telegramOAuthCallback({ code, state })

      // Temporarily store token so getMe() can use it
      useAuthStore.getState().setAuth(tokenResp.access_token, "", "", "")
      const user = await authApi.getMe()

      return { user, token: tokenResp.access_token }
    },
    onSuccess: ({ user, token }) => {
      setAuth(token, user.user_id, user.email, user.display_name)
      queryClient.setQueryData(ME_QUERY_KEY, user)
      // Clean up sessionStorage
      sessionStorage.removeItem("telegram_oauth_state")
    },
    onError: () => {
      useAuthStore.getState().logout()
      sessionStorage.removeItem("telegram_oauth_state")
    },
  })
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Open a popup window for OAuth authorization and return the authorization code.
 *
 * The popup navigates to the OAuth provider. After consent, the provider
 * redirects back to our origin at /oauth/callback?code=...&state=...
 * We detect this by polling the popup location.
 *
 * @returns The authorization code extracted from the popup's final URL.
 * @throws Error if the popup is blocked or closed without completing OAuth.
 */
export function openOAuthPopup(authorizationUrl: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const width = 500
    const height = 600
    const left = window.screenX + (window.outerWidth - width) / 2
    const top = window.screenY + (window.outerHeight - height) / 2

    const popup = window.open(
      authorizationUrl,
      "google-oauth",
      `width=${width},height=${height},left=${left},top=${top},popup=yes`,
    )

    if (!popup) {
      reject(new Error("Popup was blocked. Please allow popups for this site."))
      return
    }

    const pollInterval = setInterval(() => {
      try {
        if (popup.closed) {
          clearInterval(pollInterval)
          reject(new Error("OAuth popup was closed before completing sign-in."))
          return
        }

        // Check if the popup navigated back to our origin
        if (popup.location.origin === window.location.origin) {
          const params = new URLSearchParams(popup.location.search)
          const code = params.get("code")
          const error = params.get("error")

          clearInterval(pollInterval)
          popup.close()

          if (error) {
            reject(new Error(`OAuth error: ${error}`))
          } else if (code) {
            resolve(code)
          } else {
            reject(new Error("No authorization code received from OAuth provider."))
          }
        }
      } catch {
        // Cross-origin access — popup is still on the OAuth provider's domain.
        // This is expected; keep polling.
      }
    }, 200)
  })
}
