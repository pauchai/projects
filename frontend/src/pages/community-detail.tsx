import { useParams } from "react-router-dom"
import { Users, Calendar } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useCommunity } from "@/hooks/use-communities"

export function CommunityDetailPage() {
  const { communityId } = useParams<{ communityId: string }>()
  const { data: community, isLoading } = useCommunity(communityId)

  if (isLoading) {
    return <p className="text-muted-foreground">Loading community...</p>
  }

  if (!community) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-normal text-muted-foreground">
            Community not found
          </CardTitle>
        </CardHeader>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{community.name}</h1>
        {community.description && (
          <p className="mt-1 text-muted-foreground">{community.description}</p>
        )}
        <div className="mt-3 flex items-center gap-4 text-sm text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <Users className="h-4 w-4" />
            {community.members.filter((m) => m.is_active).length} members
          </span>
          <span className="flex items-center gap-1.5">
            <Calendar className="h-4 w-4" />
            Created {new Date(community.created_at).toLocaleDateString()}
          </span>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="cursor-pointer transition-colors hover:bg-accent">
          <CardHeader>
            <CardTitle className="text-lg">Projects</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Browse and manage community projects
            </p>
          </CardContent>
        </Card>

        <Card className="cursor-pointer transition-colors hover:bg-accent">
          <CardHeader>
            <CardTitle className="text-lg">Needs</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Find roles to fill in projects
            </p>
          </CardContent>
        </Card>

        <Card className="cursor-pointer transition-colors hover:bg-accent">
          <CardHeader>
            <CardTitle className="text-lg">Marketplace</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Products and services from projects
            </p>
          </CardContent>
        </Card>

        <Card className="cursor-pointer transition-colors hover:bg-accent">
          <CardHeader>
            <CardTitle className="text-lg">Feature Requests</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Submit and vote on feature ideas
            </p>
          </CardContent>
        </Card>

        <Card className="cursor-pointer transition-colors hover:bg-accent">
          <CardHeader>
            <CardTitle className="text-lg">Members</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              View community members and roles
            </p>
          </CardContent>
        </Card>

        <Card className="cursor-pointer transition-colors hover:bg-accent">
          <CardHeader>
            <CardTitle className="text-lg">Fund</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Community treasury and distributions
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
