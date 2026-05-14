/**
 * Module workspace — Settings tab.
 * Visible to module master only (enforced by layout).
 */

import { useParams } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useModule } from "@/hooks/use-modules"

export function ModuleSettingsPage() {
  const { moduleId } = useParams<{ moduleId: string }>()
  const { data: module, isLoading, isError } = useModule(moduleId ?? "")

  if (isLoading) return <p className="text-muted-foreground">Loading…</p>
  if (isError || !module) return <p className="text-destructive">Module not found.</p>

  return (
    <div className="space-y-6 max-w-2xl">
      <h2 className="text-xl font-bold">Module Settings</h2>
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Info</CardTitle>
        </CardHeader>
        <CardContent className="text-sm space-y-2">
          <div>
            <span className="text-muted-foreground">Module ID: </span>
            <span className="font-mono text-xs">{module.module_id}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Title: </span>
            <span>{module.title}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Master: </span>
            <span className="font-mono text-xs">{module.master_id}</span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
