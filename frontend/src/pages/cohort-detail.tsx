import { useState } from "react"
import { useParams, Link } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { useAuthStore } from "@/stores/auth-store"
import {
  useCohort,
  useCohortTasks,
  useCohortLeaderboard,
  useCohortHelperMetrics,
  useCohortTopicExperts,
  useActivateCohort,
  useBeginCompletingCohort,
  useGraduateCohort,
  useCancelCohort,
  useEnrolLearner,
  useRemoveLearner,
  useCreateTask,
  useActivateTask,
  useCloseTask,
  useSubmitSolution,
  useSubmitReview,
} from "@/hooks/use-cohorts"
import { useModule } from "@/hooks/use-modules"
import { ApiError } from "@/api/client"
import type { CohortStatus } from "@/api/types"

// ---------------------------------------------------------------------------
// Constants & helpers
// ---------------------------------------------------------------------------

const REVIEW_CRITERIA = ["correctness", "clarity", "completeness"] as const

type ScoreMap = Record<string, { score: number; comment: string }>

function defaultScores(): ScoreMap {
  return Object.fromEntries(REVIEW_CRITERIA.map((c) => [c, { score: 3, comment: "" }]))
}

const STATUS_VARIANT: Record<CohortStatus, "default" | "secondary" | "outline" | "destructive"> = {
  forming: "secondary",
  active: "default",
  completing: "outline",
  graduated: "secondary",
  cancelled: "destructive",
}

type Tab = "overview" | "tasks" | "progression" | "leaderboard"

// ---------------------------------------------------------------------------
// State shape interfaces
// ---------------------------------------------------------------------------

interface SolutionFormState {
  open: boolean
  content: string
  error: string | null
}

interface ReviewFormState {
  open: boolean
  scores: ScoreMap
  feedback: string
  error: string | null
}

interface CreateTaskFormState {
  open: boolean
  title: string
  topicId: string
  description: string
  error: string | null
}

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

export function CohortDetailPage() {
  const { cohortId } = useParams<{ cohortId: string }>()
  const userId = useAuthStore((s) => s.userId)
  const [activeTab, setActiveTab] = useState<Tab>("overview")
  const [actionError, setActionError] = useState<string | null>(null)
  const [enrolId, setEnrolId] = useState("")

  // Task UI state
  const [solutionForms, setSolutionForms] = useState<Record<string, SolutionFormState>>({})
  const [reviewForms, setReviewForms] = useState<Record<string, ReviewFormState>>({})
  const [createTaskForm, setCreateTaskForm] = useState<CreateTaskFormState>({
    open: false,
    title: "",
    topicId: "",
    description: "",
    error: null,
  })

  // ---------------------------------------------------------------------------
  // Queries — all hooks must be called unconditionally before any early return
  // ---------------------------------------------------------------------------

  const { data: cohort, isLoading, isError, error } = useCohort(cohortId ?? "")
  const { data: tasks } = useCohortTasks(cohortId ?? "")
  const { data: leaderboard } = useCohortLeaderboard(cohortId ?? "")
  const { data: helperMetrics } = useCohortHelperMetrics(cohortId ?? "")
  const { data: topicExperts } = useCohortTopicExperts(cohortId ?? "")
  // Fetch module (for topic dropdown in Create Task form). enabled guard inside useModule.
  const { data: module } = useModule(cohort?.module_id ?? "")

  // ---------------------------------------------------------------------------
  // Mutations
  // ---------------------------------------------------------------------------

  const activateCohort = useActivateCohort()
  const beginCompleting = useBeginCompletingCohort()
  const graduateCohort = useGraduateCohort()
  const cancelCohort = useCancelCohort()
  const enrolLearner = useEnrolLearner()
  const removeLearner = useRemoveLearner()
  const createTask = useCreateTask()
  const activateTask = useActivateTask()
  const closeTask = useCloseTask()
  const submitSolution = useSubmitSolution()
  const submitReview = useSubmitReview()

  // ---------------------------------------------------------------------------
  // Early returns
  // ---------------------------------------------------------------------------

  if (isLoading) return <p className="text-muted-foreground">Loading cohort...</p>
  if (isError) {
    return (
      <p className="text-destructive">
        Failed to load cohort: {error instanceof Error ? error.message : "Unknown error"}
      </p>
    )
  }
  if (!cohort) return null

  // ---------------------------------------------------------------------------
  // Derived values
  // ---------------------------------------------------------------------------

  const isMaster = cohort.master_id === userId
  const myMembership = cohort.memberships.find((m) => m.learner_id === userId && m.is_active)
  const canManageTasks = isMaster || myMembership?.role === "curator"
  const activeMembers = cohort.memberships.filter((m) => m.is_active)

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  const handleAction = async (fn: () => Promise<unknown>) => {
    setActionError(null)
    try {
      await fn()
    } catch (e) {
      setActionError(e instanceof ApiError ? e.detail : "Action failed")
    }
  }

  const handleEnrol = () => {
    if (!enrolId.trim()) return
    handleAction(() =>
      enrolLearner.mutateAsync({
        cohortId: cohort.cohort_id,
        data: { membership_id: crypto.randomUUID(), learner_id: enrolId.trim() },
      }),
    ).then(() => setEnrolId(""))
  }

  const handleCreateTask = async () => {
    if (!createTaskForm.title.trim() || !createTaskForm.topicId) {
      setCreateTaskForm((f) => ({ ...f, error: "Title and topic are required." }))
      return
    }
    setCreateTaskForm((f) => ({ ...f, error: null }))
    try {
      await createTask.mutateAsync({
        cohortId: cohort.cohort_id,
        data: {
          task_id: crypto.randomUUID(),
          topic_id: createTaskForm.topicId,
          title: createTaskForm.title.trim(),
          description: createTaskForm.description.trim() || undefined,
        },
      })
      setCreateTaskForm({ open: false, title: "", topicId: "", description: "", error: null })
    } catch (e) {
      setCreateTaskForm((f) => ({
        ...f,
        error: e instanceof ApiError ? e.detail : "Failed to create task.",
      }))
    }
  }

  const handleSubmitSolution = async (taskId: string) => {
    const form = solutionForms[taskId]
    if (!form?.content.trim()) return
    setSolutionForms((prev) => ({ ...prev, [taskId]: { ...prev[taskId], error: null } }))
    try {
      await submitSolution.mutateAsync({
        cohortId: cohort.cohort_id,
        taskId,
        data: { submission_id: crypto.randomUUID(), content: form.content.trim() },
      })
      setSolutionForms((prev) => ({ ...prev, [taskId]: { open: false, content: "", error: null } }))
    } catch (e) {
      setSolutionForms((prev) => ({
        ...prev,
        [taskId]: {
          ...prev[taskId],
          error: e instanceof ApiError ? e.detail : "Failed to submit.",
        },
      }))
    }
  }

  const handleSubmitReview = async (taskId: string, submissionId: string) => {
    const form = reviewForms[submissionId]
    if (!form) return
    setReviewForms((prev) => ({ ...prev, [submissionId]: { ...prev[submissionId], error: null } }))
    try {
      await submitReview.mutateAsync({
        cohortId: cohort.cohort_id,
        taskId,
        submissionId,
        data: {
          review_id: crypto.randomUUID(),
          scores: REVIEW_CRITERIA.map((c) => ({
            criterion: c,
            score: form.scores[c]?.score ?? 3,
            comment: form.scores[c]?.comment || undefined,
          })),
          overall_feedback: form.feedback.trim() || undefined,
        },
      })
      setReviewForms((prev) => ({ ...prev, [submissionId]: { open: false, scores: defaultScores(), feedback: "", error: null } }))
    } catch (e) {
      setReviewForms((prev) => ({
        ...prev,
        [submissionId]: {
          ...prev[submissionId],
          error: e instanceof ApiError ? e.detail : "Failed to submit review.",
        },
      }))
    }
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{cohort.cohort_id}</h1>
            <Badge variant={STATUS_VARIANT[cohort.status]}>{cohort.status}</Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Module: {cohort.module_id} &nbsp;·&nbsp; Master: {cohort.master_id}
          </p>
        </div>
        <div className="flex gap-2 flex-wrap">
          {isMaster && (
            <Link to={`/cohorts/${cohort.cohort_id}/dashboard`}>
              <Button variant="outline" size="sm">Dashboard</Button>
            </Link>
          )}
        </div>
      </div>

      {/* Status actions (master only) */}
      {isMaster && (
        <div className="flex flex-wrap gap-2">
          {cohort.status === "forming" && (
            <Button
              size="sm"
              onClick={() => handleAction(() => activateCohort.mutateAsync(cohort.cohort_id))}
              disabled={activateCohort.isPending}
            >
              Activate
            </Button>
          )}
          {cohort.status === "active" && (
            <Button
              size="sm"
              onClick={() => handleAction(() => beginCompleting.mutateAsync(cohort.cohort_id))}
              disabled={beginCompleting.isPending}
            >
              Begin Completing
            </Button>
          )}
          {cohort.status === "completing" && (
            <Button
              size="sm"
              onClick={() => handleAction(() => graduateCohort.mutateAsync(cohort.cohort_id))}
              disabled={graduateCohort.isPending}
            >
              Graduate
            </Button>
          )}
          {["forming", "active", "completing"].includes(cohort.status) && (
            <Button
              variant="destructive"
              size="sm"
              onClick={() => handleAction(() => cancelCohort.mutateAsync(cohort.cohort_id))}
              disabled={cancelCohort.isPending}
            >
              Cancel
            </Button>
          )}
        </div>
      )}

      {actionError && <p className="text-destructive text-sm">{actionError}</p>}

      {/* Tabs */}
      <div className="flex gap-1 border-b border-border">
        {(["overview", "tasks", "progression", "leaderboard"] as Tab[]).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm capitalize transition-colors ${
              activeTab === tab
                ? "border-b-2 border-foreground font-medium text-foreground"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Tab: Overview                                                        */}
      {/* ------------------------------------------------------------------ */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          <div>
            <h2 className="font-semibold mb-3">Members ({activeMembers.length})</h2>
            {activeMembers.length === 0 ? (
              <p className="text-muted-foreground text-sm">No active members yet.</p>
            ) : (
              <div className="space-y-2">
                {activeMembers.map((m) => (
                  <div
                    key={m.membership_id}
                    className="flex items-center justify-between rounded border border-border px-3 py-2 text-sm"
                  >
                    <span className="font-mono text-xs">{m.learner_id}</span>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">{m.role}</Badge>
                      {isMaster && cohort.status === "forming" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 px-2 text-destructive hover:text-destructive"
                          onClick={() =>
                            handleAction(() =>
                              removeLearner.mutateAsync({
                                cohortId: cohort.cohort_id,
                                membershipId: m.membership_id,
                              }),
                            )
                          }
                        >
                          Remove
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {isMaster && cohort.status === "forming" && (
            <div>
              <Separator className="mb-4" />
              <h2 className="font-semibold mb-3">Enrol a Learner</h2>
              <div className="flex gap-2 max-w-md">
                <input
                  type="text"
                  placeholder="Learner user ID"
                  value={enrolId}
                  onChange={(e) => setEnrolId(e.target.value)}
                  className="flex-1 rounded border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                />
                <Button size="sm" onClick={handleEnrol} disabled={enrolLearner.isPending}>
                  Enrol
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Tab: Tasks                                                           */}
      {/* ------------------------------------------------------------------ */}
      {activeTab === "tasks" && (
        <div className="space-y-4">

          {/* F3: Create task form (master/curator only) */}
          {canManageTasks && (
            <div className="rounded border border-border p-4 space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold text-sm">New Task</h2>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setCreateTaskForm((f) => ({ ...f, open: !f.open }))}
                >
                  {createTaskForm.open ? "Cancel" : "+ Create Task"}
                </Button>
              </div>
              {createTaskForm.open && (
                <div className="space-y-3">
                  <input
                    type="text"
                    placeholder="Task title"
                    value={createTaskForm.title}
                    onChange={(e) => setCreateTaskForm((f) => ({ ...f, title: e.target.value }))}
                    className="w-full rounded border border-input bg-background text-foreground px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                  <select
                    value={createTaskForm.topicId}
                    onChange={(e) => setCreateTaskForm((f) => ({ ...f, topicId: e.target.value }))}
                    className="w-full rounded border border-input bg-background text-foreground px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  >
                    <option value="">Select a topic…</option>
                    {module?.topics.map((t) => (
                      <option key={t.topic_id} value={t.topic_id}>
                        {t.title}
                      </option>
                    ))}
                  </select>
                  {!module?.topics.length && (
                    <p className="text-xs text-muted-foreground">
                      No topics available — add topics to this module first.
                    </p>
                  )}
                  <textarea
                    placeholder="Description (optional)"
                    value={createTaskForm.description}
                    onChange={(e) => setCreateTaskForm((f) => ({ ...f, description: e.target.value }))}
                    rows={3}
                    className="w-full rounded border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring resize-none"
                  />
                  {createTaskForm.error && (
                    <p className="text-destructive text-xs">{createTaskForm.error}</p>
                  )}
                  <Button size="sm" onClick={handleCreateTask} disabled={createTask.isPending}>
                    {createTask.isPending ? "Creating…" : "Create Task"}
                  </Button>
                </div>
              )}
            </div>
          )}

          {/* Task list */}
          {!tasks || tasks.length === 0 ? (
            <p className="text-muted-foreground text-sm">No practice tasks yet.</p>
          ) : (
            tasks.map((task) => {
              const mySubmission = task.submissions.find((s) => s.learner_id === userId)
              const otherSubmissions = task.submissions.filter((s) => s.learner_id !== userId)
              const solForm = solutionForms[task.task_id]

              return (
                <Card key={task.task_id}>
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between gap-2">
                      <CardTitle className="text-sm">{task.title}</CardTitle>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <Badge variant="outline">{task.status}</Badge>
                        {/* F3: Activate / Close buttons */}
                        {canManageTasks && task.status === "draft" && (
                          <Button
                            variant="secondary"
                            size="sm"
                            className="h-6 px-2 text-xs"
                            disabled={activateTask.isPending}
                            onClick={() =>
                              handleAction(() =>
                                activateTask.mutateAsync({
                                  cohortId: cohort.cohort_id,
                                  taskId: task.task_id,
                                }),
                              )
                            }
                          >
                            Activate
                          </Button>
                        )}
                        {canManageTasks && task.status === "active" && (
                          <Button
                            variant="secondary"
                            size="sm"
                            className="h-6 px-2 text-xs"
                            disabled={closeTask.isPending}
                            onClick={() =>
                              handleAction(() =>
                                closeTask.mutateAsync({
                                  cohortId: cohort.cohort_id,
                                  taskId: task.task_id,
                                }),
                              )
                            }
                          >
                            Close
                          </Button>
                        )}
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground">Topic: {task.topic_id}</p>
                  </CardHeader>

                  <CardContent className="space-y-4">
                    {task.description && (
                      <p className="text-sm text-muted-foreground">{task.description}</p>
                    )}

                    {/* F1: Submit Solution */}
                    {task.status === "active" && (
                      <div className="space-y-2">
                        <Separator />
                        {mySubmission ? (
                          <div className="space-y-1">
                            <p className="text-xs font-medium text-muted-foreground">Your submission</p>
                            <p className="text-sm rounded bg-muted px-3 py-2">{mySubmission.content}</p>
                            <Badge variant="secondary" className="text-xs">{mySubmission.status}</Badge>
                          </div>
                        ) : (
                          <div className="space-y-2">
                            {!solForm?.open ? (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() =>
                                  setSolutionForms((prev) => ({
                                    ...prev,
                                    [task.task_id]: { open: true, content: "", error: null },
                                  }))
                                }
                              >
                                Submit Solution
                              </Button>
                            ) : (
                              <div className="space-y-2">
                                <textarea
                                  placeholder="Write your solution…"
                                  value={solForm.content}
                                  onChange={(e) =>
                                    setSolutionForms((prev) => ({
                                      ...prev,
                                      [task.task_id]: { ...prev[task.task_id], content: e.target.value },
                                    }))
                                  }
                                  rows={4}
                                  className="w-full rounded border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring resize-none"
                                />
                                {solForm.error && (
                                  <p className="text-destructive text-xs">{solForm.error}</p>
                                )}
                                <div className="flex gap-2">
                                  <Button
                                    size="sm"
                                    onClick={() => handleSubmitSolution(task.task_id)}
                                    disabled={submitSolution.isPending}
                                  >
                                    {submitSolution.isPending ? "Submitting…" : "Submit"}
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() =>
                                      setSolutionForms((prev) => ({
                                        ...prev,
                                        [task.task_id]: { open: false, content: "", error: null },
                                      }))
                                    }
                                  >
                                    Cancel
                                  </Button>
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    {/* F2: Peer Reviews — submissions from other learners */}
                    {otherSubmissions.length > 0 && (
                      <div className="space-y-3">
                        <Separator />
                        <p className="text-xs font-medium text-muted-foreground">
                          Peer submissions ({otherSubmissions.length})
                        </p>
                        {otherSubmissions.map((sub) => {
                          const revForm = reviewForms[sub.submission_id]
                          return (
                            <div
                              key={sub.submission_id}
                              className="rounded border border-border px-3 py-3 space-y-2"
                            >
                              <div className="flex items-start justify-between gap-2">
                                <div className="space-y-1 flex-1 min-w-0">
                                  <p className="font-mono text-xs text-muted-foreground truncate">
                                    {sub.learner_id}
                                  </p>
                                  <p className="text-sm">{sub.content}</p>
                                </div>
                                {task.status === "active" && (
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    className="flex-shrink-0 text-xs h-7"
                                    onClick={() => {
                                      if (revForm?.open) {
                                        setReviewForms((prev) => ({
                                          ...prev,
                                          [sub.submission_id]: {
                                            open: false,
                                            scores: defaultScores(),
                                            feedback: "",
                                            error: null,
                                          },
                                        }))
                                      } else {
                                        setReviewForms((prev) => ({
                                          ...prev,
                                          [sub.submission_id]: {
                                            open: true,
                                            scores: prev[sub.submission_id]?.scores ?? defaultScores(),
                                            feedback: prev[sub.submission_id]?.feedback ?? "",
                                            error: null,
                                          },
                                        }))
                                      }
                                    }}
                                  >
                                    {revForm?.open ? "Cancel" : "Write Review"}
                                  </Button>
                                )}
                              </div>

                              {/* Inline review form */}
                              {revForm?.open && (
                                <div className="space-y-3 pt-2 border-t border-border">
                                  {REVIEW_CRITERIA.map((criterion) => (
                                    <div key={criterion} className="space-y-1">
                                      <label className="text-xs font-medium capitalize">
                                        {criterion}
                                      </label>
                                      <div className="flex gap-2 items-center">
                                        <input
                                          type="number"
                                          min={1}
                                          max={5}
                                          value={revForm.scores[criterion]?.score ?? 3}
                                          onChange={(e) => {
                                            const val = Math.min(5, Math.max(1, Number(e.target.value)))
                                            setReviewForms((prev) => ({
                                              ...prev,
                                              [sub.submission_id]: {
                                                ...prev[sub.submission_id],
                                                scores: {
                                                  ...prev[sub.submission_id].scores,
                                                  [criterion]: {
                                                    ...prev[sub.submission_id].scores[criterion],
                                                    score: val,
                                                  },
                                                },
                                              },
                                            }))
                                          }}
                                          className="w-16 rounded border border-input bg-background px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                                        />
                                        <span className="text-xs text-muted-foreground">/ 5</span>
                                        <input
                                          type="text"
                                          placeholder="Comment (optional)"
                                          value={revForm.scores[criterion]?.comment ?? ""}
                                          onChange={(e) => {
                                            setReviewForms((prev) => ({
                                              ...prev,
                                              [sub.submission_id]: {
                                                ...prev[sub.submission_id],
                                                scores: {
                                                  ...prev[sub.submission_id].scores,
                                                  [criterion]: {
                                                    ...prev[sub.submission_id].scores[criterion],
                                                    comment: e.target.value,
                                                  },
                                                },
                                              },
                                            }))
                                          }}
                                          className="flex-1 rounded border border-input bg-background px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                                        />
                                      </div>
                                    </div>
                                  ))}
                                  <div className="space-y-1">
                                    <label className="text-xs font-medium">Overall feedback</label>
                                    <textarea
                                      placeholder="Overall feedback (optional)"
                                      value={revForm.feedback}
                                      onChange={(e) =>
                                        setReviewForms((prev) => ({
                                          ...prev,
                                          [sub.submission_id]: {
                                            ...prev[sub.submission_id],
                                            feedback: e.target.value,
                                          },
                                        }))
                                      }
                                      rows={3}
                                      className="w-full rounded border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring resize-none"
                                    />
                                  </div>
                                  {revForm.error && (
                                    <p className="text-destructive text-xs">{revForm.error}</p>
                                  )}
                                  <Button
                                    size="sm"
                                    onClick={() => handleSubmitReview(task.task_id, sub.submission_id)}
                                    disabled={submitReview.isPending}
                                  >
                                    {submitReview.isPending ? "Submitting…" : "Submit Review"}
                                  </Button>
                                </div>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    )}

                    {/* Submission count footer */}
                    <p className="text-xs text-muted-foreground">
                      {task.submissions.length} submission
                      {task.submissions.length !== 1 ? "s" : ""} total
                    </p>
                  </CardContent>
                </Card>
              )
            })
          )}
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Tab: Progression                                                     */}
      {/* ------------------------------------------------------------------ */}
      {activeTab === "progression" && (
        <div className="space-y-6">
          <div>
            <h2 className="font-semibold mb-3">Topic Experts</h2>
            {!topicExperts || topicExperts.length === 0 ? (
              <p className="text-muted-foreground text-sm">No topic experts yet.</p>
            ) : (
              <div className="space-y-2">
                {topicExperts.map((e) => (
                  <div
                    key={e.expert_id}
                    className="flex items-center justify-between rounded border border-border px-3 py-2 text-sm"
                  >
                    <span className="font-mono text-xs">{e.learner_id}</span>
                    <Badge variant="secondary">{e.topic_id}</Badge>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div>
            <h2 className="font-semibold mb-3">Helper Metrics</h2>
            {!helperMetrics || helperMetrics.length === 0 ? (
              <p className="text-muted-foreground text-sm">No metrics recorded yet.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-xs text-muted-foreground">
                      <th className="pb-2 pr-4">Learner</th>
                      <th className="pb-2 pr-4">Helped</th>
                      <th className="pb-2 pr-4">Answers</th>
                      <th className="pb-2 pr-4">Reviews</th>
                      <th className="pb-2">Avg Satisfaction</th>
                    </tr>
                  </thead>
                  <tbody>
                    {helperMetrics.map((m) => (
                      <tr key={m.learner_id} className="border-b border-border">
                        <td className="py-2 pr-4 font-mono text-xs">{m.learner_id}</td>
                        <td className="py-2 pr-4">{m.learners_helped}</td>
                        <td className="py-2 pr-4">{m.questions_answered}</td>
                        <td className="py-2 pr-4">{m.tasks_reviewed}</td>
                        <td className="py-2">
                          {m.average_satisfaction != null
                            ? Number(m.average_satisfaction).toFixed(2)
                            : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Tab: Leaderboard                                                     */}
      {/* ------------------------------------------------------------------ */}
      {activeTab === "leaderboard" && (
        <div>
          {!leaderboard || leaderboard.length === 0 ? (
            <p className="text-muted-foreground text-sm">
              No leaderboard data yet. Complete tasks to earn XP.
            </p>
          ) : (
            <div className="space-y-2">
              {leaderboard.map((entry) => (
                <div
                  key={entry.learner_id}
                  className={`flex items-center gap-4 rounded border border-border px-4 py-3 text-sm ${
                    entry.learner_id === userId ? "bg-muted" : ""
                  }`}
                >
                  <span className="w-6 text-center font-bold text-muted-foreground">
                    {entry.rank}
                  </span>
                  <span className="flex-1 font-mono text-xs">{entry.learner_id}</span>
                  <span className="font-semibold">{entry.total_xp} XP</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
