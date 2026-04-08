import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useSubmitFeature } from "@/hooks/use-features"
import { ApiError } from "@/api/client"

interface FormErrors {
  title?: string
  description?: string
}

function validate(title: string, description: string): FormErrors {
  const errors: FormErrors = {}

  if (title.trim().length < 3) {
    errors.title = "Title must be at least 3 characters"
  } else if (title.trim().length > 500) {
    errors.title = "Title cannot exceed 500 characters"
  }

  if (description.trim().length < 1) {
    errors.description = "Description is required"
  } else if (description.length > 10_000) {
    errors.description = "Description cannot exceed 10,000 characters"
  }

  return errors
}

export function SubmitFeaturePage() {
  const navigate = useNavigate()
  const submitMutation = useSubmitFeature()

  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [category, setCategory] = useState("")
  const [priority, setPriority] = useState("")
  const [fieldErrors, setFieldErrors] = useState<FormErrors>({})

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const errors = validate(title, description)
    setFieldErrors(errors)

    if (Object.keys(errors).length > 0) {
      return
    }

    const requestId = crypto.randomUUID()

    submitMutation.mutate(
      {
        request_id: requestId,
        title: title.trim(),
        description: description.trim(),
        category: category.trim() || null,
        priority: priority.trim() || null,
      },
      {
        onSuccess: () => {
          navigate(`/features/${requestId}`)
        },
      },
    )
  }

  const serverError =
    submitMutation.error instanceof ApiError
      ? submitMutation.error.detail
      : submitMutation.error
        ? "Failed to submit feature request. Please try again."
        : null

  return (
    <div className="flex justify-center pt-6">
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle>Submit a Feature Request</CardTitle>
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
                placeholder="Short summary of your request (3-500 characters)"
                aria-invalid={!!fieldErrors.title}
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                {fieldErrors.title ? (
                  <p className="text-destructive">{fieldErrors.title}</p>
                ) : (
                  <span />
                )}
                <span>{title.length} / 500</span>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">
                Description <span className="text-destructive">*</span>
              </Label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe the feature you'd like to see. What problem does it solve? How should it work?"
                rows={6}
                aria-invalid={!!fieldErrors.description}
                className="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                {fieldErrors.description ? (
                  <p className="text-destructive">{fieldErrors.description}</p>
                ) : (
                  <span />
                )}
                <span>{description.length} / 10,000</span>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="category">Category (optional)</Label>
              <Input
                id="category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="e.g., UI/UX, Performance, Integration, Security"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="priority">Priority (optional)</Label>
              <Input
                id="priority"
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                placeholder="e.g., Low, Medium, High, Critical"
              />
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={submitMutation.isPending}
            >
              {submitMutation.isPending ? "Submitting..." : "Submit Request"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
