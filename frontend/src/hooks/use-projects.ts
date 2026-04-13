/**
 * TanStack Query hooks for project operations.
 *
 * Provides useQuery hooks for fetching projects and useMutation hooks
 * for all project actions (create, status transitions, applications, members).
 */

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"
import * as projectsApi from "@/api/projects"
import type {
  ApplyToProjectRequest,
  ChangeMemberRoleRequest,
  CreateProjectRequest,
  SearchProjectsParams,
  UpdateProjectRequest,
} from "@/api/types"

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

export const projectKeys = {
  all: ["projects"] as const,
  search: (params?: SearchProjectsParams) =>
    [...projectKeys.all, "search", params ?? {}] as const,
  detail: (projectId: string) =>
    [...projectKeys.all, "detail", projectId] as const,
}

// ---------------------------------------------------------------------------
// Queries
// ---------------------------------------------------------------------------

/** Search/list projects */
export function useSearchProjects(params?: SearchProjectsParams) {
  return useQuery({
    queryKey: projectKeys.search(params),
    queryFn: () => projectsApi.searchProjects(params),
  })
}

/** Get a single project by ID */
export function useProject(projectId: string) {
  return useQuery({
    queryKey: projectKeys.detail(projectId),
    queryFn: () => projectsApi.getProject(projectId),
    enabled: !!projectId,
  })
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

/** Create a new project */
export function useCreateProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateProjectRequest) =>
      projectsApi.createProject(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.all })
    },
  })
}

/** Update an existing project */
export function useUpdateProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      projectId,
      data,
    }: {
      projectId: string
      data: UpdateProjectRequest
    }) => projectsApi.updateProject(projectId, data),
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({
        queryKey: projectKeys.detail(projectId),
      })
      queryClient.invalidateQueries({
        queryKey: projectKeys.all,
      })
    },
  })
}

/** Helper: creates a mutation that invalidates a project detail + search list */
function useProjectAction(
  actionFn: (projectId: string) => Promise<unknown>,
) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: actionFn,
    onSuccess: (_data, projectId) => {
      queryClient.invalidateQueries({
        queryKey: projectKeys.detail(projectId),
      })
      queryClient.invalidateQueries({
        queryKey: projectKeys.all,
      })
    },
  })
}

/** Publish a project */
export function usePublishProject() {
  return useProjectAction(projectsApi.publishProject)
}

/** Activate a project */
export function useActivateProject() {
  return useProjectAction(projectsApi.activateProject)
}

/** Suspend a project */
export function useSuspendProject() {
  return useProjectAction(projectsApi.suspendProject)
}

/** Resume a project */
export function useResumeProject() {
  return useProjectAction(projectsApi.resumeProject)
}

/** Complete a project */
export function useCompleteProject() {
  return useProjectAction(projectsApi.completeProject)
}

/** Cancel a project */
export function useCancelProject() {
  return useProjectAction(projectsApi.cancelProject)
}

/** Apply to join a project */
export function useApplyToProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      projectId,
      data,
    }: {
      projectId: string
      data: ApplyToProjectRequest
    }) => projectsApi.applyToProject(projectId, data),
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({
        queryKey: projectKeys.detail(projectId),
      })
    },
  })
}

/** Accept an application */
export function useAcceptApplication() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      projectId,
      applicationId,
    }: {
      projectId: string
      applicationId: string
    }) => projectsApi.acceptApplication(projectId, applicationId),
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({
        queryKey: projectKeys.detail(projectId),
      })
    },
  })
}

/** Reject an application */
export function useRejectApplication() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      projectId,
      applicationId,
    }: {
      projectId: string
      applicationId: string
    }) => projectsApi.rejectApplication(projectId, applicationId),
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({
        queryKey: projectKeys.detail(projectId),
      })
    },
  })
}

/** Change a member's role */
export function useChangeMemberRole() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      projectId,
      membershipId,
      data,
    }: {
      projectId: string
      membershipId: string
      data: ChangeMemberRoleRequest
    }) => projectsApi.changeMemberRole(projectId, membershipId, data),
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({
        queryKey: projectKeys.detail(projectId),
      })
    },
  })
}

/** Remove a member from a project */
export function useRemoveMember() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      projectId,
      membershipId,
    }: {
      projectId: string
      membershipId: string
    }) => projectsApi.removeMember(projectId, membershipId),
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({
        queryKey: projectKeys.detail(projectId),
      })
    },
  })
}
