import { useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { useFormCohort } from "@/hooks/use-cohorts"
import { ApiError } from "@/api/client"

export function CreateCohortPage() {
  const navigate = useNavigate()
  const { projectId, moduleId } = useParams<{ projectId: string; moduleId: string }>()
  const formCohort = useFormCohort()

  const [cohortId, setCohortId] = useState<string>(() => crypto.randomUUID())
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (!moduleId) {
      setError("Module context is missing.")
      return
    }
    try {
      await formCohort.mutateAsync({ cohort_id: cohortId, module_id: moduleId })
      navigate(
        `/projects/${projectId}/modules/${moduleId}/cohorts/${cohortId}/overview`,
      )
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to create cohort.")
    }
  }

  return (
    <div className="max-w-md">
      <h1 className="text-2xl font-bold mb-6">Create a Cohort</h1>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">New Learning Cohort</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1">
              <Label htmlFor="cohortId">Cohort ID</Label>
              <Input
                id="cohortId"
                value={cohortId}
                readOnly
                className="font-mono text-sm bg-muted"
              />
              <p className="text-xs text-muted-foreground">
                Auto-generated.{" "}
                <button
                  type="button"
                  className="underline"
                  onClick={() => setCohortId(crypto.randomUUID())}
                >
                  Regenerate
                </button>
              </p>
            </div>

            <div className="space-y-1">
              <Label>Module</Label>
              <p className="text-sm font-mono text-muted-foreground">{moduleId}</p>
            </div>

            {error && <p className="text-destructive text-sm">{error}</p>}

            <div className="flex gap-3 pt-2">
              <Button type="submit" disabled={formCohort.isPending}>
                {formCohort.isPending ? "Creating…" : "Create Cohort"}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() =>
                  navigate(
                    `/projects/${projectId}/modules/${moduleId}/cohorts`,
                  )
                }
              >
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
