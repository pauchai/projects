/**
 * Project workspace layout.
 *
 * Renders tabs: Overview | Products | Fund | Tasks | Partners | Docs | Courses | Features | Modules | Cohorts
 * Settings tab is visible only to owners/admins.
 * All tabs except Settings are public.
 */

import { NavLink, Outlet, useParams, Navigate } from "react-router-dom"
import { useProject } from "@/hooks/use-projects"
import { useAuthStore } from "@/stores/auth-store"

interface TabDef {
  to: string
  label: string
  /** If true, only show when the current user is owner/admin */
  managerOnly?: boolean
}

function buildTabs(projectId: string): TabDef[] {
  return [
    { to: `/projects/${projectId}/overview`, label: "Overview" },
    { to: `/projects/${projectId}/products`, label: "Products" },
    { to: `/projects/${projectId}/fund`, label: "Fund" },
    { to: `/projects/${projectId}/tasks`, label: "Tasks" },
    { to: `/projects/${projectId}/partners`, label: "Partners" },
    { to: `/projects/${projectId}/docs`, label: "Docs" },
    { to: `/projects/${projectId}/courses`, label: "Courses" },
    { to: `/projects/${projectId}/features`, label: "Features" },
    { to: `/projects/${projectId}/modules`, label: "Modules" },
    { to: `/projects/${projectId}/cohorts`, label: "Cohorts" },
    { to: `/projects/${projectId}/settings`, label: "Settings", managerOnly: true },
  ]
}

export function ProjectLayout() {
  const { projectId } = useParams<{ projectId: string }>()
  const { data: project } = useProject(projectId ?? "")
  const userId = useAuthStore((s) => s.userId)

  if (!projectId) {
    return <Navigate to="/projects" replace />
  }

  const isManager =
    !!project &&
    project.memberships.some(
      (m) => m.user_id === userId && m.is_active && (m.role === "owner" || m.role === "admin"),
    )

  const tabs = buildTabs(projectId).filter((t) => !t.managerOnly || isManager)

  return (
    <div className="space-y-0">
      {/* Tab bar */}
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

      {/* Tab content */}
      <div className="pt-6">
        <Outlet />
      </div>
    </div>
  )
}
