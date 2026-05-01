import { useState } from "react"
import { useParams, Link } from "react-router-dom"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { useAuthStore } from "@/stores/auth-store"
import {
  useProject,
  useAcceptApplication,
  useRejectApplication,
  useChangeMemberRole,
  useRemoveMember,
} from "@/hooks/use-projects"
import type {
  ProjectResponse,
  ApplicationResponse,
  MembershipResponse,
} from "@/api/types"

/** Roles that can be assigned (owner cannot be assigned). */
const ASSIGNABLE_ROLES = ["admin", "mentor", "member", "observer"] as const

const STATUS_BADGE_VARIANT: Record<string, "default" | "secondary" | "outline" | "destructive"> = {
  pending: "outline",
  accepted: "default",
  rejected: "destructive",
}

export function ManageApplicationsPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const { data: project, isLoading, isError, error } = useProject(projectId ?? "")
  const userId = useAuthStore((s) => s.userId)

  if (isLoading) {
    return <p className="text-muted-foreground">Loading project...</p>
  }

  if (isError) {
    return (
      <p className="text-destructive">
        Failed to load project: {error instanceof Error ? error.message : "Unknown error"}
      </p>
    )
  }

  if (!project) {
    return <p className="text-muted-foreground">Project not found.</p>
  }

  const isManager = project.memberships.some(
    (m) => m.user_id === userId && m.is_active && (m.role === "owner" || m.role === "admin"),
  )

  if (!isManager) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-muted-foreground">
            You don't have permission to manage this project.{" "}
            <Link to={`/projects/${project.project_id}`} className="text-primary underline">
              Back to project
            </Link>
          </p>
        </CardContent>
      </Card>
    )
  }

  const pendingApps = project.applications.filter((a) => a.status === "pending")
  const reviewedApps = project.applications.filter((a) => a.status !== "pending")
  const activeMembers = project.memberships.filter((m) => m.is_active)

  return (
    <div className="space-y-6">
      {/* Back link + title */}
      <div>
        <Link
          to={`/projects/${project.project_id}`}
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          &larr; Back to project
        </Link>
        <h1 className="mt-1 text-2xl font-bold">{project.title} — Management</h1>
      </div>

      {/* Pending applications */}
      <section>
        <h2 className="mb-3 text-lg font-semibold">
          Pending Applications ({pendingApps.length})
        </h2>
        {pendingApps.length === 0 ? (
          <p className="text-sm text-muted-foreground">No pending applications.</p>
        ) : (
          <div className="space-y-3">
            {pendingApps.map((app) => (
              <ApplicationCard key={app.application_id} application={app} project={project} />
            ))}
          </div>
        )}
      </section>

      {/* Reviewed applications */}
      {reviewedApps.length > 0 && (
        <>
          <Separator />
          <section>
            <h2 className="mb-3 text-lg font-semibold">
              Reviewed Applications ({reviewedApps.length})
            </h2>
            <div className="space-y-3">
              {reviewedApps.map((app) => (
                <ApplicationCard
                  key={app.application_id}
                  application={app}
                  project={project}
                  readonly
                />
              ))}
            </div>
          </section>
        </>
      )}

      <Separator />

      {/* Members management */}
      <section>
        <h2 className="mb-3 text-lg font-semibold">
          Members ({activeMembers.length})
        </h2>
        {activeMembers.length === 0 ? (
          <p className="text-sm text-muted-foreground">No members yet.</p>
        ) : (
          <div className="space-y-3">
            {activeMembers.map((member) => (
              <MemberCard
                key={member.membership_id}
                member={member}
                project={project}
                currentUserId={userId}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

// ---------------------------------------------------------------------------
// ApplicationCard
// ---------------------------------------------------------------------------

function ApplicationCard({
  application,
  project,
  readonly = false,
}: {
  application: ApplicationResponse
  project: ProjectResponse
  readonly?: boolean
}) {
  const acceptMutation = useAcceptApplication()
  const rejectMutation = useRejectApplication()
  const isPending = application.status === "pending"
  const actionInFlight = acceptMutation.isPending || rejectMutation.isPending

  return (
    <Card>
      <CardContent className="pt-4 pb-4">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0 flex-1 space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium truncate">
                {application.applicant_id}
              </span>
              <Badge variant={STATUS_BADGE_VARIANT[application.status] ?? "secondary"} className="text-xs">
                {application.status}
              </Badge>
            </div>
            <div className="text-sm text-muted-foreground">
              Desired role: <span className="text-foreground">{application.desired_role}</span>
            </div>
            {application.motivation && (
              <p className="text-sm text-muted-foreground">
                <span className="font-medium text-foreground">Motivation:</span>{" "}
                {application.motivation}
              </p>
            )}
            {application.applicant_skills.length > 0 && (
              <div className="flex flex-wrap gap-1 pt-1">
                {application.applicant_skills.map((skill) => (
                  <Badge key={skill} variant="outline" className="text-xs">
                    {skill}
                  </Badge>
                ))}
              </div>
            )}
            <p className="text-xs text-muted-foreground">
              Submitted: {new Date(application.submitted_at).toLocaleDateString()}
              {application.reviewed_by && (
                <> &middot; Reviewed by: {application.reviewed_by}</>
              )}
            </p>
          </div>

          {/* Accept / Reject buttons */}
          {isPending && !readonly && (
            <div className="flex shrink-0 gap-2">
              <Button
                size="sm"
                disabled={actionInFlight}
                onClick={() =>
                  acceptMutation.mutate({
                    projectId: project.project_id,
                    applicationId: application.application_id,
                  })
                }
              >
                {acceptMutation.isPending ? "Accepting..." : "Accept"}
              </Button>
              <Button
                size="sm"
                variant="destructive"
                disabled={actionInFlight}
                onClick={() =>
                  rejectMutation.mutate({
                    projectId: project.project_id,
                    applicationId: application.application_id,
                  })
                }
              >
                {rejectMutation.isPending ? "Rejecting..." : "Reject"}
              </Button>
            </div>
          )}
        </div>

        {/* Mutation errors */}
        {acceptMutation.isError && (
          <p className="mt-2 text-sm text-destructive">
            {acceptMutation.error instanceof Error ? acceptMutation.error.message : "Failed to accept"}
          </p>
        )}
        {rejectMutation.isError && (
          <p className="mt-2 text-sm text-destructive">
            {rejectMutation.error instanceof Error ? rejectMutation.error.message : "Failed to reject"}
          </p>
        )}
      </CardContent>
    </Card>
  )
}

// ---------------------------------------------------------------------------
// MemberCard
// ---------------------------------------------------------------------------

function MemberCard({
  member,
  project,
  currentUserId,
}: {
  member: MembershipResponse
  project: ProjectResponse
  currentUserId: string | null
}) {
  const changeMutation = useChangeMemberRole()
  const removeMutation = useRemoveMember()
  const [selectedRole, setSelectedRole] = useState(member.role)

  const isOwnerMember = member.role === "owner"
  const isSelf = member.user_id === currentUserId

  // Cannot change owner role or remove the owner
  const canManage = !isOwnerMember

  const handleRoleChange = () => {
    if (selectedRole === member.role) return
    changeMutation.mutate({
      projectId: project.project_id,
      membershipId: member.membership_id,
      data: { new_role: selectedRole },
    })
  }

  const handleRemove = () => {
    if (!confirm(`Remove this member from the project?`)) return
    removeMutation.mutate({
      projectId: project.project_id,
      membershipId: member.membership_id,
    })
  }

  return (
    <Card>
      <CardContent className="pt-4 pb-4">
        <div className="flex items-center justify-between gap-4">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium truncate">
                {member.user_id === project.owner_id ? (
                  <>Owner &middot; {member.user_id}</>
                ) : (
                  member.user_id
                )}
              </span>
              {isSelf && (
                <Badge variant="secondary" className="text-xs">You</Badge>
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              Joined: {new Date(member.joined_at).toLocaleDateString()}
            </p>
          </div>

          <div className="flex shrink-0 items-center gap-2">
            {canManage ? (
              <>
                <select
                  value={selectedRole}
                  onChange={(e) => setSelectedRole(e.target.value)}
                  className="h-8 rounded-md border border-input bg-background text-foreground px-2 text-sm"
                >
                  {ASSIGNABLE_ROLES.map((role) => (
                    <option key={role} value={role}>
                      {role}
                    </option>
                  ))}
                </select>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={selectedRole === member.role || changeMutation.isPending}
                  onClick={handleRoleChange}
                >
                  {changeMutation.isPending ? "Saving..." : "Save"}
                </Button>
                <Button
                  size="sm"
                  variant="destructive"
                  disabled={removeMutation.isPending}
                  onClick={handleRemove}
                >
                  {removeMutation.isPending ? "Removing..." : "Remove"}
                </Button>
              </>
            ) : (
              <Badge variant="outline" className="text-xs">{member.role}</Badge>
            )}
          </div>
        </div>

        {/* Mutation errors */}
        {changeMutation.isError && (
          <p className="mt-2 text-sm text-destructive">
            {changeMutation.error instanceof Error ? changeMutation.error.message : "Failed to change role"}
          </p>
        )}
        {removeMutation.isError && (
          <p className="mt-2 text-sm text-destructive">
            {removeMutation.error instanceof Error ? removeMutation.error.message : "Failed to remove member"}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
