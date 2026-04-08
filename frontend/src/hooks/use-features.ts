/**
 * TanStack Query hooks for feature request operations.
 *
 * Provides useQuery hooks for fetching feature requests and useMutation
 * hooks for submitting and managing them.
 */

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"
import * as featuresApi from "@/api/features"
import type {
  CreateFeatureRequestRequest,
  ListFeaturesParams,
  UpdateFeatureStatusRequest,
} from "@/api/types"

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

export const featureKeys = {
  all: ["features"] as const,
  list: (params?: ListFeaturesParams) =>
    [...featureKeys.all, "list", params ?? {}] as const,
  detail: (requestId: string) =>
    [...featureKeys.all, "detail", requestId] as const,
}

// ---------------------------------------------------------------------------
// Queries
// ---------------------------------------------------------------------------

/** List feature requests with optional filters */
export function useFeatures(params?: ListFeaturesParams) {
  return useQuery({
    queryKey: featureKeys.list(params),
    queryFn: () => featuresApi.listFeatures(params),
  })
}

/** Get a single feature request by ID */
export function useFeature(requestId: string) {
  return useQuery({
    queryKey: featureKeys.detail(requestId),
    queryFn: () => featuresApi.getFeature(requestId),
    enabled: !!requestId,
  })
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

/** Submit a new feature request */
export function useSubmitFeature() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateFeatureRequestRequest) =>
      featuresApi.submitFeature(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: featureKeys.all })
    },
  })
}

/** Update feature request status (admin action) */
export function useUpdateFeatureStatus() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      requestId,
      data,
    }: {
      requestId: string
      data: UpdateFeatureStatusRequest
    }) => featuresApi.updateFeatureStatus(requestId, data),
    onSuccess: (_data, { requestId }) => {
      queryClient.invalidateQueries({
        queryKey: featureKeys.detail(requestId),
      })
      queryClient.invalidateQueries({
        queryKey: featureKeys.all,
      })
    },
  })
}
