/**
 * Feature Requests API functions: list, get, submit, update status.
 */

import { get, post, put } from "./client"
import type {
  CreateFeatureRequestRequest,
  FeatureRequestResponse,
  ListFeaturesParams,
  MessageResponse,
  UpdateFeatureStatusRequest,
} from "./types"

/** GET /features — list all feature requests with optional filters */
export function listFeatures(
  params?: ListFeaturesParams,
): Promise<FeatureRequestResponse[]> {
  const queryParams: Record<string, string> = {}
  if (params?.status) queryParams.status = params.status
  if (params?.author_id) queryParams.author_id = params.author_id
  return get<FeatureRequestResponse[]>("/features", queryParams)
}

/** GET /features/:id — get a single feature request */
export function getFeature(
  requestId: string,
): Promise<FeatureRequestResponse> {
  return get<FeatureRequestResponse>(`/features/${requestId}`)
}

/** POST /features — submit a new feature request */
export function submitFeature(
  data: CreateFeatureRequestRequest,
): Promise<FeatureRequestResponse> {
  return post<FeatureRequestResponse>("/features", data)
}

/** PUT /admin/features/:id/status — update status and admin notes */
export function updateFeatureStatus(
  requestId: string,
  data: UpdateFeatureStatusRequest,
): Promise<MessageResponse> {
  return put<MessageResponse>(
    `/admin/features/${requestId}/status`,
    data,
  )
}
