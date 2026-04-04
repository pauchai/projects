import { Separator } from "@/components/ui/separator"
import { useAuthStore } from "@/stores/auth-store"
import { useSearchProjects } from "@/hooks/use-projects"
import { ProjectCard } from "@/components/project-card"

export function ProfilePage() {
  const { userId, email, displayName } = useAuthStore()

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
        <h1 className="text-2xl font-bold">{displayName ?? "User"}</h1>
        <p className="text-sm text-muted-foreground">{email}</p>
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
