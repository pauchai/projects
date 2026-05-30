/**
 * Project workspace — Settings tab (general project settings / edit form).
 *
 * Adapted from edit-project.tsx for the workspace settings tab.
 * On save, stays within the workspace (navigates to overview tab).
 */

import { useState, useEffect } from "react"
import { useParams, useNavigate, Link } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { useProject, useUpdateProject } from "@/hooks/use-projects"
import { useSetDocsRepoUrl, useSyncDocsVolume } from "@/hooks/use-docs"
import { useAuthStore } from "@/stores/auth-store"
import { ApiError } from "@/api/client"

interface FormErrors {
  title?: string
  description?: string
  maxMembers?: string
}

function validate(title: string, description: string, maxMembers: string): FormErrors {
  const errors: FormErrors = {}

  if (title.trim().length < 3) {
    errors.title = "Title must be at least 3 characters"
  } else if (title.trim().length > 200) {
    errors.title = "Title cannot exceed 200 characters"
  }

  if (description.length > 5000) {
    errors.description = "Description cannot exceed 5000 characters"
  }

  if (maxMembers.trim() !== "") {
    const num = Number(maxMembers)
    if (!Number.isInteger(num) || num < 1) {
      errors.maxMembers = "Must be a positive integer"
    }
  }

  return errors
}

export function ProjectSettingsPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const { data: project, isLoading, isError, error } = useProject(projectId ?? "")
  const userId = useAuthStore((s) => s.userId)
  const updateMutation = useUpdateProject()
  const setDocsRepoUrlMutation = useSetDocsRepoUrl(projectId ?? "")
  const syncDocsMutation = useSyncDocsVolume(projectId ?? "")

  const isOwner = project?.owner_id === userId

  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [skills, setSkills] = useState("")
  const [maxMembers, setMaxMembers] = useState("")
  const [fieldErrors, setFieldErrors] = useState<FormErrors>({})
  const [initialized, setInitialized] = useState(false)
  const [docsRepoUrl, setDocsRepoUrl] = useState("")

  useEffect(() => {
    if (project && !initialized) {
      setTitle(project.title)
      setDescription(project.description)
      setSkills(project.required_skills.join(", "))
      setMaxMembers(project.max_members?.toString() ?? "")
      setDocsRepoUrl(project.docs_repo_url ?? "")
      setInitialized(true)
    }
  }, [project, initialized])

  if (isLoading) {
    return <p className="text-muted-foreground">Loading project...</p>
  }

  if (isError) {
    return (
      <p className="text-destructive">
        Failed to load project:{" "}
        {error instanceof Error ? error.message : "Unknown error"}
      </p>
    )
  }

  if (!project) {
    return <p className="text-muted-foreground">Project not found.</p>
  }

  if (!isOwner) {
    return (
      <p className="text-destructive">
        You do not have permission to edit this project.
      </p>
    )
  }

  if (!initialized) {
    // Initialization now handled by useEffect above
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const errors = validate(title, description, maxMembers)
    setFieldErrors(errors)

    if (Object.keys(errors).length > 0) return

    const skillsList = skills
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean)

    updateMutation.mutate(
      {
        projectId: project.project_id,
        data: {
          title: title.trim(),
          description: description || "",
          required_skills: skillsList.length > 0 ? skillsList : [],
          max_members: maxMembers.trim() ? Number(maxMembers) : null,
        },
      },
      {
        onSuccess: () => {
          navigate(`/projects/${project.project_id}/overview`)
        },
      },
    )
  }

  const serverError =
    updateMutation.error instanceof ApiError
      ? updateMutation.error.detail
      : updateMutation.error
        ? "Failed to update project. Please try again."
        : null

  return (
    <div className="space-y-8">
      {/* General settings form */}
      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>General Settings</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {serverError && (
              <p className="text-sm text-destructive">{serverError}</p>
            )}

            <div className="space-y-2">
              <Label htmlFor="title">
                Title <span className="text-destructive">*</span>
              </Label>
              <Input
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Project title (3–200 characters)"
                aria-invalid={!!fieldErrors.title}
              />
              {fieldErrors.title && (
                <p className="text-sm text-destructive">{fieldErrors.title}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe what this project is about (max 5000 characters)"
                rows={5}
                className="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                {fieldErrors.description ? (
                  <p className="text-destructive">{fieldErrors.description}</p>
                ) : (
                  <span />
                )}
                <span>{description.length} / 5000</span>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="skills">Required skills (comma-separated)</Label>
              <Input
                id="skills"
                value={skills}
                onChange={(e) => setSkills(e.target.value)}
                placeholder="e.g., React, Python, UI/UX Design"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="maxMembers">Max members (optional)</Label>
              <Input
                id="maxMembers"
                type="number"
                min="1"
                value={maxMembers}
                onChange={(e) => setMaxMembers(e.target.value)}
                placeholder="Leave empty for unlimited"
                aria-invalid={!!fieldErrors.maxMembers}
              />
              {fieldErrors.maxMembers && (
                <p className="text-sm text-destructive">{fieldErrors.maxMembers}</p>
              )}
            </div>

            <Button
              type="submit"
              disabled={updateMutation.isPending}
            >
              {updateMutation.isPending ? "Saving..." : "Save Changes"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Separator />

      {/* Docs Volume */}
      <Card className="max-w-2xl">
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Docs Volume</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="docsRepoUrl">Docs Repo URL</Label>
            <p className="text-xs text-muted-foreground">
              Git repository for project documentation (include token for private repos:{" "}
              <code>https://&lt;token&gt;@github.com/…</code>).
            </p>
            <div className="flex gap-2">
              <Input
                id="docsRepoUrl"
                value={docsRepoUrl}
                onChange={(e) => setDocsRepoUrl(e.target.value)}
                placeholder="https://<token>@github.com/org/docs.git"
                className="font-mono text-sm flex-1"
              />
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  setDocsRepoUrlMutation.mutate(docsRepoUrl.trim() || null)
                }
                disabled={setDocsRepoUrlMutation.isPending}
              >
                {setDocsRepoUrlMutation.isPending ? "Saving…" : "Save"}
              </Button>
            </div>
            {setDocsRepoUrlMutation.isSuccess && (
              <p className="text-xs text-emerald-600">Docs repo URL saved.</p>
            )}
            {setDocsRepoUrlMutation.isError && (
              <p className="text-xs text-destructive">Failed to save.</p>
            )}
          </div>

          <div className="space-y-1">
            <p className="text-sm font-medium">Sync Docs</p>
            <p className="text-xs text-muted-foreground">
              Clone or pull the docs repository into the local volume.
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => syncDocsMutation.mutate()}
              disabled={syncDocsMutation.isPending || !project.docs_repo_url}
            >
              {syncDocsMutation.isPending ? "Syncing…" : "Sync Docs"}
            </Button>
            {syncDocsMutation.isSuccess && (
              <p className="text-xs text-emerald-600">
                {syncDocsMutation.data?.message ?? "Docs synced."}
              </p>
            )}
            {syncDocsMutation.isError && (
              <p className="text-xs text-destructive">Sync failed.</p>
            )}
          </div>
        </CardContent>
      </Card>

      <Separator />

      {/* Applications sub-section link */}
      <div>
        <h2 className="mb-2 text-base font-semibold">Applications & Members</h2>
        <p className="text-sm text-muted-foreground mb-3">
          Review incoming applications and manage member roles.
        </p>
        <Link to={`/projects/${project.project_id}/settings/applications`}>
          <Button variant="outline">
            Manage Applications →
          </Button>
        </Link>
      </div>
    </div>
  )
}
