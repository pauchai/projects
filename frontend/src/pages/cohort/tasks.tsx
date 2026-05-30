/**
 * Cohort workspace — Tasks tab.
 * Task list + create task form (master/curator).
 * Submit solution + peer reviews.
 * Ported from the "tasks" tab of cohort-detail.tsx.
 */

import { useState } from "react"
import { useParams } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { useAuthStore } from "@/stores/auth-store"
import {
  useCohort,
  useCohortTasks,
  useCreateTask,
  useActivateTask,
  useCloseTask,
  useSubmitSolution,
  useSubmitReview,
} from "@/hooks/use-cohorts"
import { useModule } from "@/hooks/use-modules"
import { ApiError } from "@/api/client"

const REVIEW_CRITERIA = ["correctness", "clarity", "completeness"] as const

type ScoreMap = Record<string, { score: number; comment: string }>

function defaultScores(): ScoreMap {
  return Object.fromEntries(REVIEW_CRITERIA.map((c) => [c, { score: 3, comment: "" }]))
}

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

export function CohortTasksPage() {
  const { cohortId } = useParams<{ cohortId: string }>()
  const userId = useAuthStore((s) => s.userId)
  const [actionError, setActionError] = useState<string | null>(null)

  const [solutionForms, setSolutionForms] = useState<Record<string, SolutionFormState>>({})
  const [reviewForms, setReviewForms] = useState<Record<string, ReviewFormState>>({})
  const [createTaskForm, setCreateTaskForm] = useState<CreateTaskFormState>({
    open: false,
    title: "",
    topicId: "",
    description: "",
    error: null,
  })

  const { data: cohort, isLoading: cohortLoading } = useCohort(cohortId ?? "")
  const { data: tasks } = useCohortTasks(cohortId ?? "")
  const { data: module } = useModule(cohort?.module_id ?? "")

  const createTask = useCreateTask()
  const activateTask = useActivateTask()
  const closeTask = useCloseTask()
  const submitSolution = useSubmitSolution()
  const submitReview = useSubmitReview()

  if (cohortLoading) return <p className="text-muted-foreground">Loading cohort…</p>
  if (!cohort) return <p className="text-destructive">Cohort not found.</p>

  const isMaster = cohort.master_id === userId
  const myMembership = cohort.memberships.find((m) => m.learner_id === userId && m.is_active)
  const canManageTasks = isMaster || myMembership?.role === "curator"

  const handleAction = async (fn: () => Promise<unknown>) => {
    setActionError(null)
    try {
      await fn()
    } catch (e) {
      setActionError(e instanceof ApiError ? e.detail : "Action failed")
    }
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
      setReviewForms((prev) => ({
        ...prev,
        [submissionId]: { open: false, scores: defaultScores(), feedback: "", error: null },
      }))
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

  return (
    <div className="space-y-4">
      {actionError && <p className="text-destructive text-sm">{actionError}</p>}

      {/* Create task form (master/curator only) */}
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

                {/* Submit Solution */}
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

                {/* Peer Reviews */}
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
                                onClick={() =>
                                  handleSubmitReview(task.task_id, sub.submission_id)
                                }
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
  )
}
