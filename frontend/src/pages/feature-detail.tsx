import { useState } from "react"
import { useParams, Link } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { useAuthStore } from "@/stores/auth-store"
import { useFeature, useUpdateFeatureStatus } from "@/hooks/use-features"
import { ApiError } from "@/api/client"
import type { FeatureStatus } from "@/api/types"

/** Status badge color map */
const STATUS_VARIANT: Record<
  string,
  "default" | "secondary" | "outline" | "destructive"
> = {
  submitted: "outline",
  planned: "secondary",
  in_progress: "default",
  done: "secondary",
  rejected: "destructive",
}

const STATUS_LABELS: Record<string, string> = {
  submitted: "Submitted",
  planned: "Planned",
  in_progress: "In Progress",
  done: "Done",
  rejected: "Rejected",
}

/**
 * Returns the list of allowed status transitions for the current status.
 */
function getStatusTransitions(
  status: string,
): Array<{
  target: FeatureStatus
  label: string
  variant: "default" | "outline" | "destructive"
}> {
  switch (status) {
    case "submitted":
      return [
        { target: "planned", label: "Plan", variant: "default" },
        { target: "rejected", label: "Reject", variant: "destructive" },
      ]
    case "planned":
      return [
        { target: "in_progress", label: "Start Work", variant: "default" },
        { target: "rejected", label: "Reject", variant: "destructive" },
      ]
    case "in_progress":
      return [
        { target: "done", label: "Mark Done", variant: "default" },
        { target: "planned", label: "Back to Planned", variant: "outline" },
        { target: "rejected", label: "Reject", variant: "destructive" },
      ]
    default:
      return []
  }
}

export function FeatureDetailPage() {
  const { requestId } = useParams<{ requestId: string }>()
  const { data: feature, isLoading, isError, error } = useFeature(requestId ?? "")
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  if (isLoading) {
    return <p className="text-muted-foreground">Loading feature request...</p>
  }

  if (isError) {
    return (
      <p className="text-destructive">
        Failed to load feature request:{" "}
        {error instanceof Error ? error.message : "Unknown error"}
      </p>
    )
  }

  if (!feature) {
    return <p className="text-muted-foreground">Feature request not found.</p>
  }

  const transitions = getStatusTransitions(feature.status)

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link
        to="/features"
        className="text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        &larr; All Feature Requests
      </Link>

      {/* Header */}
      <div>
        <div className="flex items-start justify-between gap-4">
          <h1 className="text-2xl font-bold">{feature.title}</h1>
          <Badge
            variant={STATUS_VARIANT[feature.status] ?? "secondary"}
            className="shrink-0 text-sm"
          >
            {STATUS_LABELS[feature.status] ?? feature.status}
          </Badge>
        </div>
      </div>

      {/* Meta info */}
      <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
        {feature.category && <span>Category: {feature.category}</span>}
        {feature.priority && <span>Priority: {feature.priority}</span>}
        <span>Created: {new Date(feature.created_at).toLocaleDateString()}</span>
        <span>Updated: {new Date(feature.updated_at).toLocaleDateString()}</span>
      </div>

      {/* Description */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Description</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="whitespace-pre-wrap text-sm text-muted-foreground">
            {feature.description}
          </p>
        </CardContent>
      </Card>

      {/* Admin notes */}
      {feature.admin_notes && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Admin Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="whitespace-pre-wrap text-sm text-muted-foreground">
              {feature.admin_notes}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Status management (authenticated users) */}
      {isAuthenticated && transitions.length > 0 && (
        <>
          <Separator />
          <StatusManagement
            requestId={feature.request_id}
            currentStatus={feature.status}
            transitions={transitions}
          />
        </>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Sub-component: Status Management
// ---------------------------------------------------------------------------

function StatusManagement({
  requestId,
  currentStatus,
  transitions,
}: {
  requestId: string
  currentStatus: string
  transitions: Array<{
    target: FeatureStatus
    label: string
    variant: "default" | "outline" | "destructive"
  }>
}) {
  const updateStatus = useUpdateFeatureStatus()
  const [adminNotes, setAdminNotes] = useState("")
  const [pendingTarget, setPendingTarget] = useState<FeatureStatus | null>(null)

  const handleStatusChange = (target: FeatureStatus) => {
    setPendingTarget(target)
    updateStatus.mutate(
      {
        requestId,
        data: {
          status: target,
          admin_notes: adminNotes.trim() || null,
        },
      },
      {
        onSuccess: () => {
          setAdminNotes("")
          setPendingTarget(null)
        },
        onError: () => {
          setPendingTarget(null)
        },
      },
    )
  }

  const serverError =
    updateStatus.error instanceof ApiError
      ? updateStatus.error.detail
      : updateStatus.error
        ? "Failed to update status. Please try again."
        : null

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Manage Status</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">
          Current status:{" "}
          <span className="font-medium text-foreground">
            {STATUS_LABELS[currentStatus] ?? currentStatus}
          </span>
        </p>

        <div className="space-y-2">
          <Label htmlFor="adminNotes">Admin Notes (optional)</Label>
          <textarea
            id="adminNotes"
            value={adminNotes}
            onChange={(e) => setAdminNotes(e.target.value)}
            placeholder="Add a note about this status change..."
            rows={3}
            className="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
          />
        </div>

        {serverError && (
          <p className="text-sm text-destructive">{serverError}</p>
        )}

        <div className="flex flex-wrap gap-2">
          {transitions.map((transition) => (
            <Button
              key={transition.target}
              variant={transition.variant}
              size="sm"
              disabled={updateStatus.isPending}
              onClick={() => handleStatusChange(transition.target)}
            >
              {updateStatus.isPending && pendingTarget === transition.target
                ? `${transition.label}...`
                : transition.label}
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
