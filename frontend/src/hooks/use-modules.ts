/**
 * TanStack Query hooks for Module & Topic operations.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import * as modulesApi from "@/api/modules"
import type { AddTopicRequest, CreateModuleRequest } from "@/api/types"

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

export const moduleKeys = {
  all: ["modules"] as const,
  list: () => [...moduleKeys.all, "list"] as const,
  detail: (moduleId: string) => [...moduleKeys.all, "detail", moduleId] as const,
}

// ---------------------------------------------------------------------------
// Queries
// ---------------------------------------------------------------------------

export function useModules() {
  return useQuery({
    queryKey: moduleKeys.list(),
    queryFn: modulesApi.listModules,
  })
}

export function useModule(moduleId: string) {
  return useQuery({
    queryKey: moduleKeys.detail(moduleId),
    queryFn: () => modulesApi.getModule(moduleId),
    enabled: !!moduleId,
  })
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

export function useCreateModule() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateModuleRequest) => modulesApi.createModule(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: moduleKeys.list() })
    },
  })
}

export function useAddTopic(moduleId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: AddTopicRequest) => modulesApi.addTopic(moduleId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: moduleKeys.detail(moduleId) })
    },
  })
}

export function useRemoveTopic(moduleId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (topicId: string) => modulesApi.removeTopic(moduleId, topicId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: moduleKeys.detail(moduleId) })
    },
  })
}
