/**
 * TanStack Query hooks for Project Needs.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import * as projectsApi from "@/api/projects"
import type { CreateProjectNeedRequest } from "@/api/types"

export const projectNeedsKey = (projectId: string) =>
  ["projects", projectId, "needs"] as const

/** GET /projects/:id/needs */
export function useProjectNeeds(projectId: string) {
  return useQuery({
    queryKey: projectNeedsKey(projectId),
    queryFn: () => projectsApi.getProjectNeeds(projectId),
    enabled: Boolean(projectId),
  })
}

/** POST /projects/:id/needs */
export function useCreateProjectNeed(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateProjectNeedRequest) =>
      projectsApi.createProjectNeed(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectNeedsKey(projectId) })
    },
  })
}

/** PATCH /projects/:id/needs/:needId/close */
export function useCloseProjectNeed(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (needId: string) => projectsApi.closeProjectNeed(projectId, needId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectNeedsKey(projectId) })
    },
  })
}
