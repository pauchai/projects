import { Link } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { ProjectSummaryResponse } from "@/api/types"

/** Human-readable status labels and color variants */
const STATUS_CONFIG: Record<string, { label: string; variant: "default" | "secondary" | "outline" | "destructive" }> = {
  draft: { label: "Draft", variant: "secondary" },
  recruiting: { label: "Recruiting", variant: "outline" },
  active: { label: "Active", variant: "default" },
  suspended: { label: "Suspended", variant: "destructive" },
  completed: { label: "Completed", variant: "secondary" },
  cancelled: { label: "Cancelled", variant: "destructive" },
}

interface ProjectCardProps {
  project: ProjectSummaryResponse
}

export function ProjectCard({ project }: ProjectCardProps) {
  const statusConfig = STATUS_CONFIG[project.status] ?? {
    label: project.status,
    variant: "secondary" as const,
  }

  return (
    <Link to={`/projects/${project.project_id}`} className="block">
      <Card className="transition-colors hover:border-primary/50">
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between gap-2">
            <CardTitle className="text-lg leading-snug">
              {project.title}
            </CardTitle>
            <Badge variant={statusConfig.variant} className="shrink-0">
              {statusConfig.label}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {project.description && (
            <p className="mb-3 line-clamp-2 text-sm text-muted-foreground">
              {project.description}
            </p>
          )}
          {project.required_skills.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {project.required_skills.map((skill) => (
                <Badge key={skill} variant="outline" className="text-xs">
                  {skill}
                </Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  )
}
