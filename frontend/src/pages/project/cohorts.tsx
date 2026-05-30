import { Link, useParams } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useMyCohorts } from "@/hooks/use-cohorts"
import { useAuthStore } from "@/stores/auth-store"
import type { CohortStatus } from "@/api/types"

const STATUS_VARIANT: Record<CohortStatus, "default" | "secondary" | "outline" | "destructive"> = {
  forming: "secondary",
  active: "default",
  completing: "outline",
  graduated: "secondary",
  cancelled: "destructive",
}

export function ProjectCohortsPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const { userId, isAuthenticated } = useAuthStore()
  const { data: cohorts, isLoading, isError, error } = useMyCohorts()

  if (isLoading) {
    return <p className="text-muted-foreground">Loading cohorts...</p>
  }

  if (isError) {
    return (
      <p className="text-destructive">
        Failed to load cohorts: {error instanceof Error ? error.message : "Unknown error"}
      </p>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Cohorts</h1>
        {isAuthenticated && (
          <Link to={`/projects/${projectId}/cohorts/new`}>
            <Button size="sm">New Cohort</Button>
          </Link>
        )}
      </div>

      {cohorts && cohorts.length === 0 && (
        <p className="text-muted-foreground">No cohorts yet.</p>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        {cohorts?.map((cohort) => {
          const isMaster = cohort.master_id === userId
          const activeCount = cohort.memberships.filter((m) => m.is_active).length

          return (
            <Card key={cohort.cohort_id} className="flex flex-col">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-base leading-tight truncate">
                    {cohort.cohort_id}
                  </CardTitle>
                  <Badge variant={STATUS_VARIANT[cohort.status]} className="shrink-0">
                    {cohort.status}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground">
                  Module: {cohort.module_id}
                </p>
              </CardHeader>
              <CardContent className="flex-1 space-y-3">
                <div className="flex gap-4 text-sm text-muted-foreground">
                  <span>{activeCount} member{activeCount !== 1 ? "s" : ""}</span>
                  {isMaster && (
                    <span className="font-medium text-foreground">You are master</span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">
                  Formed {new Date(cohort.formed_at).toLocaleDateString()}
                </p>
                <div className="flex gap-2 pt-1">
                  <Link to={`/cohorts/${cohort.cohort_id}`} className="flex-1">
                    <Button variant="outline" size="sm" className="w-full">View</Button>
                  </Link>
                  {isMaster && (
                    <Link to={`/cohorts/${cohort.cohort_id}/dashboard`} className="flex-1">
                      <Button size="sm" className="w-full">Dashboard</Button>
                    </Link>
                  )}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
