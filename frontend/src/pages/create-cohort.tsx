import { useState } from "react"
import { useNavigate, Link } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { useFormCohort } from "@/hooks/use-cohorts"
import { useModules } from "@/hooks/use-modules"
import { ApiError } from "@/api/client"

export function CreateCohortPage() {
  const navigate = useNavigate()
  const formCohort = useFormCohort()
  const { data: modules, isLoading: modulesLoading } = useModules()

  const [cohortId, setCohortId] = useState<string>(() => crypto.randomUUID())
  const [moduleId, setModuleId] = useState("")
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (!moduleId) {
      setError("Please select a module.")
      return
    }
    try {
      await formCohort.mutateAsync({ cohort_id: cohortId, module_id: moduleId })
      navigate(`/cohorts/${cohortId}`)
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
              <Label htmlFor="moduleId">Module</Label>
              {modulesLoading && (
                <p className="text-sm text-muted-foreground">Loading modules…</p>
              )}
              {!modulesLoading && (!modules || modules.length === 0) && (
                <p className="text-sm text-muted-foreground">
                  No modules available.{" "}
                  <Link to="/modules/new" className="underline">
                    Create one first
                  </Link>
                  .
                </p>
              )}
              {!modulesLoading && modules && modules.length > 0 && (
                <select
                  id="moduleId"
                  value={moduleId}
                  onChange={(e) => setModuleId(e.target.value)}
                  className="w-full border rounded-md px-3 py-2 text-sm bg-background"
                  required
                >
                  <option value="">Select a module…</option>
                  {modules.map((m) => (
                    <option key={m.module_id} value={m.module_id}>
                      {m.title} ({m.topic_count} topic{m.topic_count !== 1 ? "s" : ""})
                    </option>
                  ))}
                </select>
              )}
            </div>

            {error && <p className="text-destructive text-sm">{error}</p>}

            <div className="flex gap-3 pt-2">
              <Button
                type="submit"
                disabled={formCohort.isPending || !moduleId}
              >
                {formCohort.isPending ? "Creating…" : "Create Cohort"}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate("/cohorts")}
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
