/**
 * API functions for curator earnings endpoints.
 *
 * Endpoints:
 *   GET  /me/earnings               — summary + all commissions
 *   GET  /me/earnings/history       — full commission history
 *   POST /me/earnings/:id/release   — release a pending commission
 */

import { get, post } from "./client"
import type { CommissionResponse, EarningsSummaryResponse } from "./types"

/** GET /me/earnings */
export function getMyEarnings(): Promise<EarningsSummaryResponse> {
  return get<EarningsSummaryResponse>("/me/earnings")
}

/** GET /me/earnings/history */
export function getMyEarningsHistory(): Promise<CommissionResponse[]> {
  return get<CommissionResponse[]>("/me/earnings/history")
}

/** POST /me/earnings/:id/release */
export function releaseEarning(commissionId: string): Promise<CommissionResponse> {
  return post<CommissionResponse>(`/me/earnings/${commissionId}/release`)
}
