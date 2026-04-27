/**
 * React Query hooks for curator earnings.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import * as earningsApi from "@/api/earnings"

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

export const earningsKeys = {
  summary: () => ["earnings", "summary"] as const,
  history: () => ["earnings", "history"] as const,
}

// ---------------------------------------------------------------------------
// Queries
// ---------------------------------------------------------------------------

/** Earnings summary: total_pending, total_released, full commissions list */
export function useMyEarnings() {
  return useQuery({
    queryKey: earningsKeys.summary(),
    queryFn: () => earningsApi.getMyEarnings(),
  })
}

/** Full commission history (all statuses) */
export function useMyEarningsHistory() {
  return useQuery({
    queryKey: earningsKeys.history(),
    queryFn: () => earningsApi.getMyEarningsHistory(),
  })
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

/** Release a pending commission payout */
export function useReleaseEarning() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (commissionId: string) => earningsApi.releaseEarning(commissionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: earningsKeys.summary() })
      queryClient.invalidateQueries({ queryKey: earningsKeys.history() })
    },
  })
}
