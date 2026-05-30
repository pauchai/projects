/**
 * Cohort workspace — Overview tab.
 * Members list + enrol form (master only, during forming).
 * Ported from the "overview" tab of cohort-detail.tsx.
 */

import { useState } from "react"
import { useParams } from "react-router-dom"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { useAuthStore } from "@/stores/auth-store"
import {
  useCohort,
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

export function CohortOverviewPage() {
  const { cohortId } = useParams<{ cohortId: string }>()
  const userId = useAuthStore((s) => s.userId)
  const [actionError, setActionError] = useState<string | null>(null)
  const [enrolId, setEnrolId] = useState("")

  const { data: cohort, isLoading, isError } = useCohort(cohortId ?? "")
  const activateCohort = useActivateCohort()
  const beginCompleting = useBeginCompletingCohort()
  const graduateCohort = useGraduateCohort()
  const cancelCohort = useCancelCohort()
  const enrolLearner = useEnrolLearner()
  const removeLearner = useRemoveLearner()

  if (isLoading) return <p className="text-muted-foreground">Loading cohort…</p>
  if (isError || !cohort) return <p className="text-destructive">Cohort not found.</p>

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

      {/* Members */}
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

      {/* Enrol form */}
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
  )
}
