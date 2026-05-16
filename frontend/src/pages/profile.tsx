import { useState } from "react"
import { Link } from "react-router-dom"
import { Separator } from "@/components/ui/separator"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useAuthStore } from "@/stores/auth-store"
import { useUpdateProfile, useReferrals, useCreateInviteCode } from "@/hooks/use-auth"
import { useSearchProjects } from "@/hooks/use-projects"
import { ProjectCard } from "@/components/project-card"
import { ApiError } from "@/api/client"
import type { UserInviteCodeRequest } from "@/api/types"

function EditProfileForm({ onDone }: { onDone: (emailChanged: boolean) => void }) {
  const { email, displayName } = useAuthStore()
  const mutation = useUpdateProfile()

  const [emailValue, setEmailValue] = useState(email ?? "")
  const [displayNameValue, setDisplayNameValue] = useState(displayName ?? "")
  const [emailError, setEmailError] = useState<string | null>(null)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setEmailError(null)

    const payload: { email?: string; display_name?: string } = {}
    const emailChanged = emailValue.trim() !== email
    if (emailChanged) payload.email = emailValue.trim()
    if (displayNameValue.trim() !== displayName) payload.display_name = displayNameValue.trim()

    // Nothing changed — just close
    if (Object.keys(payload).length === 0) {
      onDone(false)
      return
    }

    mutation.mutate(payload, {
      onSuccess: () => onDone(emailChanged),
      onError: (err) => {
        if (err instanceof ApiError && err.status === 422) {
          setEmailError(err.detail ?? "This email is already taken.")
        } else {
          setEmailError(err.message)
        }
      },
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-1">
        <Label htmlFor="display-name">Display Name</Label>
        <Input
          id="display-name"
          value={displayNameValue}
          onChange={(e) => setDisplayNameValue(e.target.value)}
          placeholder="Your display name"
          disabled={mutation.isPending}
        />
      </div>

      <div className="space-y-1">
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          type="email"
          value={emailValue}
          onChange={(e) => { setEmailValue(e.target.value); setEmailError(null) }}
          placeholder="your@email.com"
          disabled={mutation.isPending}
          aria-invalid={emailError !== null}
        />
        {emailError && (
          <p className="text-sm text-destructive">{emailError}</p>
        )}
      </div>

      <div className="flex gap-2">
        <Button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? "Saving…" : "Save"}
        </Button>
        <Button type="button" variant="outline" onClick={() => onDone(false)} disabled={mutation.isPending}>
          Cancel
        </Button>
      </div>
    </form>
  )
}

export function ProfilePage() {
  const { userId, email, displayName } = useAuthStore()
  const [editing, setEditing] = useState(false)
  const [showEmailBanner, setShowEmailBanner] = useState(false)

  function handleDone(emailChanged: boolean) {
    setEditing(false)
    if (emailChanged) setShowEmailBanner(true)
  }

  const {
    data: ownedProjects,
    isLoading: loadingOwned,
  } = useSearchProjects(
    userId ? { owner_id: userId, status: "all" } : undefined,
  )

  const {
    data: memberProjects,
    isLoading: loadingMember,
  } = useSearchProjects(
    userId ? { member_user_id: userId, status: "all" } : undefined,
  )

  const { data: referralsData, isLoading: loadingReferrals } = useReferrals()

  const inviteMutation = useCreateInviteCode()
  const [inviteScope, setInviteScope] = useState<"system" | "project">("system")
  const [inviteProjectId, setInviteProjectId] = useState("")
  const [inviteRole, setInviteRole] = useState("")
  const [generatedCode, setGeneratedCode] = useState<{
    code: string
    expires_at: string
    scope: string
    project_id: string | null
  } | null>(null)
  const [copied, setCopied] = useState(false)

  function handleGenerateInvite() {
    const params: UserInviteCodeRequest = { scope: inviteScope }
    if (inviteScope === "project") {
      if (inviteProjectId.trim()) params.project_id = inviteProjectId.trim()
      if (inviteRole.trim()) params.role = inviteRole.trim()
    }
    inviteMutation.mutate(params, {
      onSuccess: (data) => {
        setGeneratedCode({
          code: data.code,
          expires_at: data.expires_at,
          scope: data.scope,
          project_id: data.project_id,
        })
        setCopied(false)
      },
    })
  }

  function handleCopyCode() {
    if (!generatedCode) return
    let text: string
    if (generatedCode.scope === "project" && generatedCode.project_id) {
      // Build a shareable registration link pre-filled with code + project_id
      const base = window.location.origin
      text = `${base}/register?project=${generatedCode.project_id}&code=${generatedCode.code}`
    } else {
      text = generatedCode.code
    }
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  // Exclude projects the user owns from the "member of" list
  const ownedIds = new Set(ownedProjects?.map((p) => p.project_id) ?? [])
  const otherMemberProjects = memberProjects?.filter(
    (p) => !ownedIds.has(p.project_id),
  )

  return (
    <div className="space-y-6">
      <div>
        {showEmailBanner && (
          <div
            role="status"
            className="mb-4 rounded-md border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-800 dark:border-blue-800 dark:bg-blue-950 dark:text-blue-200"
          >
            Email updated. Note: email verification is not yet required — your new address is active immediately.
            <button
              type="button"
              onClick={() => setShowEmailBanner(false)}
              className="ml-3 font-medium underline underline-offset-2 hover:no-underline"
              aria-label="Dismiss"
            >
              Dismiss
            </button>
          </div>
        )}
        {editing ? (
          <EditProfileForm onDone={handleDone} />
        ) : (
          <>
            <h1 className="text-2xl font-bold">{displayName ?? "User"}</h1>
            <p className="text-sm text-muted-foreground">{email}</p>
            {userId && (
              <p className="mt-1 font-mono text-xs text-muted-foreground">ID: {userId}</p>
            )}
            <div className="mt-2 flex items-center gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => { setEditing(true); setShowEmailBanner(false) }}
              >
                Edit Profile
              </Button>
              <Link
                to="/settings/security"
                className="text-sm text-primary underline-offset-4 hover:underline"
              >
                Security Settings &rarr;
              </Link>
            </div>
          </>
        )}
      </div>

      <Separator />

      {/* Projects I own */}
      <section>
        <h2 className="mb-3 text-lg font-semibold">My Projects</h2>
        {loadingOwned ? (
          <p className="text-sm text-muted-foreground">Loading...</p>
        ) : ownedProjects && ownedProjects.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2">
            {ownedProjects.map((project) => (
              <ProjectCard key={project.project_id} project={project} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            You haven't created any projects yet.
          </p>
        )}
      </section>

      <Separator />

      {/* Projects I'm a member of */}
      <section>
        <h2 className="mb-3 text-lg font-semibold">Projects I'm a Member Of</h2>
        {loadingMember ? (
          <p className="text-sm text-muted-foreground">Loading...</p>
        ) : otherMemberProjects && otherMemberProjects.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2">
            {otherMemberProjects.map((project) => (
              <ProjectCard key={project.project_id} project={project} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            You're not a member of any other projects.
          </p>
        )}
      </section>
      <Separator />

      {/* Referrals */}
      <section>
        <h2 className="mb-3 text-lg font-semibold">
          People I Invited
          {referralsData && referralsData.total > 0 && (
            <span className="ml-2 text-sm font-normal text-muted-foreground">
              ({referralsData.total})
            </span>
          )}
        </h2>
        {loadingReferrals ? (
          <p className="text-sm text-muted-foreground">Loading...</p>
        ) : referralsData && referralsData.referrals.length > 0 ? (
          <ul className="space-y-2">
            {referralsData.referrals.map((r) => (
              <li key={r.user_id} className="text-sm">
                <span className="font-medium">{r.display_name}</span>
                <span className="ml-2 text-muted-foreground">
                  joined {new Date(r.joined_at).toLocaleDateString()}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">
            You haven't invited anyone yet.
          </p>
        )}
      </section>
      <Separator />

      {/* Invite Code */}
      <section>
        <h2 className="mb-1 text-lg font-semibold">Invite Someone</h2>
        <p className="mb-3 text-sm text-muted-foreground">
          Generate a single-use invite code valid for 7 days.
        </p>

        {/* Scope selector */}
        <div className="mb-3 flex gap-3">
          <label className="flex items-center gap-1.5 text-sm">
            <input
              type="radio"
              name="invite-scope"
              value="system"
              checked={inviteScope === "system"}
              onChange={() => setInviteScope("system")}
            />
            Platform invite
          </label>
          <label className="flex items-center gap-1.5 text-sm">
            <input
              type="radio"
              name="invite-scope"
              value="project"
              checked={inviteScope === "project"}
              onChange={() => setInviteScope("project")}
            />
            Project invite
          </label>
        </div>

        {/* Project-scoped fields */}
        {inviteScope === "project" && (
          <div className="mb-3 space-y-2">
            <div className="space-y-1">
              <Label htmlFor="invite-project-id">Project ID</Label>
              <Input
                id="invite-project-id"
                value={inviteProjectId}
                onChange={(e) => setInviteProjectId(e.target.value)}
                placeholder="Paste project UUID"
                className="max-w-xs font-mono text-sm"
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="invite-role">Role (optional)</Label>
              <Input
                id="invite-role"
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value)}
                placeholder="e.g. member, contributor"
                className="max-w-xs"
              />
            </div>
          </div>
        )}

        <Button
          variant="outline"
          size="sm"
          onClick={handleGenerateInvite}
          disabled={inviteMutation.isPending || (inviteScope === "project" && !inviteProjectId.trim())}
        >
          {inviteMutation.isPending ? "Generating…" : "Generate Invite Code"}
        </Button>
        {inviteMutation.isError && (
          <p className="mt-2 text-sm text-destructive">
            {inviteMutation.error instanceof Error
              ? inviteMutation.error.message
              : "Failed to generate code."}
          </p>
        )}
        {generatedCode && (
          <div className="mt-3 space-y-1">
            <div className="flex items-center gap-2">
              <code className="rounded bg-muted px-3 py-1.5 font-mono text-sm">
                {generatedCode.code}
              </code>
              <Button variant="ghost" size="sm" onClick={handleCopyCode}>
                {copied
                  ? "Copied!"
                  : generatedCode.scope === "project"
                    ? "Copy Link"
                    : "Copy"}
              </Button>
              <span className="text-xs text-muted-foreground">
                expires {new Date(generatedCode.expires_at).toLocaleDateString()}
              </span>
            </div>
            {generatedCode.scope === "project" && generatedCode.project_id && (
              <p className="text-xs text-muted-foreground">
                Project invite for{" "}
                <span className="font-mono">{generatedCode.project_id}</span>
                {" "}— registrant will be auto-enrolled as a member.
              </p>
            )}
          </div>
        )}
      </section>
    </div>
  )
}
