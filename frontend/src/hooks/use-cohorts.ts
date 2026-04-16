/**
 * TanStack Query hooks for Cohort Learning operations.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import * as cohortsApi from "@/api/cohorts"
import type {
  CreatePracticeTaskRequest,
  EnrolLearnerRequest,
  FormCohortRequest,
  PromoteToModuleCuratorRequest,
  PromoteToTopicExpertRequest,
  SubmitPeerReviewRequest,
  SubmitTaskSolutionRequest,
  ValidateTopicCompetencyRequest,
} from "@/api/types"

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

export const cohortKeys = {
  all: ["cohorts"] as const,
  list: () => [...cohortKeys.all, "list"] as const,
  detail: (cohortId: string) => [...cohortKeys.all, "detail", cohortId] as const,
  tasks: (cohortId: string) => [...cohortKeys.all, "tasks", cohortId] as const,
  leaderboard: (cohortId: string) =>
    [...cohortKeys.all, "leaderboard", cohortId] as const,
  helperMetrics: (cohortId: string) =>
    [...cohortKeys.all, "helperMetrics", cohortId] as const,
  topicExperts: (cohortId: string) =>
    [...cohortKeys.all, "topicExperts", cohortId] as const,
  pendingValidations: (cohortId: string) =>
    [...cohortKeys.all, "pendingValidations", cohortId] as const,
  pendingPromotions: (cohortId: string) =>
    [...cohortKeys.all, "pendingPromotions", cohortId] as const,
  myRewards: () => ["rewards", "me"] as const,
  myRewardHistory: () => ["rewards", "me", "history"] as const,
}

// ---------------------------------------------------------------------------
// Queries
// ---------------------------------------------------------------------------

/** List all cohorts for the authenticated user */
export function useMyCohorts() {
  return useQuery({
    queryKey: cohortKeys.list(),
    queryFn: () => cohortsApi.listMyCohorts(),
  })
}

/** Get a single cohort by ID */
export function useCohort(cohortId: string) {
  return useQuery({
    queryKey: cohortKeys.detail(cohortId),
    queryFn: () => cohortsApi.getCohort(cohortId),
    enabled: !!cohortId,
  })
}

/** List tasks for a cohort */
export function useCohortTasks(cohortId: string) {
  return useQuery({
    queryKey: cohortKeys.tasks(cohortId),
    queryFn: () => cohortsApi.listTasks(cohortId),
    enabled: !!cohortId,
  })
}

/** Leaderboard for a cohort */
export function useCohortLeaderboard(cohortId: string) {
  return useQuery({
    queryKey: cohortKeys.leaderboard(cohortId),
    queryFn: () => cohortsApi.getLeaderboard(cohortId),
    enabled: !!cohortId,
  })
}

/** Helper metrics for a cohort */
export function useCohortHelperMetrics(cohortId: string) {
  return useQuery({
    queryKey: cohortKeys.helperMetrics(cohortId),
    queryFn: () => cohortsApi.getHelperMetrics(cohortId),
    enabled: !!cohortId,
  })
}

/** Topic experts for a cohort */
export function useCohortTopicExperts(cohortId: string) {
  return useQuery({
    queryKey: cohortKeys.topicExperts(cohortId),
    queryFn: () => cohortsApi.getTopicExperts(cohortId),
    enabled: !!cohortId,
  })
}

/** Pending competency validations queue */
export function usePendingValidations(cohortId: string) {
  return useQuery({
    queryKey: cohortKeys.pendingValidations(cohortId),
    queryFn: () => cohortsApi.getPendingValidations(cohortId),
    enabled: !!cohortId,
  })
}

/** Pending curator promotions queue */
export function usePendingPromotions(cohortId: string) {
  return useQuery({
    queryKey: cohortKeys.pendingPromotions(cohortId),
    queryFn: () => cohortsApi.getPendingPromotions(cohortId),
    enabled: !!cohortId,
  })
}

/** Authenticated user's reward balance */
export function useMyRewards() {
  return useQuery({
    queryKey: cohortKeys.myRewards(),
    queryFn: () => cohortsApi.getMyRewards(),
  })
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

/** Form (create) a new cohort */
export function useFormCohort() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: FormCohortRequest) => cohortsApi.formCohort(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cohortKeys.list() })
    },
  })
}

/** Enrol a learner */
export function useEnrolLearner() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ cohortId, data }: { cohortId: string; data: EnrolLearnerRequest }) =>
      cohortsApi.enrolLearner(cohortId, data),
    onSuccess: (_data, { cohortId }) => {
      queryClient.invalidateQueries({ queryKey: cohortKeys.detail(cohortId) })
    },
  })
}

/** Remove a learner */
export function useRemoveLearner() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      cohortId,
      membershipId,
    }: {
      cohortId: string
      membershipId: string
    }) => cohortsApi.removeLearner(cohortId, membershipId),
    onSuccess: (_data, { cohortId }) => {
      queryClient.invalidateQueries({ queryKey: cohortKeys.detail(cohortId) })
    },
  })
}

/** Helper: cohort status-transition mutations (activate / begin-completing / graduate / cancel) */
function useCohortStatusAction(actionFn: (cohortId: string) => Promise<unknown>) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: actionFn,
    onSuccess: (_data, cohortId) => {
      queryClient.invalidateQueries({ queryKey: cohortKeys.detail(cohortId) })
      queryClient.invalidateQueries({ queryKey: cohortKeys.list() })
    },
  })
}

export function useActivateCohort() {
  return useCohortStatusAction(cohortsApi.activateCohort)
}
export function useBeginCompletingCohort() {
  return useCohortStatusAction(cohortsApi.beginCompletingCohort)
}
export function useGraduateCohort() {
  return useCohortStatusAction(cohortsApi.graduateCohort)
}
export function useCancelCohort() {
  return useCohortStatusAction(cohortsApi.cancelCohort)
}

/** Create a practice task */
export function useCreateTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      cohortId,
      data,
    }: {
      cohortId: string
      data: CreatePracticeTaskRequest
    }) => cohortsApi.createTask(cohortId, data),
    onSuccess: (_data, { cohortId }) => {
      queryClient.invalidateQueries({ queryKey: cohortKeys.tasks(cohortId) })
    },
  })
}

/** Submit a task solution */
export function useSubmitSolution() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      cohortId,
      taskId,
      data,
    }: {
      cohortId: string
      taskId: string
      data: SubmitTaskSolutionRequest
    }) => cohortsApi.submitSolution(cohortId, taskId, data),
    onSuccess: (_data, { cohortId }) => {
      queryClient.invalidateQueries({ queryKey: cohortKeys.tasks(cohortId) })
    },
  })
}

/** Submit a peer review */
export function useSubmitReview() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      cohortId,
      taskId,
      submissionId,
      data,
    }: {
      cohortId: string
      taskId: string
      submissionId: string
      data: SubmitPeerReviewRequest
    }) => cohortsApi.submitReview(cohortId, taskId, submissionId, data),
    onSuccess: (_data, { cohortId }) => {
      queryClient.invalidateQueries({ queryKey: cohortKeys.tasks(cohortId) })
    },
  })
}

/** Validate topic competency */
export function useValidateCompetency() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      cohortId,
      learnerId,
      data,
    }: {
      cohortId: string
      learnerId: string
      data: ValidateTopicCompetencyRequest
    }) => cohortsApi.validateCompetency(cohortId, learnerId, data),
    onSuccess: (_data, { cohortId }) => {
      queryClient.invalidateQueries({ queryKey: cohortKeys.detail(cohortId) })
      queryClient.invalidateQueries({ queryKey: cohortKeys.pendingValidations(cohortId) })
    },
  })
}

/** Promote to topic expert */
export function usePromoteExpert() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      cohortId,
      learnerId,
      data,
    }: {
      cohortId: string
      learnerId: string
      data: PromoteToTopicExpertRequest
    }) => cohortsApi.promoteExpert(cohortId, learnerId, data),
    onSuccess: (_data, { cohortId }) => {
      queryClient.invalidateQueries({ queryKey: cohortKeys.topicExperts(cohortId) })
    },
  })
}

/** Promote to module curator */
export function usePromoteCurator() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      cohortId,
      learnerId,
      data,
    }: {
      cohortId: string
      learnerId: string
      data: PromoteToModuleCuratorRequest
    }) => cohortsApi.promoteCurator(cohortId, learnerId, data),
    onSuccess: (_data, { cohortId }) => {
      queryClient.invalidateQueries({ queryKey: cohortKeys.pendingPromotions(cohortId) })
    },
  })
}
