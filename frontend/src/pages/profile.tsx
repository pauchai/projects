import { useState } from "react"
import { Link } from "react-router-dom"
import { Separator } from "@/components/ui/separator"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useAuthStore } from "@/stores/auth-store"
import { useUpdateProfile } from "@/hooks/use-auth"
import { useSearchProjects } from "@/hooks/use-projects"
import { ProjectCard } from "@/components/project-card"
import { ApiError } from "@/api/client"

function EditProfileForm({ onCancel }: { onCancel: () => void }) {
  const { email, displayName } = useAuthStore()
  const mutation = useUpdateProfile()

  const [emailValue, setEmailValue] = useState(email ?? "")
  const [displayNameValue, setDisplayNameValue] = useState(displayName ?? "")
  const [emailError, setEmailError] = useState<string | null>(null)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setEmailError(null)

    const payload: { email?: string; display_name?: string } = {}
    if (emailValue.trim() !== email) payload.email = emailValue.trim()
    if (displayNameValue.trim() !== displayName) payload.display_name = displayNameValue.trim()

    // Nothing changed — just close
    if (Object.keys(payload).length === 0) {
      onCancel()
      return
    }

    mutation.mutate(payload, {
      onSuccess: () => onCancel(),
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
        <Button type="button" variant="outline" onClick={onCancel} disabled={mutation.isPending}>
          Cancel
        </Button>
      </div>
    </form>
  )
}

export function ProfilePage() {
  const { userId, email, displayName } = useAuthStore()
  const [editing, setEditing] = useState(false)

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

  // Exclude projects the user owns from the "member of" list
  const ownedIds = new Set(ownedProjects?.map((p) => p.project_id) ?? [])
  const otherMemberProjects = memberProjects?.filter(
    (p) => !ownedIds.has(p.project_id),
  )

  return (
    <div className="space-y-6">
      <div>
        {editing ? (
          <EditProfileForm onCancel={() => setEditing(false)} />
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
                onClick={() => setEditing(true)}
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
    </div>
  )
}
