import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Plus, Users } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useCommunities, useCreateCommunity } from "@/hooks/use-communities"
import { useAuthStore } from "@/stores/auth-store"

export function CommunitiesPage() {
  const { isAuthenticated } = useAuthStore()
  const { data: communities = [], isLoading } = useCommunities()
  const createCommunity = useCreateCommunity()
  const navigate = useNavigate()
  const [isCreating, setIsCreating] = useState(false)
  const [newName, setNewName] = useState("")
  const [newDescription, setNewDescription] = useState("")

  const handleCreate = async () => {
    if (!newName.trim()) return
    try {
      await createCommunity.mutateAsync({
        name: newName.trim(),
        description: newDescription.trim(),
      })
      setNewName("")
      setNewDescription("")
      setIsCreating(false)
    } catch {
      // handled by react query
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">Communities</h1>
        {isAuthenticated && (
          <Button onClick={() => setIsCreating(!isCreating)}>
            <Plus className="mr-2 h-4 w-4" />
            Create
          </Button>
        )}
      </div>

      {/* Create form */}
      {isCreating && (
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Name</label>
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="Community name"
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-ring"
                  autoFocus
                />
              </div>
              <div>
                <label className="text-sm font-medium">Description</label>
                <textarea
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  placeholder="Optional description"
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-ring"
                  rows={3}
                />
              </div>
              <div className="flex gap-2">
                <Button onClick={handleCreate} disabled={!newName.trim()}>
                  {createCommunity.isPending ? "Creating..." : "Create community"}
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => {
                    setIsCreating(false)
                    setNewName("")
                    setNewDescription("")
                  }}
                >
                  Cancel
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* List */}
      {isLoading ? (
        <p className="text-muted-foreground">Loading communities...</p>
      ) : communities.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-normal text-muted-foreground">
              No communities yet
            </CardTitle>
          </CardHeader>
          {isAuthenticated && (
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Create the first community to get started.
              </p>
            </CardContent>
          )}
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {communities.map((c) => (
            <Card
              key={c.community_id}
              className="cursor-pointer transition-colors hover:bg-accent"
              onClick={() => navigate(`/communities/${c.community_id}`)}
            >
              <CardHeader>
                <CardTitle className="text-lg">{c.name}</CardTitle>
              </CardHeader>
              <CardContent>
                {c.description && (
                  <p className="mb-3 text-sm text-muted-foreground line-clamp-2">
                    {c.description}
                  </p>
                )}
                <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                  <Users className="h-4 w-4" />
                  {c.member_count} member{c.member_count !== 1 ? "s" : ""}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
