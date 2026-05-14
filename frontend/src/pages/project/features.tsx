import { useState } from "react"
import { Link, useParams } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { FeatureCard } from "@/components/feature-card"
import { useFeatures } from "@/hooks/use-features"
import { useAuthStore } from "@/stores/auth-store"
import type { ListFeaturesParams } from "@/api/types"

const STATUS_OPTIONS = [
  { value: "", label: "All" },
  { value: "submitted", label: "Submitted" },
  { value: "planned", label: "Planned" },
  { value: "in_progress", label: "In Progress" },
  { value: "done", label: "Done" },
  { value: "rejected", label: "Rejected" },
]

export function ProjectFeaturesPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const [status, setStatus] = useState("")
  const [showMine, setShowMine] = useState(false)

  const { isAuthenticated, userId } = useAuthStore()

  const listParams: ListFeaturesParams = {
    ...(status ? { status } : {}),
    ...(showMine && userId ? { author_id: userId } : {}),
  }

  const { data: features, isLoading, isError, error } = useFeatures(listParams)

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Feature Requests</h1>
        {isAuthenticated && (
          <Link to={`/projects/${projectId}/features/new`}>
            <Button size="sm">Submit Request</Button>
          </Link>
        )}
      </div>

      {/* Filter controls */}
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="flex flex-wrap gap-2">
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

        {isAuthenticated && (
          <Button
            variant={showMine ? "default" : "outline"}
            size="sm"
            onClick={() => setShowMine(!showMine)}
            className="sm:ml-auto"
          >
            My Requests
          </Button>
        )}
      </div>

      {/* Results */}
      {isLoading && (
        <p className="text-muted-foreground">Loading feature requests...</p>
      )}

      {isError && (
        <p className="text-destructive">
          Failed to load feature requests:{" "}
          {error instanceof Error ? error.message : "Unknown error"}
        </p>
      )}

      {features && features.length === 0 && (
        <p className="text-muted-foreground">
          No feature requests yet.{" "}
          {isAuthenticated && (
            <Link
              to={`/projects/${projectId}/features/new`}
              className="text-primary underline hover:no-underline"
            >
              Submit one?
            </Link>
          )}
        </p>
      )}

      {features && features.length > 0 && (
        <div className="space-y-4">
          {features.map((feature) => (
            <FeatureCard key={feature.request_id} feature={feature} />
          ))}
        </div>
      )}
    </div>
  )
}
