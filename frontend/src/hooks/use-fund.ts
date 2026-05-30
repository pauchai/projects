/**
 * TanStack Query hooks for project fund operations.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import * as fundApi from "@/api/fund"
import type { DepositRequest, DistributeRequest } from "@/api/types"

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

export const fundKeys = {
  detail: (projectId: string) => ["projects", projectId, "fund"] as const,
}

// ---------------------------------------------------------------------------
// Queries
// ---------------------------------------------------------------------------

/** Get fund balance and history for a project */
export function useFund(projectId: string) {
  return useQuery({
    queryKey: fundKeys.detail(projectId),
    queryFn: () => fundApi.getFund(projectId),
    enabled: !!projectId,
  })
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

/** Deposit into project fund */
export function useDeposit(projectId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: DepositRequest) => fundApi.deposit(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: fundKeys.detail(projectId) })
    },
  })
}

/** Create a distribution request from project fund */
export function useDistribute(projectId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: DistributeRequest) => fundApi.distribute(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: fundKeys.detail(projectId) })
    },
  })
}
