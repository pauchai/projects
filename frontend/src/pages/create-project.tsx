import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useCreateProject } from "@/hooks/use-projects"
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

export function CreateProjectPage() {
  const navigate = useNavigate()
  const createMutation = useCreateProject()

  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [skills, setSkills] = useState("")
  const [maxMembers, setMaxMembers] = useState("")
  const [fieldErrors, setFieldErrors] = useState<FormErrors>({})

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const errors = validate(title, description, maxMembers)
    setFieldErrors(errors)

    if (Object.keys(errors).length > 0) {
      return
    }

    const projectId = crypto.randomUUID()
    const skillsList = skills
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean)

    createMutation.mutate(
      {
        project_id: projectId,
        title: title.trim(),
        description: description || undefined,
        required_skills: skillsList.length > 0 ? skillsList : undefined,
        max_members: maxMembers.trim() ? Number(maxMembers) : null,
      },
      {
        onSuccess: () => {
          navigate(`/projects/${projectId}`)
        },
      },
    )
  }

  const serverError =
    createMutation.error instanceof ApiError
      ? createMutation.error.detail
      : createMutation.error
        ? "Failed to create project. Please try again."
        : null

  return (
    <div className="flex justify-center pt-6">
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle>Create a new project</CardTitle>
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
                placeholder="Project title (3-200 characters)"
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
              className="w-full"
              disabled={createMutation.isPending}
            >
              {createMutation.isPending ? "Creating..." : "Create Project"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
