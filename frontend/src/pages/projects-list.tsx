import { useState } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { ProjectCard } from "@/components/project-card"
import { useSearchProjects } from "@/hooks/use-projects"
import { useAuthStore } from "@/stores/auth-store"
import type { SearchProjectsParams } from "@/api/types"

const STATUS_OPTIONS = [
  { value: "", label: "All" },
  { value: "recruiting", label: "Recruiting" },
  { value: "active", label: "Active" },
  { value: "completed", label: "Completed" },
]

type Tab = "all" | "mine"

export function ProjectsListPage() {
  const { isAuthenticated, userId } = useAuthStore()
  const [tab, setTab] = useState<Tab>("all")

  const [keyword, setKeyword] = useState("")
  const [skills, setSkills] = useState("")
  const [status, setStatus] = useState("")

  const allParams: SearchProjectsParams = {
    ...(keyword.trim() ? { keyword: keyword.trim() } : {}),
    ...(skills.trim() ? { skills: skills.trim() } : {}),
    ...(status ? { status } : {}),
  }

  const myParams: SearchProjectsParams = {
    member_user_id: userId ?? undefined,
  }

  const { data: projects, isLoading, isError, error } = useSearchProjects(
    tab === "mine" ? myParams : allParams,
  )

  return (
    <div>
      <h1 className="text-2xl font-bold">Projects / Проекты</h1>
      <p className="mt-1 mb-6 text-sm text-muted-foreground">
        Explore collaborative initiatives open for new members. Find a project that matches your skills and interests, or start your own.
      </p>
      <p className="mb-6 text-sm text-muted-foreground">
        Исследуйте совместные инициативы, открытые для новых участников. Найдите проект под свои навыки и интересы или создайте свой.
      </p>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-border mb-6">
        <button
          onClick={() => setTab("all")}
          className={[
            "px-4 py-2 text-sm font-medium border-b-2 transition-colors",
            tab === "all"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground",
          ].join(" ")}
        >
          All
        </button>
        {isAuthenticated && (
          <button
            onClick={() => setTab("mine")}
            className={[
              "px-4 py-2 text-sm font-medium border-b-2 transition-colors",
              tab === "mine"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground",
            ].join(" ")}
          >
            My Projects
          </button>
        )}
      </div>

      {/* Search/filter — only on All tab */}
      {tab === "all" && (
        <div className="mb-6 flex flex-col gap-3 sm:flex-row">
          <Input
            placeholder="Search by keyword..."
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            className="sm:flex-1"
          />
          <Input
            placeholder="Filter by skills (comma-separated)"
            value={skills}
            onChange={(e) => setSkills(e.target.value)}
            className="sm:flex-1"
          />
          <div className="flex gap-2">
            {STATUS_OPTIONS.map((opt) => (
              <Button
                key={opt.value}
                variant={status === opt.value ? "default" : "outline"}
                size="sm"
                onClick={() => setStatus(opt.value)}
              >
                {opt.label}
              </Button>
            ))}
          </div>
        </div>
      )}

      {/* Results */}
      {isLoading && <p className="text-muted-foreground">Loading projects...</p>}

      {isError && (
        <p className="text-destructive">
          Failed to load projects: {error instanceof Error ? error.message : "Unknown error"}
        </p>
      )}

      {projects && projects.length === 0 && (
        <p className="text-muted-foreground">
          {tab === "mine"
            ? "You are not a member of any projects yet."
            : "No projects found. Try adjusting your search criteria."}
        </p>
      )}

      {projects && projects.length > 0 && (
        <div className="space-y-4">
          {projects.map((project) => (
            <ProjectCard key={project.project_id} project={project} />
          ))}
        </div>
      )}
    </div>
  )
}
