/**
 * Fund API functions for a project's fund.
 */

import { get, post } from "./client"
import type { DepositRequest, DistributeRequest, FundDistributionResponse, FundResponse } from "./types"

/** GET /projects/:id/fund — get fund balance and history */
export function getFund(projectId: string): Promise<FundResponse> {
  return get<FundResponse>(`/projects/${projectId}/fund`)
}

/** POST /projects/:id/fund/deposit — deposit into fund */
export function deposit(projectId: string, data: DepositRequest): Promise<FundResponse> {
  return post<FundResponse>(`/projects/${projectId}/fund/deposit`, data)
}

/** POST /projects/:id/fund/distribute — create distribution request */
export function distribute(
  projectId: string,
  data: DistributeRequest,
): Promise<FundDistributionResponse> {
  return post<FundDistributionResponse>(`/projects/${projectId}/fund/distribute`, data)
}
