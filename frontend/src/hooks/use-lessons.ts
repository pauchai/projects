/**
 * TanStack Query hooks for Lesson operations.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import * as modulesApi from "@/api/modules"
import { moduleKeys } from "./use-modules"

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

export const lessonKeys = {
  all: ["lessons"] as const,
  byModule: (moduleId: string) => [...lessonKeys.all, "module", moduleId] as const,
  detail: (moduleId: string, lessonId: string) =>
    [...lessonKeys.all, "detail", moduleId, lessonId] as const,
  file: (moduleId: string, filePath: string) =>
    [...lessonKeys.all, "file", moduleId, filePath] as const,
}

// ---------------------------------------------------------------------------
// Queries
// ---------------------------------------------------------------------------

export function useLessons(moduleId: string) {
  return useQuery({
    queryKey: lessonKeys.byModule(moduleId),
    queryFn: () => modulesApi.listLessons(moduleId),
    enabled: !!moduleId,
  })
}

export function useLessonFile(moduleId: string, filePath: string | null) {
  return useQuery({
    queryKey: lessonKeys.file(moduleId, filePath ?? ""),
    queryFn: () => modulesApi.getLessonFile(moduleId, filePath!),
    enabled: !!moduleId && !!filePath,
  })
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

export function useSyncModuleVolume(moduleId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => modulesApi.syncModuleVolume(moduleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: lessonKeys.byModule(moduleId) })
    },
  })
}

export function useSyncLessonsFromManifest(moduleId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => modulesApi.syncLessonsFromManifest(moduleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: lessonKeys.byModule(moduleId) })
      queryClient.invalidateQueries({ queryKey: moduleKeys.detail(moduleId) })
    },
  })
}

export function useSetRepoUrl(moduleId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (repoUrl: string | null) => modulesApi.setRepoUrl(moduleId, repoUrl),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: moduleKeys.detail(moduleId) })
    },
  })
}
