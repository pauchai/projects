import { useParams, Link } from "react-router-dom"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { useState } from "react"
import { useAuthStore } from "@/stores/auth-store"
import {
  useCohort,
  usePendingValidations,
  usePendingPromotions,
  useValidateCompetency,
  usePromoteExpert,
  usePromoteCurator,
} from "@/hooks/use-cohorts"
import { ApiError } from "@/api/client"

interface ValidationFormState {
  score: number
  approved: boolean
}

export function CohortDashboardPage() {
  const { cohortId } = useParams<{ cohortId: string }>()
  const userId = useAuthStore((s) => s.userId)
  const [actionError, setActionError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  // per-row validation form state: pending_id → { score, approved }
  const [validationForms, setValidationForms] = useState<Record<string, ValidationFormState>>({})

  const getValidationForm = (pendingId: string): ValidationFormState =>
    validationForms[pendingId] ?? { score: 0, approved: false }

  const setValidationField = (
    pendingId: string,
    field: keyof ValidationFormState,
    value: number | boolean,
  ) => {
    setValidationForms((prev) => ({
      ...prev,
      [pendingId]: { ...getValidationForm(pendingId), [field]: value },
    }))
  }

  const { data: cohort, isLoading: cohortLoading } = useCohort(cohortId ?? "")
  const {
    data: pendingValidations,
    isLoading: validationsLoading,
    isError: validationsError,
  } = usePendingValidations(cohortId ?? "")
  const {
    data: pendingPromotions,
    isLoading: promotionsLoading,
    isError: promotionsError,
  } = usePendingPromotions(cohortId ?? "")

  const validateCompetency = useValidateCompetency()
  const promoteExpert = usePromoteExpert()
  const promoteCurator = usePromoteCurator()

  if (cohortLoading) {
    return <p className="text-muted-foreground">Loading dashboard...</p>
  }

  if (!cohort) {
    return <p className="text-destructive">Cohort not found.</p>
  }

  const isMaster = cohort.master_id === userId
  if (!isMaster) {
    return (
      <p className="text-destructive">
        Only the cohort master can access this dashboard.
      </p>
    )
  }

  const handleAction = async (fn: () => Promise<unknown>, msg: string) => {
    setActionError(null)
    setSuccessMsg(null)
    try {
      await fn()
      setSuccessMsg(msg)
    } catch (e) {
      setActionError(e instanceof ApiError ? e.detail : "Action failed")
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Cohort Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {cohort.cohort_id} &nbsp;·&nbsp;
            <Badge variant="outline" className="text-xs">
              {cohort.status}
            </Badge>
          </p>
        </div>
        <Link to={`/cohorts/${cohort.cohort_id}`}>
          <Button variant="outline" size="sm">Back to Cohort</Button>
        </Link>
      </div>

      {actionError && <p className="text-destructive text-sm">{actionError}</p>}
      {successMsg && <p className="text-sm text-green-600 dark:text-green-400">{successMsg}</p>}

      {/* Pending Competency Validations */}
      <section>
        <h2 className="text-lg font-semibold mb-3">
          Pending Competency Validations
        </h2>
        {validationsLoading && (
          <p className="text-muted-foreground text-sm">Loading...</p>
        )}
        {validationsError && (
          <p className="text-destructive text-sm">Failed to load validations.</p>
        )}
        {pendingValidations && pendingValidations.length === 0 && (
          <p className="text-muted-foreground text-sm">No pending validations.</p>
        )}
        <div className="space-y-3">
        {pendingValidations?.map((pv) => {
            const form = getValidationForm(pv.pending_id)
            const isScoreValid = form.score >= 0 && form.score <= 100
            return (
            <Card key={pv.pending_id}>
              <CardContent className="pt-4 pb-4 space-y-3">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="space-y-1">
                    <p className="text-sm">
                      <span className="text-muted-foreground">Learner: </span>
                      <span className="font-mono text-xs">{pv.learner_id}</span>
                    </p>
                    <p className="text-sm">
                      <span className="text-muted-foreground">Topic: </span>
                      <span>{pv.topic_id}</span>
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Queued {new Date(pv.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                {/* Per-row validation form */}
                <div className="flex flex-wrap items-center gap-4">
                  <label className="flex flex-col gap-1">
                    <span className="text-xs text-muted-foreground">
                      Knowledge check score (0–100)
                    </span>
                    <input
                      type="number"
                      min={0}
                      max={100}
                      value={form.score}
                      onChange={(e) =>
                        setValidationField(pv.pending_id, "score", Number(e.target.value))
                      }
                      className="w-24 rounded border border-input bg-background px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
                    />
                  </label>
                  <label className="flex items-center gap-2 text-sm cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={form.approved}
                      onChange={(e) =>
                        setValidationField(pv.pending_id, "approved", e.target.checked)
                      }
                      className="h-4 w-4 rounded border-input accent-primary"
                    />
                    Mentor approved
                  </label>
                </div>

                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    disabled={validateCompetency.isPending || !isScoreValid}
                    onClick={() =>
                      handleAction(
                        () =>
                          validateCompetency.mutateAsync({
                            cohortId: cohort.cohort_id,
                            learnerId: pv.learner_id,
                            data: {
                              topic_id: pv.topic_id,
                              knowledge_check_score: form.score,
                              mentor_approved: form.approved,
                            },
                          }),
                        "Competency validated",
                      )
                    }
                  >
                    Validate
                  </Button>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() =>
                      handleAction(
                        () =>
                          promoteExpert.mutateAsync({
                            cohortId: cohort.cohort_id,
                            learnerId: pv.learner_id,
                            data: {
                              expert_id: crypto.randomUUID(),
                              topic_id: pv.topic_id,
                            },
                          }),
                        "Promoted to topic expert",
                      )
                    }
                    disabled={promoteExpert.isPending}
                  >
                    Promote Expert
                  </Button>
                </div>
              </CardContent>
            </Card>
            )
          })}
        </div>
      </section>

      <Separator />

      {/* Pending Curator Promotions */}
      <section>
        <h2 className="text-lg font-semibold mb-3">
          Pending Curator Promotions
        </h2>
        {promotionsLoading && (
          <p className="text-muted-foreground text-sm">Loading...</p>
        )}
        {promotionsError && (
          <p className="text-destructive text-sm">Failed to load promotions.</p>
        )}
        {pendingPromotions && pendingPromotions.length === 0 && (
          <p className="text-muted-foreground text-sm">No pending curator promotions.</p>
        )}
        <div className="space-y-3">
          {pendingPromotions?.map((pp) => (
            <Card key={pp.pending_id}>
              <CardContent className="pt-4 pb-4 flex flex-wrap items-center justify-between gap-3">
                <div className="space-y-1">
                  <p className="text-sm">
                    <span className="text-muted-foreground">Learner: </span>
                    <span className="font-mono text-xs">{pp.learner_id}</span>
                  </p>
                  <p className="text-sm">
                    <span className="text-muted-foreground">Module: </span>
                    <span>{pp.module_id}</span>
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Queued {new Date(pp.created_at).toLocaleDateString()}
                  </p>
                </div>
                <Button
                  size="sm"
                  onClick={() =>
                    handleAction(
                      () =>
                        promoteCurator.mutateAsync({
                          cohortId: cohort.cohort_id,
                          learnerId: pp.learner_id,
                          data: {
                            curator_id: crypto.randomUUID(),
                            module_id: pp.module_id,
                          },
                        }),
                      "Promoted to module curator",
                    )
                  }
                  disabled={promoteCurator.isPending}
                >
                  Promote Curator
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </div>
  )
}
