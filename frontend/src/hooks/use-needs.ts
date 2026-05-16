/**
 * TanStack Query hook for the global open-needs list (GET /needs).
 */

import { useQuery } from "@tanstack/react-query"
import { getOpenNeeds } from "@/api/needs"

export const openNeedsKey = ["needs", "open"] as const

/** GET /needs — all open needs across the platform */
export function useOpenNeeds() {
  return useQuery({
    queryKey: openNeedsKey,
    queryFn: getOpenNeeds,
  })
}
