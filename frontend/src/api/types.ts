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
  invite_code: string
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

/** POST /auth/local/set-password — request body */
export interface SetPasswordRequest {
  password: string
}

/** PATCH /auth/me — request body (both fields optional) */
export interface UpdateProfileRequest {
  email?: string
  display_name?: string
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

// ---------------------------------------------------------------------------
// Cohorts
// ---------------------------------------------------------------------------

export type CohortStatus = "forming" | "active" | "completing" | "graduated" | "cancelled"

/** POST /cohorts — request body */
export interface FormCohortRequest {
  cohort_id: string
  module_id: string
}

/** POST /cohorts/{id}/learners — request body */
export interface EnrolLearnerRequest {
  membership_id: string
  learner_id: string
}

/** A single cohort membership */
export interface CohortMembershipResponse {
  membership_id: string
  learner_id: string
  cohort_id: string
  role: string
  is_active: boolean
  joined_at: string
}

/** Full cohort response */
export interface CohortResponse {
  cohort_id: string
  master_id: string
  module_id: string
  status: CohortStatus
  formed_at: string
  memberships: CohortMembershipResponse[]
}

/** POST /cohorts/{id}/tasks — request body */
export interface CreatePracticeTaskRequest {
  task_id: string
  topic_id: string
  title: string
  description?: string
}

/** Task submission */
export interface TaskSubmissionResponse {
  submission_id: string
  task_id: string
  learner_id: string
  content: string
  status: string
  submitted_at: string
}

/** Full practice task response */
export interface PracticeTaskResponse {
  task_id: string
  cohort_id: string
  topic_id: string
  creator_id: string
  title: string
  description: string
  status: string
  created_at: string
  submissions: TaskSubmissionResponse[]
}

/** POST /cohorts/{id}/tasks/{tid}/submissions — request body */
export interface SubmitTaskSolutionRequest {
  submission_id: string
  content: string
}

/** A single score within a peer review */
export interface ReviewScoreResponse {
  criterion: string
  score: number
  comment: string
}

/** Full peer review response */
export interface PeerReviewResponse {
  review_id: string
  submission_id: string
  reviewer_id: string
  task_id: string
  cohort_id: string
  status: string
  overall_feedback: string
  created_at: string
  reviewed_at: string | null
  scores: ReviewScoreResponse[]
}

/** POST /cohorts/{id}/tasks/{tid}/submissions/{sid}/reviews — request body */
export interface SubmitPeerReviewRequest {
  review_id: string
  scores: { criterion: string; score: number; comment?: string }[]
  overall_feedback?: string
}

/** Leaderboard entry */
export interface LeaderboardEntryResponse {
  learner_id: string
  total_xp: number
  rank: number
}

/** Helper metrics */
export interface HelperMetricsResponse {
  learner_id: string
  cohort_id: string
  learners_helped: number
  questions_answered: number
  tasks_reviewed: number
  average_satisfaction: number | null
  updated_at: string
}

/** Topic expert */
export interface TopicExpertResponse {
  expert_id: string
  learner_id: string
  topic_id: string
  cohort_id: string
  validated_at: string
  validator_id: string
}

/** Pending competency validation */
export interface PendingCompetencyValidationResponse {
  pending_id: string
  learner_id: string
  topic_id: string
  cohort_id: string
  created_at: string
}

/** Pending curator promotion */
export interface PendingCuratorPromotionResponse {
  pending_id: string
  learner_id: string
  module_id: string
  cohort_id: string
  created_at: string
}

/** POST /cohorts/{id}/members/{lid}/validate-competency — request body */
export interface ValidateTopicCompetencyRequest {
  topic_id: string
  knowledge_check_score: number
  mentor_approved: boolean
}

/** POST /cohorts/{id}/members/{lid}/promote-expert — request body */
export interface PromoteToTopicExpertRequest {
  expert_id: string
  topic_id: string
}

/** POST /cohorts/{id}/members/{lid}/promote-curator — request body */
export interface PromoteToModuleCuratorRequest {
  curator_id: string
  module_id: string
}

/** Reward balance */
export interface RewardBalanceResponse {
  learner_id: string
  total_xp: number
  total_credits: number
  badges: string[]
  reputation_score: number | null
}

/** Reward entry */
export interface RewardEntryResponse {
  entry_id: string
  learner_id: string
  reward_type: string
  amount: number | null
  metadata: Record<string, string>
  granted_at: string
  triggering_event: string | null
  cohort_id: string | null
}

// ---------------------------------------------------------------------------
// Modules & Topics
// ---------------------------------------------------------------------------

export interface TopicResponse {
  topic_id: string
  title: string
  position: number
  description: string
}

export interface ModuleResponse {
  module_id: string
  title: string
  master_id: string
  topics: TopicResponse[]
  topic_count: number
}

export interface CreateModuleRequest {
  module_id: string
  title: string
}

export interface AddTopicRequest {
  topic_id: string
  title: string
  position: number
  description: string
}

// ---------------------------------------------------------------------------
// Partnership / Earnings
// ---------------------------------------------------------------------------

export type CommissionStatus = "pending" | "released"

/** Single curator commission (GET /me/earnings, GET /me/earnings/history) */
export interface CommissionResponse {
  commission_id: string
  curator_id: string
  cohort_id: string
  module_id: string
  base_amount: number
  bonus_amount: number
  total_amount: number
  status: CommissionStatus
  earned_at: string
  release_eligible_at: string
  released_at: string | null
}

/** GET /me/earnings — aggregated summary */
export interface EarningsSummaryResponse {
  curator_id: string
  total_pending: number
  total_released: number
  commissions: CommissionResponse[]
}
