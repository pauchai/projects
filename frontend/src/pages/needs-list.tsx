/**
 * Public Needs List — /needs
 *
 * Shows all open project needs across the platform.
 * Authenticated users can apply directly from this page.
 */

import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useAuthStore } from "@/stores/auth-store"
import { useOpenNeeds } from "@/hooks/use-needs"
import { useApplyToProject } from "@/hooks/use-projects"

function ApplyDialog({
  need,
  onClose,
}: {
  need: { need_id: string; project_id: string; role: string }
  onClose: () => void
}) {
  const [motivation, setMotivation] = useState("")
  const [skills, setSkills] = useState("")
  const applyMutation = useApplyToProject(need.project_id)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    applyMutation.mutate(
      {
        application_id: globalThis.crypto.randomUUID(),
        desired_role: need.role,
        motivation,
        applicant_skills: skills
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        need_id: need.need_id,
      },
      { onSuccess: onClose },
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg border border-border bg-background p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold">Apply for {need.role}</h2>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="motivation">Motivation</Label>
            <Input
              id="motivation"
              placeholder="Why do you want to join this project?"
              value={motivation}
              onChange={(e) => setMotivation(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="skills">Skills (comma-separated)</Label>
            <Input
              id="skills"
              placeholder="e.g. React, Python, Design"
              value={skills}
              onChange={(e) => setSkills(e.target.value)}
            />
          </div>
          {applyMutation.isError && (
            <p className="text-sm text-destructive">
              {(applyMutation.error as Error)?.message ?? "Something went wrong"}
            </p>
          )}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={applyMutation.isPending}>
              {applyMutation.isPending ? "Submitting…" : "Submit"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

export function NeedsListPage() {
  const { data: needs, isLoading, isError } = useOpenNeeds()
  const { isAuthenticated } = useAuthStore()
  const navigate = useNavigate()
  const [applyTarget, setApplyTarget] = useState<{
    need_id: string
    project_id: string
    role: string
  } | null>(null)

  if (isLoading) {
    return <p className="text-muted-foreground">Loading needs…</p>
  }

  if (isError) {
    return <p className="text-destructive">Failed to load needs.</p>
  }

  if (!needs || needs.length === 0) {
    return (
      <div className="flex flex-col items-center gap-4 py-16 text-center">
        <p className="text-muted-foreground">No open needs at the moment.</p>
        <Link to="/projects">
          <Button variant="outline">Browse projects</Button>
        </Link>
      </div>
    )
  }

  return (
    <>
      {applyTarget && (
        <ApplyDialog need={applyTarget} onClose={() => setApplyTarget(null)} />
      )}

      <div className="flex flex-col gap-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Open Needs</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Projects are looking for contributors. Find a role that fits you.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          {needs.map((need) => (
            <Card key={need.need_id} className="flex flex-col justify-between">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-base leading-snug">
                    {need.role}
                  </CardTitle>
                  <Badge variant="outline" className="shrink-0 text-xs">
                    {need.slots} slot{need.slots !== 1 ? "s" : ""}
                  </Badge>
                </div>
                <Link
                  to={`/projects/${need.project_id}`}
                  className="mt-0.5 text-sm font-medium text-primary hover:underline"
                >
                  {need.project_title}
                </Link>
              </CardHeader>

              <CardContent className="flex flex-col gap-3">
                <p className="text-sm text-muted-foreground line-clamp-3">
                  {need.description}
                </p>

                {need.skills.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {need.skills.map((skill) => (
                      <Badge key={skill} variant="secondary" className="text-xs">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                )}

                {isAuthenticated ? (
                  <Button
                    size="sm"
                    className="mt-1 self-start"
                    onClick={() =>
                      setApplyTarget({
                        need_id: need.need_id,
                        project_id: need.project_id,
                        role: need.role,
                      })
                    }
                  >
                    Apply
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    variant="outline"
                    className="mt-1 self-start"
                    onClick={() => navigate("/login")}
                  >
                    Log in to apply
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </>
  )
}
