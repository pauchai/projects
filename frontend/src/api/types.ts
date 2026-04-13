/**
 * TypeScript interfaces matching backend API request/response shapes.
 *
 * These types form the contract between frontend and backend.
 * Keep in sync with:
 *   - src/auth/api/schemas.py
 *   - src/project_collaboration/api/schemas.py
 */

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

/** POST /auth/register — request body */
export interface RegisterRequest {
  email: string
  password: string
  display_name: string
}

/** POST /auth/register — response */
export interface UserResponse {
  user_id: string
  email: string
  display_name: string
}

/** POST /auth/login — request body */
export interface LoginRequest {
  email: string
  password: string
}

/** POST /auth/login — response */
export interface TokenResponse {
  access_token: string
  token_type: string
}

// ---------------------------------------------------------------------------
// OAuth
// ---------------------------------------------------------------------------

/** GET /auth/oauth/google/available — response */
export interface OAuthAvailableResponse {
  available: boolean
}

/** GET /auth/oauth/google/authorize — response */
export interface OAuthAuthorizeResponse {
  authorization_url: string
  state: string
}

/** POST /auth/oauth/google/callback — request body */
export interface OAuthCallbackRequest {
  code: string
  state: string
}

/** GET /auth/oauth/telegram/authorize — response */
export interface TelegramAuthorizeResponse {
  telegram_url: string
  state: string
}

// ---------------------------------------------------------------------------
// Project Collaboration
// ---------------------------------------------------------------------------

/** POST /projects — request body */
export interface CreateProjectRequest {
  project_id: string
  title: string
  description?: string
  required_skills?: string[]
  max_members?: number | null
}

/** GET /projects/search — query params */
export interface SearchProjectsParams {
  keyword?: string
  status?: string
  skills?: string
  owner_id?: string
  member_user_id?: string
}

/** Membership within a project */
export interface MembershipResponse {
  membership_id: string
  user_id: string
  project_id: string
  role: string
  is_active: boolean
  joined_at: string
}

/** Application to join a project */
export interface ApplicationResponse {
  application_id: string
  applicant_id: string
  project_id: string
  desired_role: string
  motivation: string
  applicant_skills: string[]
  status: string
  reviewed_by: string | null
  submitted_at: string
}

/** Full project detail (GET /projects/:id, POST /projects) */
export interface ProjectResponse {
  project_id: string
  title: string
  description: string
  owner_id: string
  required_skills: string[]
  max_members: number | null
  status: string
  created_at: string
  memberships: MembershipResponse[]
  applications: ApplicationResponse[]
}

/** Project summary for search results */
export interface ProjectSummaryResponse {
  project_id: string
  title: string
  description: string
  owner_id: string
  required_skills: string[]
  status: string
  created_at: string
}

/** POST /projects/:id/applications — request body */
export interface ApplyToProjectRequest {
  application_id: string
  desired_role: string
  motivation?: string
  applicant_skills?: string[]
}

/** PATCH /projects/:id — request body */
export interface UpdateProjectRequest {
  title: string
  description?: string
  required_skills?: string[]
  max_members?: number | null
}

/** PATCH /projects/:id/members/:mid/role — request body */
export interface ChangeMemberRoleRequest {
  new_role: string
}

/** Generic message response from action endpoints */
export interface MessageResponse {
  message: string
}

/** API error response shape */
export interface ApiErrorResponse {
  detail: string
}

// ---------------------------------------------------------------------------
// Feature Requests
// ---------------------------------------------------------------------------

/** Feature request status values */
export type FeatureStatus =
  | "submitted"
  | "planned"
  | "in_progress"
  | "done"
  | "rejected"

/** GET /features — query params */
export interface ListFeaturesParams {
  status?: string
  author_id?: string
}

/** POST /features — request body */
export interface CreateFeatureRequestRequest {
  request_id: string
  title: string
  description: string
  category?: string | null
  priority?: string | null
}

/** PUT /admin/features/:id/status — request body */
export interface UpdateFeatureStatusRequest {
  status: string
  admin_notes?: string | null
}

/** Feature request response (GET /features, GET /features/:id, POST /features) */
export interface FeatureRequestResponse {
  request_id: string
  author_id: string
  title: string
  description: string
  status: FeatureStatus
  category: string | null
  priority: string | null
  admin_notes: string
  created_at: string
  updated_at: string
}

// ---------------------------------------------------------------------------
// Credentials management
// ---------------------------------------------------------------------------

/** A single credential (sign-in method) */
export interface CredentialResponse {
  credential_id: string
  provider: string
  provider_display_name: string
  provider_user_id: string
  is_removable: boolean
}

/** GET /auth/credentials — all sign-in methods for the current user */
export interface CredentialsListResponse {
  user_email: string
  user_display_name: string
  credentials: CredentialResponse[]
  total_count: number
  has_local_credential: boolean
}
