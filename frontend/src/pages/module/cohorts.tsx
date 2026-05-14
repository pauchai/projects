/**
 * Module workspace — Cohorts tab.
 * Lists cohorts belonging to this module.
 * Authenticated users can create a new cohort.
 */

import { Link, useParams } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useAuthStore } from "@/stores/auth-store"
import { useMyCohorts } from "@/hooks/use-cohorts"

export function ModuleCohortsPage() {
  const { projectId, moduleId } = useParams<{ projectId: string; moduleId: string }>()
  const { isAuthenticated } = useAuthStore()
  const { data: allCohorts, isLoading, isError } = useMyCohorts()

  // Filter to cohorts belonging to this module
  const cohorts = allCohorts?.filter((c) => c.module_id === moduleId) ?? []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Cohorts</h2>
        {isAuthenticated && (
          <Link to={`/projects/${projectId}/modules/${moduleId}/cohorts/new`}>
            <Button size="sm">New Cohort</Button>
          </Link>
        )}
      </div>

      {isLoading && <p className="text-muted-foreground">Loading cohorts…</p>}
      {isError && <p className="text-destructive">Failed to load cohorts.</p>}

      {!isLoading && cohorts.length === 0 && (
        <p className="text-muted-foreground">No cohorts yet for this module.</p>
      )}

      {cohorts.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {cohorts.map((cohort) => (
            <Card key={cohort.cohort_id}>
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-mono text-sm">
                  {cohort.cohort_id}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Badge variant="secondary">{cohort.status}</Badge>
                <Link
                  to={`/projects/${projectId}/modules/${moduleId}/cohorts/${cohort.cohort_id}/overview`}
                  className="block"
                >
                  <Button size="sm" variant="outline" className="w-full">
                    Open
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
