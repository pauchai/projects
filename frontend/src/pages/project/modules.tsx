import { Link, useParams } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useModules } from "@/hooks/use-modules"
import { useAuthStore } from "@/stores/auth-store"

export function ProjectModulesPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const { isAuthenticated } = useAuthStore()
  const { data: modules, isLoading, isError } = useModules()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Modules</h1>
        {isAuthenticated && (
          <Link to={`/projects/${projectId}/modules/new`}>
            <Button size="sm">New Module</Button>
          </Link>
        )}
      </div>

      {isLoading && <p className="text-muted-foreground">Loading modules…</p>}
      {isError && <p className="text-destructive">Failed to load modules.</p>}

      {modules && modules.length === 0 && (
        <p className="text-muted-foreground">No modules yet.</p>
      )}

      {modules && modules.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {modules.map((module) => (
            <Card key={module.module_id}>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">{module.title}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <span>Master:</span>
                  <span className="font-mono truncate">{module.master_id}</span>
                </div>
                <Badge variant="secondary">
                  {module.topic_count} topic{module.topic_count !== 1 ? "s" : ""}
                </Badge>
                <Link to={`/projects/${projectId}/modules/${module.module_id}/overview`} className="block">
                  <Button size="sm" variant="outline" className="w-full">View</Button>
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
