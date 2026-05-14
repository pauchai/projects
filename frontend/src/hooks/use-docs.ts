/**
 * TanStack Query hooks for Project Docs operations.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import * as projectsApi from "@/api/projects"
import { projectKeys } from "./use-projects"

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

export const docsKeys = {
  all: ["docs"] as const,
  file: (projectId: string, filePath: string) =>
    [...docsKeys.all, "file", projectId, filePath] as const,
}

// ---------------------------------------------------------------------------
// Queries
// ---------------------------------------------------------------------------

export function useDocsFile(projectId: string, filePath: string | null) {
  return useQuery({
    queryKey: docsKeys.file(projectId, filePath ?? ""),
    queryFn: () => projectsApi.getDocsFile(projectId, filePath!),
    enabled: !!projectId && !!filePath,
  })
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

export function useSyncDocsVolume(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => projectsApi.syncDocsVolume(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: docsKeys.all })
    },
  })
}

export function useSetDocsRepoUrl(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (docsRepoUrl: string | null) =>
      projectsApi.setDocsRepoUrl(projectId, docsRepoUrl),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.detail(projectId) })
    },
  })
}
