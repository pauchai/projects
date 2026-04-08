/**
 * TanStack Query hook for fetching user credentials (sign-in methods).
 */

import { useQuery } from "@tanstack/react-query"
import { useAuthStore } from "@/stores/auth-store"
import { getUserCredentials } from "@/api/credentials"

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
