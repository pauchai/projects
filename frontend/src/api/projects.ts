/**
 * Projects API functions: CRUD, search, status transitions, applications, members.
 */

import { del, get, getText, patch, post } from "./client"
import type {
  ApplyToProjectRequest,
  ChangeMemberRoleRequest,
  CreateProjectRequest,
  MessageResponse,
  ProjectResponse,
  ProjectSummaryResponse,
  SearchProjectsParams,
  SyncResponse,
  UpdateProjectRequest,
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
  if (params?.owner_id) queryParams.owner_id = params.owner_id
  if (params?.member_user_id) queryParams.member_user_id = params.member_user_id
  return get<ProjectSummaryResponse[]>("/projects/search", queryParams)
}

/** GET /projects/:id — get project detail */
export function getProject(projectId: string): Promise<ProjectResponse> {
  return get<ProjectResponse>(`/projects/${projectId}`)
}

/** PATCH /projects/:id — update project */
export function updateProject(
  projectId: string,
  data: UpdateProjectRequest,
): Promise<ProjectResponse> {
  return patch<ProjectResponse>(`/projects/${projectId}`, data)
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

// ---------------------------------------------------------------------------
// Docs repo URL & sync
// ---------------------------------------------------------------------------

export function setDocsRepoUrl(
  projectId: string,
  docsRepoUrl: string | null,
): Promise<ProjectResponse> {
  return patch<ProjectResponse>(`/projects/${projectId}/docs-repo-url`, {
    docs_repo_url: docsRepoUrl,
  })
}

export function syncDocsVolume(projectId: string): Promise<SyncResponse> {
  return post<SyncResponse>(`/projects/${projectId}/sync-docs`, {})
}

export function getDocsFile(projectId: string, filePath: string): Promise<string> {
  return getText(`/projects/${projectId}/docs/${filePath}`)
}

export function getDocsTree(projectId: string): Promise<{ files: string[] }> {
  return get<{ files: string[] }>(`/projects/${projectId}/docs`)
}
