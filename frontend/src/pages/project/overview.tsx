/**
 * Project workspace — Overview tab.
 *
 * Adapted from the old project-detail page.
 * Navigation links now point to workspace sub-routes.
 */

import { useState } from "react"
import { useParams, Link } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { useAuthStore } from "@/stores/auth-store"
import {
  useProject,
  usePublishProject,
  useActivateProject,
  useSuspendProject,
  useResumeProject,
  useCompleteProject,
  useCancelProject,
  useApplyToProject,
} from "@/hooks/use-projects"
import {
  useProjectNeeds,
  useCreateProjectNeed,
  useCloseProjectNeed,
} from "@/hooks/use-project-needs"
import type { ProjectResponse, ProjectNeedResponse } from "@/api/types"

const STATUS_VARIANT: Record<string, "default" | "secondary" | "outline" | "destructive"> = {
  draft: "secondary",
  recruiting: "outline",
  active: "default",
  suspended: "destructive",
  completed: "secondary",
  cancelled: "destructive",
}

function getStatusActions(status: string) {
  const actions: Array<{
    label: string
    hook: "publish" | "activate" | "suspend" | "resume" | "complete" | "cancel"
    variant: "default" | "outline" | "destructive"
  }> = []

  switch (status) {
    case "draft":
      actions.push({ label: "Publish", hook: "publish", variant: "default" })
      break
    case "recruiting":
      actions.push({ label: "Activate", hook: "activate", variant: "default" })
      actions.push({ label: "Suspend", hook: "suspend", variant: "outline" })
      actions.push({ label: "Cancel", hook: "cancel", variant: "destructive" })
      break
    case "active":
      actions.push({ label: "Complete", hook: "complete", variant: "default" })
      actions.push({ label: "Suspend", hook: "suspend", variant: "outline" })
      actions.push({ label: "Cancel", hook: "cancel", variant: "destructive" })
      break
    case "suspended":
      actions.push({ label: "Resume", hook: "resume", variant: "default" })
      break
  }

  return actions
}

export function ProjectOverviewPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const { data: project, isLoading, isError, error } = useProject(projectId ?? "")
  const userId = useAuthStore((s) => s.userId)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

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

  const isOwner = userId === project.owner_id
  const isManager = project.memberships.some(
    (m) => m.user_id === userId && m.is_active && (m.role === "owner" || m.role === "admin"),
  )
  const isMember = project.memberships.some((m) => m.user_id === userId && m.is_active)
  const hasApplied = project.applications.some((a) => a.applicant_id === userId)
  const canApply =
    isAuthenticated &&
    !isOwner &&
    !isMember &&
    !hasApplied &&
    project.status === "recruiting"

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-start justify-between gap-4">
          <h1 className="text-2xl font-bold">{project.title}</h1>
          <Badge
            variant={STATUS_VARIANT[project.status] ?? "secondary"}
            className="shrink-0 text-sm"
          >
            {project.status}
          </Badge>
        </div>
        {project.description && (
          <p className="mt-2 text-muted-foreground whitespace-pre-wrap">
            {project.description}
          </p>
        )}
      </div>

      {/* Meta info */}
      <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
        {project.max_members !== null && (
          <span>Max members: {project.max_members}</span>
        )}
        <span>Created: {new Date(project.created_at).toLocaleDateString()}</span>
      </div>

      {/* Skills */}
      {project.required_skills.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {project.required_skills.map((skill) => (
            <Badge key={skill} variant="outline">
              {skill}
            </Badge>
          ))}
        </div>
      )}

      {/* Owner actions */}
      {isOwner && <OwnerActions project={project} />}

      {/* Apply section */}
      {canApply && <ApplySection projectId={project.project_id} />}

      {hasApplied && !isMember && !isOwner && (
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground">
              You have already applied to this project.
            </p>
          </CardContent>
        </Card>
      )}

      <Separator />

      {/* Members */}
      <MembersSection project={project} />

      <Separator />

      {/* Project Needs */}
      <ProjectNeedsSection projectId={project.project_id} isMember={isMember || isOwner} />

      {/* Applications summary + link to settings tab (owner / admin) */}
      {isManager && (
        <>
          <Separator />
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold">
                Applications ({project.applications.length})
              </h2>
              <Link
                to={`/projects/${project.project_id}/settings/applications`}
                className="text-sm text-primary underline hover:no-underline"
              >
                Manage &rarr;
              </Link>
            </div>
            {project.applications.filter((a) => a.status === "pending").length > 0 ? (
              <p className="text-sm text-muted-foreground">
                {project.applications.filter((a) => a.status === "pending").length} pending
                application(s) awaiting review.
              </p>
            ) : (
              <p className="text-sm text-muted-foreground">No pending applications.</p>
            )}
          </div>
        </>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function OwnerActions({ project }: { project: ProjectResponse }) {
  const publishProject = usePublishProject()
  const activateProject = useActivateProject()
  const suspendProject = useSuspendProject()
  const resumeProject = useResumeProject()
  const completeProject = useCompleteProject()
  const cancelProject = useCancelProject()

  const hooks = {
    publish: publishProject,
    activate: activateProject,
    suspend: suspendProject,
    resume: resumeProject,
    complete: completeProject,
    cancel: cancelProject,
  }

  const actions = getStatusActions(project.status)

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Project Actions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-2">
          {actions.map((action) => {
            const mutation = hooks[action.hook]
            return (
              <Button
                key={action.hook}
                variant={action.variant}
                size="sm"
                disabled={mutation.isPending}
                onClick={() => mutation.mutate(project.project_id)}
              >
                {mutation.isPending ? `${action.label}...` : action.label}
              </Button>
            )
          })}
          <Link to={`/projects/${project.project_id}/settings`}>
            <Button variant="outline" size="sm">
              Settings
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  )
}

function ApplySection({ projectId }: { projectId: string }) {
  const applyMutation = useApplyToProject()
  const [desiredRole, setDesiredRole] = useState("contributor")
  const [motivation, setMotivation] = useState("")
  const [skills, setSkills] = useState("")
  const [showForm, setShowForm] = useState(false)

  const handleApply = (e: React.FormEvent) => {
    e.preventDefault()
    applyMutation.mutate(
      {
        projectId,
        data: {
          application_id: crypto.randomUUID(),
          desired_role: desiredRole,
          motivation: motivation || undefined,
          applicant_skills: skills
            ? skills
                .split(",")
                .map((s) => s.trim())
                .filter(Boolean)
            : undefined,
        },
      },
      {
        onSuccess: () => {
          setShowForm(false)
        },
      },
    )
  }

  if (!showForm) {
    return <Button onClick={() => setShowForm(true)}>Apply to join</Button>
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Apply to Join</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleApply} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="desiredRole">Desired role</Label>
            <Input
              id="desiredRole"
              value={desiredRole}
              onChange={(e) => setDesiredRole(e.target.value)}
              placeholder="e.g., contributor, designer, developer"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="motivation">Motivation (optional)</Label>
            <Input
              id="motivation"
              value={motivation}
              onChange={(e) => setMotivation(e.target.value)}
              placeholder="Why do you want to join?"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="skills">Your skills (optional, comma-separated)</Label>
            <Input
              id="skills"
              value={skills}
              onChange={(e) => setSkills(e.target.value)}
              placeholder="e.g., React, Python, Design"
            />
          </div>
          <div className="flex gap-2">
            <Button type="submit" disabled={applyMutation.isPending}>
              {applyMutation.isPending ? "Applying..." : "Submit Application"}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowForm(false)}
            >
              Cancel
            </Button>
          </div>
          {applyMutation.isError && (
            <p className="text-sm text-destructive">
              {applyMutation.error instanceof Error
                ? applyMutation.error.message
                : "Failed to apply"}
            </p>
          )}
        </form>
      </CardContent>
    </Card>
  )
}

function MembersSection({ project }: { project: ProjectResponse }) {
  const activeMembers = project.memberships.filter((m) => m.is_active)

  return (
    <div>
      <h2 className="mb-3 text-lg font-semibold">Members ({activeMembers.length})</h2>
      {activeMembers.length === 0 ? (
        <p className="text-sm text-muted-foreground">No members yet.</p>
      ) : (
        <div className="space-y-2">
          {activeMembers.map((member) => (
            <div
              key={member.membership_id}
              className="flex items-center justify-between rounded-md border px-4 py-2"
            >
              <span className="text-sm">
                {member.user_id === project.owner_id ? (
                  <span className="font-medium">Owner</span>
                ) : (
                  member.user_id
                )}
              </span>
              <Badge variant="outline" className="text-xs">
                {member.role}
              </Badge>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Project Needs
// ---------------------------------------------------------------------------

function ProjectNeedsSection({
  projectId,
  isMember,
}: {
  projectId: string
  isMember: boolean
}) {
  const { data: needs, isLoading } = useProjectNeeds(projectId)
  const createNeed = useCreateProjectNeed(projectId)
  const closeNeed = useCloseProjectNeed(projectId)
  const [showForm, setShowForm] = useState(false)
  const [role, setRole] = useState("member")
  const [description, setDescription] = useState("")
  const [skills, setSkills] = useState("")
  const [slots, setSlots] = useState(1)

  function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    createNeed.mutate(
      {
        role: role.trim(),
        description: description.trim(),
        skills: skills ? skills.split(",").map((s) => s.trim()).filter(Boolean) : undefined,
        slots: slots,
      },
      {
        onSuccess: () => {
          setRole("member")
          setDescription("")
          setSkills("")
          setSlots(1)
          setShowForm(false)
        },
      },
    )
  }

  const openNeeds = needs?.filter((n) => n.status === "open") ?? []

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold">
          Project Needs
          {openNeeds.length > 0 && (
            <span className="ml-2 text-sm font-normal text-muted-foreground">
              ({openNeeds.length} open)
            </span>
          )}
        </h2>
        {isMember && !showForm && (
          <Button variant="outline" size="sm" onClick={() => setShowForm(true)}>
            Add Need
          </Button>
        )}
      </div>

      {showForm && (
        <Card className="mb-4">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">New Project Need</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-3">
              <div className="space-y-1">
                <Label htmlFor="need-role">Role *</Label>
                <Input
                  id="need-role"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  placeholder="member, mentor, admin, observer"
                  required
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="need-description">Description *</Label>
                <Input
                  id="need-description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="What will this person work on?"
                  required
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="need-skills">Skills (optional, comma-separated)</Label>
                <Input
                  id="need-skills"
                  value={skills}
                  onChange={(e) => setSkills(e.target.value)}
                  placeholder="e.g. React, TypeScript"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="need-slots">Slots</Label>
                <Input
                  id="need-slots"
                  type="number"
                  min={1}
                  value={slots}
                  onChange={(e) => setSlots(Number(e.target.value))}
                  className="w-20"
                />
              </div>
              <div className="flex gap-2">
                <Button
                  type="submit"
                  size="sm"
                  disabled={createNeed.isPending || !role.trim() || !description.trim()}
                >
                  {createNeed.isPending ? "Creating…" : "Create"}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowForm(false)}
                >
                  Cancel
                </Button>
              </div>
              {createNeed.isError && (
                <p className="text-sm text-destructive">
                  {createNeed.error instanceof Error
                    ? createNeed.error.message
                    : "Failed to create need."}
                </p>
              )}
            </form>
          </CardContent>
        </Card>
      )}

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading...</p>
      ) : openNeeds.length === 0 ? (
        <p className="text-sm text-muted-foreground">No open needs at the moment.</p>
      ) : (
        <div className="space-y-2">
          {openNeeds.map((need) => (
            <NeedRow
              key={need.need_id}
              need={need}
              isMember={isMember}
              onClose={() => closeNeed.mutate(need.need_id)}
              isClosing={closeNeed.isPending}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function NeedRow({
  need,
  isMember,
  onClose,
  isClosing,
}: {
  need: ProjectNeedResponse
  isMember: boolean
  onClose: () => void
  isClosing: boolean
}) {
  return (
    <div className="flex items-start justify-between rounded-md border px-4 py-3 gap-4">
      <div className="min-w-0 flex-1 space-y-1">
        <p className="text-sm font-medium">{need.description}</p>
        <div className="flex flex-wrap gap-1 mt-1">
          <Badge variant="secondary" className="text-xs">
            {need.role}
          </Badge>
          {need.slots > 1 && (
            <Badge variant="outline" className="text-xs">
              {need.slots} slots
            </Badge>
          )}
          {need.skills.map((s) => (
            <Badge key={s} variant="outline" className="text-xs">
              {s}
            </Badge>
          ))}
        </div>
      </div>
      {isMember && (
        <Button
          variant="ghost"
          size="sm"
          className="shrink-0 text-xs"
          onClick={onClose}
          disabled={isClosing}
        >
          Close
        </Button>
      )}
    </div>
  )
}
