/**
 * API functions for Cohort Learning endpoints.
 *
 * All paths are relative to /api and handled by the typed fetch wrapper
 * in client.ts which injects the JWT automatically.
 */

import { del, get, post } from "./client"
import type {
  CohortResponse,
  CreatePracticeTaskRequest,
  EnrolLearnerRequest,
  FormCohortRequest,
  HelperMetricsResponse,
  LeaderboardEntryResponse,
  MessageResponse,
  PendingCompetencyValidationResponse,
  PendingCuratorPromotionResponse,
  PracticeTaskResponse,
  PromoteToModuleCuratorRequest,
  PromoteToTopicExpertRequest,
  RewardBalanceResponse,
  RewardEntryResponse,
  SubmitPeerReviewRequest,
  SubmitTaskSolutionRequest,
  TopicExpertResponse,
  ValidateTopicCompetencyRequest,
} from "./types"

// ---------------------------------------------------------------------------
// Cohorts
// ---------------------------------------------------------------------------

/** POST /cohorts — form a new cohort */
export function formCohort(data: FormCohortRequest): Promise<CohortResponse> {
  return post<CohortResponse>("/cohorts", data)
}

/** GET /cohorts — list cohorts for the authenticated user */
export function listMyCohorts(): Promise<CohortResponse[]> {
  return get<CohortResponse[]>("/cohorts")
}

/** GET /cohorts/:id */
export function getCohort(cohortId: string): Promise<CohortResponse> {
  return get<CohortResponse>(`/cohorts/${cohortId}`)
}

/** POST /cohorts/:id/learners */
export function enrolLearner(
  cohortId: string,
  data: EnrolLearnerRequest,
): Promise<MessageResponse> {
  return post<MessageResponse>(`/cohorts/${cohortId}/learners`, data)
}

/** DELETE /cohorts/:id/learners/:mid */
export function removeLearner(
  cohortId: string,
  membershipId: string,
): Promise<MessageResponse> {
  return del<MessageResponse>(`/cohorts/${cohortId}/learners/${membershipId}`)
}

/** POST /cohorts/:id/activate */
export function activateCohort(cohortId: string): Promise<MessageResponse> {
  return post<MessageResponse>(`/cohorts/${cohortId}/activate`)
}

/** POST /cohorts/:id/begin-completing */
export function beginCompletingCohort(cohortId: string): Promise<MessageResponse> {
  return post<MessageResponse>(`/cohorts/${cohortId}/begin-completing`)
}

/** POST /cohorts/:id/graduate */
export function graduateCohort(cohortId: string): Promise<MessageResponse> {
  return post<MessageResponse>(`/cohorts/${cohortId}/graduate`)
}

/** POST /cohorts/:id/cancel */
export function cancelCohort(cohortId: string): Promise<MessageResponse> {
  return post<MessageResponse>(`/cohorts/${cohortId}/cancel`)
}

// ---------------------------------------------------------------------------
// Practice Tasks
// ---------------------------------------------------------------------------

/** POST /cohorts/:id/tasks */
export function createTask(
  cohortId: string,
  data: CreatePracticeTaskRequest,
): Promise<PracticeTaskResponse> {
  return post<PracticeTaskResponse>(`/cohorts/${cohortId}/tasks`, data)
}

/** GET /cohorts/:id/tasks */
export function listTasks(cohortId: string): Promise<PracticeTaskResponse[]> {
  return get<PracticeTaskResponse[]>(`/cohorts/${cohortId}/tasks`)
}

/** POST /cohorts/:id/tasks/:tid/activate */
export function activateTask(
  cohortId: string,
  taskId: string,
): Promise<MessageResponse> {
  return post<MessageResponse>(`/cohorts/${cohortId}/tasks/${taskId}/activate`)
}

/** POST /cohorts/:id/tasks/:tid/close */
export function closeTask(
  cohortId: string,
  taskId: string,
): Promise<MessageResponse> {
  return post<MessageResponse>(`/cohorts/${cohortId}/tasks/${taskId}/close`)
}

/** POST /cohorts/:id/tasks/:tid/submissions */
export function submitSolution(
  cohortId: string,
  taskId: string,
  data: SubmitTaskSolutionRequest,
): Promise<MessageResponse> {
  return post<MessageResponse>(
    `/cohorts/${cohortId}/tasks/${taskId}/submissions`,
    data,
  )
}

/** POST /cohorts/:id/tasks/:tid/submissions/:sid/reviews */
export function submitReview(
  cohortId: string,
  taskId: string,
  submissionId: string,
  data: SubmitPeerReviewRequest,
): Promise<MessageResponse> {
  return post<MessageResponse>(
    `/cohorts/${cohortId}/tasks/${taskId}/submissions/${submissionId}/reviews`,
    data,
  )
}

// ---------------------------------------------------------------------------
// Progression / Partner metrics
// ---------------------------------------------------------------------------

/** GET /cohorts/:id/helper-metrics */
export function getHelperMetrics(cohortId: string): Promise<HelperMetricsResponse[]> {
  return get<HelperMetricsResponse[]>(`/cohorts/${cohortId}/helper-metrics`)
}

/** GET /cohorts/:id/topic-experts */
export function getTopicExperts(cohortId: string): Promise<TopicExpertResponse[]> {
  return get<TopicExpertResponse[]>(`/cohorts/${cohortId}/topic-experts`)
}

/** GET /cohorts/:id/leaderboard */
export function getLeaderboard(cohortId: string): Promise<LeaderboardEntryResponse[]> {
  return get<LeaderboardEntryResponse[]>(`/cohorts/${cohortId}/leaderboard`)
}

/** POST /cohorts/:id/members/:lid/validate-competency */
export function validateCompetency(
  cohortId: string,
  learnerId: string,
  data: ValidateTopicCompetencyRequest,
): Promise<MessageResponse> {
  return post<MessageResponse>(
    `/cohorts/${cohortId}/members/${learnerId}/validate-competency`,
    data,
  )
}

/** POST /cohorts/:id/members/:lid/promote-expert */
export function promoteExpert(
  cohortId: string,
  learnerId: string,
  data: PromoteToTopicExpertRequest,
): Promise<MessageResponse> {
  return post<MessageResponse>(
    `/cohorts/${cohortId}/members/${learnerId}/promote-expert`,
    data,
  )
}

/** POST /cohorts/:id/members/:lid/promote-curator */
export function promoteCurator(
  cohortId: string,
  learnerId: string,
  data: PromoteToModuleCuratorRequest,
): Promise<MessageResponse> {
  return post<MessageResponse>(
    `/cohorts/${cohortId}/members/${learnerId}/promote-curator`,
    data,
  )
}

// ---------------------------------------------------------------------------
// Dashboard queues (Stage 17-18)
// ---------------------------------------------------------------------------

/** GET /cohorts/:id/pending-competency-validations */
export function getPendingValidations(
  cohortId: string,
): Promise<PendingCompetencyValidationResponse[]> {
  return get<PendingCompetencyValidationResponse[]>(
    `/cohorts/${cohortId}/pending-competency-validations`,
  )
}

/** GET /cohorts/:id/pending-curator-promotions */
export function getPendingPromotions(
  cohortId: string,
): Promise<PendingCuratorPromotionResponse[]> {
  return get<PendingCuratorPromotionResponse[]>(
    `/cohorts/${cohortId}/pending-curator-promotions`,
  )
}

// ---------------------------------------------------------------------------
// Rewards (current user)
// ---------------------------------------------------------------------------

/** GET /me/rewards */
export function getMyRewards(): Promise<RewardBalanceResponse> {
  return get<RewardBalanceResponse>("/me/rewards")
}

/** GET /me/rewards/history */
export function getMyRewardHistory(): Promise<RewardEntryResponse[]> {
  return get<RewardEntryResponse[]>("/me/rewards/history")
}
