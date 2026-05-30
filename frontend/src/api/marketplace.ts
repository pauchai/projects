/**
 * Marketplace API: GET /marketplace — all active public products across the platform.
 */

import { get } from "./client"
import type { MarketplaceProductResponse } from "./types"

/** GET /marketplace — list all active public products (no auth required) */
export function getMarketplaceProducts(): Promise<MarketplaceProductResponse[]> {
  return get<MarketplaceProductResponse[]>("/marketplace")
}
