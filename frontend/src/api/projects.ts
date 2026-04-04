/**
 * Projects API functions: CRUD, search, status transitions, applications, members.
 */

import { del, get, patch, post } from "./client"
import type {
  ApplyToProjectRequest,
  ChangeMemberRoleRequest,
  CreateProjectRequest,
  MessageResponse,
  ProjectResponse,
  ProjectSummaryResponse,
  SearchProjectsParams,
} from "./types"

/** POST /projects — create a new project */
export function createProject(
  data: CreateProjectRequest,
): Promise<ProjectResponse> {
  return post<ProjectResponse>("/projects", data)
}

/** GET /projects/search — search/filter projects */
export function searchProjects(
  params?: SearchProjectsParams,
): Promise<ProjectSummaryResponse[]> {
  const queryParams: Record<string, string> = {}
  if (params?.keyword) queryParams.keyword = params.keyword
  if (params?.status) queryParams.status = params.status
  if (params?.skills) queryParams.skills = params.skills
  return get<ProjectSummaryResponse[]>("/projects/search", queryParams)
}

/** GET /projects/:id — get project detail */
export function getProject(projectId: string): Promise<ProjectResponse> {
  return get<ProjectResponse>(`/projects/${projectId}`)
}

/** POST /projects/:id/publish */
export function publishProject(projectId: string): Promise<MessageResponse> {
  return post<MessageResponse>(`/projects/${projectId}/publish`)
}

/** POST /projects/:id/activate */
export function activateProject(projectId: string): Promise<MessageResponse> {
  return post<MessageResponse>(`/projects/${projectId}/activate`)
}

/** POST /projects/:id/suspend */
export function suspendProject(projectId: string): Promise<MessageResponse> {
  return post<MessageResponse>(`/projects/${projectId}/suspend`)
}

/** POST /projects/:id/resume */
export function resumeProject(projectId: string): Promise<MessageResponse> {
  return post<MessageResponse>(`/projects/${projectId}/resume`)
}

/** POST /projects/:id/complete */
export function completeProject(projectId: string): Promise<MessageResponse> {
  return post<MessageResponse>(`/projects/${projectId}/complete`)
}

/** POST /projects/:id/cancel */
export function cancelProject(projectId: string): Promise<MessageResponse> {
  return post<MessageResponse>(`/projects/${projectId}/cancel`)
}

/** POST /projects/:id/applications — apply to join */
export function applyToProject(
  projectId: string,
  data: ApplyToProjectRequest,
): Promise<MessageResponse> {
  return post<MessageResponse>(
    `/projects/${projectId}/applications`,
    data,
  )
}

/** POST /projects/:id/applications/:appId/accept */
export function acceptApplication(
  projectId: string,
  applicationId: string,
): Promise<MessageResponse> {
  return post<MessageResponse>(
    `/projects/${projectId}/applications/${applicationId}/accept`,
  )
}

/** POST /projects/:id/applications/:appId/reject */
export function rejectApplication(
  projectId: string,
  applicationId: string,
): Promise<MessageResponse> {
  return post<MessageResponse>(
    `/projects/${projectId}/applications/${applicationId}/reject`,
  )
}

/** PATCH /projects/:id/members/:mid/role */
export function changeMemberRole(
  projectId: string,
  membershipId: string,
  data: ChangeMemberRoleRequest,
): Promise<MessageResponse> {
  return patch<MessageResponse>(
    `/projects/${projectId}/members/${membershipId}/role`,
    data,
  )
}

/** DELETE /projects/:id/members/:mid */
export function removeMember(
  projectId: string,
  membershipId: string,
): Promise<MessageResponse> {
  return del<MessageResponse>(
    `/projects/${projectId}/members/${membershipId}`,
  )
}
