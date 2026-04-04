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
