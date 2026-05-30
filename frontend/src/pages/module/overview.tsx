/**
 * Module workspace — Overview tab.
 * Shows module metadata (title, master, topic count).
 */

import { useParams } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useModule } from "@/hooks/use-modules"

export function ModuleOverviewPage() {
  const { moduleId } = useParams<{ moduleId: string }>()
  const { data: module, isLoading, isError } = useModule(moduleId ?? "")

  if (isLoading) return <p className="text-muted-foreground">Loading module…</p>
  if (isError || !module) return <p className="text-destructive">Module not found.</p>

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold">{module.title}</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Master: <span className="font-mono">{module.master_id}</span>
        </p>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Module Info</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">Module ID:</span>
            <span className="font-mono text-xs">{module.module_id}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">Topics:</span>
            <Badge variant="secondary">{module.topic_count}</Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
