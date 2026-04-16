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
} from "@/hooks/use-cohorts"
import { ApiError } from "@/api/client"
import type { CohortStatus } from "@/api/types"

const STATUS_VARIANT: Record<CohortStatus, "default" | "secondary" | "outline" | "destructive"> = {
  forming: "secondary",
  active: "default",
  completing: "outline",
  graduated: "secondary",
  cancelled: "destructive",
}

type Tab = "overview" | "tasks" | "progression" | "leaderboard"

export function CohortDetailPage() {
  const { cohortId } = useParams<{ cohortId: string }>()
  const userId = useAuthStore((s) => s.userId)
  const [activeTab, setActiveTab] = useState<Tab>("overview")
  const [actionError, setActionError] = useState<string | null>(null)
  const [enrolId, setEnrolId] = useState("")

  const { data: cohort, isLoading, isError, error } = useCohort(cohortId ?? "")
  const { data: tasks } = useCohortTasks(cohortId ?? "")
  const { data: leaderboard } = useCohortLeaderboard(cohortId ?? "")
  const { data: helperMetrics } = useCohortHelperMetrics(cohortId ?? "")
  const { data: topicExperts } = useCohortTopicExperts(cohortId ?? "")

  const activateCohort = useActivateCohort()
  const beginCompleting = useBeginCompletingCohort()
  const graduateCohort = useGraduateCohort()
  const cancelCohort = useCancelCohort()
  const enrolLearner = useEnrolLearner()
  const removeLearner = useRemoveLearner()

  if (isLoading) {
    return <p className="text-muted-foreground">Loading cohort...</p>
  }

  if (isError) {
    return (
      <p className="text-destructive">
        Failed to load cohort: {error instanceof Error ? error.message : "Unknown error"}
      </p>
    )
  }

  if (!cohort) return null

  const isMaster = cohort.master_id === userId
  const activeMembers = cohort.memberships.filter((m) => m.is_active)

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

      {/* Tab: Overview */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          <div>
            <h2 className="font-semibold mb-3">
              Members ({activeMembers.length})
            </h2>
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

          {/* Enrol form (master + forming status) */}
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

      {/* Tab: Tasks */}
      {activeTab === "tasks" && (
        <div className="space-y-4">
          {!tasks || tasks.length === 0 ? (
            <p className="text-muted-foreground text-sm">No practice tasks yet.</p>
          ) : (
            tasks.map((task) => (
              <Card key={task.task_id}>
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <CardTitle className="text-sm">{task.title}</CardTitle>
                    <Badge variant="outline">{task.status}</Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">Topic: {task.topic_id}</p>
                </CardHeader>
                <CardContent className="text-sm space-y-1">
                  {task.description && (
                    <p className="text-muted-foreground">{task.description}</p>
                  )}
                  <p className="text-xs text-muted-foreground">
                    {task.submissions.length} submission{task.submissions.length !== 1 ? "s" : ""}
                  </p>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      )}

      {/* Tab: Progression */}
      {activeTab === "progression" && (
        <div className="space-y-6">
          {/* Topic Experts */}
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

          {/* Helper metrics */}
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

      {/* Tab: Leaderboard */}
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
