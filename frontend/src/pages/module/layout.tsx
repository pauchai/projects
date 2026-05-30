/**
 * Module workspace layout.
 *
 * Tabs: Overview | Topics | Cohorts | Settings
 * Settings visible to module master only.
 */

import { NavLink, Outlet, useParams, Navigate } from "react-router-dom"
import { useModule } from "@/hooks/use-modules"
import { useAuthStore } from "@/stores/auth-store"

interface TabDef {
  to: string
  label: string
  masterOnly?: boolean
}

function buildTabs(projectId: string, moduleId: string): TabDef[] {
  const base = `/projects/${projectId}/modules/${moduleId}`
  return [
    { to: `${base}/overview`, label: "Overview" },
    { to: `${base}/topics`, label: "Topics" },
    { to: `${base}/cohorts`, label: "Cohorts" },
    { to: `${base}/lessons`, label: "Lessons" },
    { to: `${base}/settings`, label: "Settings", masterOnly: true },
  ]
}

export function ModuleLayout() {
  const { projectId, moduleId } = useParams<{ projectId: string; moduleId: string }>()
  const { data: module } = useModule(moduleId ?? "")
  const userId = useAuthStore((s) => s.userId)

  if (!projectId || !moduleId) {
    return <Navigate to="/projects" replace />
  }

  const isMaster = !!module && module.master_id === userId
  const tabs = buildTabs(projectId, moduleId).filter((t) => !t.masterOnly || isMaster)

  return (
    <div className="space-y-0">
      <div className="border-b">
        <nav className="-mb-px flex gap-1 overflow-x-auto">
          {tabs.map((tab) => (
            <NavLink
              key={tab.to}
              to={tab.to}
              className={({ isActive }) =>
                [
                  "whitespace-nowrap border-b-2 px-4 py-3 text-sm font-medium transition-colors",
                  isActive
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground",
                ].join(" ")
              }
            >
              {tab.label}
            </NavLink>
          ))}
        </nav>
      </div>
      <div className="pt-6">
        <Outlet />
      </div>
    </div>
  )
}
