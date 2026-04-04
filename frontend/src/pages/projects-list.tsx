import { useState } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { ProjectCard } from "@/components/project-card"
import { useSearchProjects } from "@/hooks/use-projects"
import type { SearchProjectsParams } from "@/api/types"

const STATUS_OPTIONS = [
  { value: "", label: "All" },
  { value: "recruiting", label: "Recruiting" },
  { value: "active", label: "Active" },
  { value: "completed", label: "Completed" },
]

export function ProjectsListPage() {
  const [keyword, setKeyword] = useState("")
  const [skills, setSkills] = useState("")
  const [status, setStatus] = useState("")

  /** Build the params object for the query */
  const searchParams: SearchProjectsParams = {
    ...(keyword.trim() ? { keyword: keyword.trim() } : {}),
    ...(skills.trim() ? { skills: skills.trim() } : {}),
    ...(status ? { status } : {}),
  }

  const { data: projects, isLoading, isError, error } = useSearchProjects(searchParams)

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">Projects</h1>

      {/* Search and filter controls */}
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

      {/* Results */}
      {isLoading && (
        <p className="text-muted-foreground">Loading projects...</p>
      )}

      {isError && (
        <p className="text-destructive">
          Failed to load projects: {error instanceof Error ? error.message : "Unknown error"}
        </p>
      )}

      {projects && projects.length === 0 && (
        <p className="text-muted-foreground">
          No projects found. Try adjusting your search criteria.
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
