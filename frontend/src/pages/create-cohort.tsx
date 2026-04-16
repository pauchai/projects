import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { useFormCohort } from "@/hooks/use-cohorts"
import { ApiError } from "@/api/client"

export function CreateCohortPage() {
  const navigate = useNavigate()
  const formCohort = useFormCohort()
  const [cohortId, setCohortId] = useState<string>(() => crypto.randomUUID())
  const [moduleId, setModuleId] = useState("")
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (!moduleId.trim()) {
      setError("Module ID is required.")
      return
    }
    try {
      await formCohort.mutateAsync({ cohort_id: cohortId, module_id: moduleId.trim() })
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
                onChange={(e) => setCohortId(e.target.value)}
                placeholder="UUID or custom identifier"
              />
              <p className="text-xs text-muted-foreground">
                Must be unique.{" "}
                <button
                  type="button"
                  className="underline"
                  onClick={() => setCohortId(crypto.randomUUID())}
                >
                  Generate new
                </button>
              </p>
            </div>

            <div className="space-y-1">
              <Label htmlFor="moduleId">Module ID</Label>
              <Input
                id="moduleId"
                value={moduleId}
                onChange={(e) => setModuleId(e.target.value)}
                placeholder="The module this cohort will study"
                required
              />
            </div>

            {error && <p className="text-destructive text-sm">{error}</p>}

            <div className="flex gap-3 pt-2">
              <Button type="submit" disabled={formCohort.isPending}>
                {formCohort.isPending ? "Creating..." : "Create Cohort"}
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
