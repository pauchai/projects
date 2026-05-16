/**
 * TanStack Query hook for the global marketplace (GET /marketplace).
 */

import { useQuery } from "@tanstack/react-query"
import { getMarketplaceProducts } from "@/api/marketplace"

export const marketplaceKey = ["marketplace"] as const

/** GET /marketplace — all active public products across the platform */
export function useMarketplaceProducts() {
  return useQuery({
    queryKey: marketplaceKey,
    queryFn: getMarketplaceProducts,
  })
}
