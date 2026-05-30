/**
 * Cohort workspace layout.
 *
 * Tabs: Overview | Tasks | Progression | Leaderboard | Dashboard (master only)
 */

import { NavLink, Outlet, useParams, Navigate } from "react-router-dom"
import { useCohort } from "@/hooks/use-cohorts"
import { useAuthStore } from "@/stores/auth-store"

interface TabDef {
  to: string
  label: string
  masterOnly?: boolean
}

function buildTabs(projectId: string, moduleId: string, cohortId: string): TabDef[] {
  const base = `/projects/${projectId}/modules/${moduleId}/cohorts/${cohortId}`
  return [
    { to: `${base}/overview`, label: "Overview" },
    { to: `${base}/tasks`, label: "Tasks" },
    { to: `${base}/progression`, label: "Progression" },
    { to: `${base}/leaderboard`, label: "Leaderboard" },
    { to: `${base}/dashboard`, label: "Dashboard", masterOnly: true },
  ]
}

export function CohortLayout() {
  const { projectId, moduleId, cohortId } = useParams<{
    projectId: string
    moduleId: string
    cohortId: string
  }>()
  const { data: cohort } = useCohort(cohortId ?? "")
  const userId = useAuthStore((s) => s.userId)

  if (!projectId || !moduleId || !cohortId) {
    return <Navigate to="/projects" replace />
  }

  const isMaster = !!cohort && cohort.master_id === userId
  const tabs = buildTabs(projectId, moduleId, cohortId).filter((t) => !t.masterOnly || isMaster)

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
