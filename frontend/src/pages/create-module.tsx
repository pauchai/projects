import { useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { useCreateModule } from "@/hooks/use-modules"
import { ApiError } from "@/api/client"

export function CreateModulePage() {
  const navigate = useNavigate()
  const { projectId } = useParams<{ projectId: string }>()
  const createModule = useCreateModule()
  const [moduleId, setModuleId] = useState<string>(() => crypto.randomUUID())
  const [title, setTitle] = useState("")
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (!title.trim()) {
      setError("Title is required.")
      return
    }
    try {
      await createModule.mutateAsync({ module_id: moduleId, title: title.trim() })
      navigate(`/projects/${projectId}/modules/${moduleId}/overview`)
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to create module.")
    }
  }

  return (
    <div className="max-w-md">
      <h1 className="text-2xl font-bold mb-6">Create a Module</h1>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">New Learning Module</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1">
              <Label htmlFor="moduleId">Module ID</Label>
              <Input
                id="moduleId"
                value={moduleId}
                readOnly
                className="font-mono text-sm bg-muted"
              />
              <p className="text-xs text-muted-foreground">
                Auto-generated.{" "}
                <button
                  type="button"
                  className="underline"
                  onClick={() => setModuleId(crypto.randomUUID())}
                >
                  Regenerate
                </button>
              </p>
            </div>

            <div className="space-y-1">
              <Label htmlFor="title">Title</Label>
              <Input
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Introduction to TypeScript"
              />
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <Button type="submit" className="w-full" disabled={createModule.isPending}>
              {createModule.isPending ? "Creating…" : "Create Module"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
