/**
 * Module workspace — Topics tab.
 * List topics; module master can add/remove topics.
 * Ported from pages/module-detail.tsx.
 */

import { useState } from "react"
import { useParams } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator"
import { useModule, useAddTopic, useRemoveTopic } from "@/hooks/use-modules"
import { useAuthStore } from "@/stores/auth-store"
import { ApiError } from "@/api/client"

export function ModuleTopicsPage() {
  const { moduleId } = useParams<{ moduleId: string }>()
  const userId = useAuthStore((s) => s.userId)

  const { data: module, isLoading, isError } = useModule(moduleId ?? "")
  const addTopic = useAddTopic(moduleId ?? "")
  const removeTopic = useRemoveTopic(moduleId ?? "")

  const [topicTitle, setTopicTitle] = useState("")
  const [topicPosition, setTopicPosition] = useState("")
  const [topicDescription, setTopicDescription] = useState("")
  const [formError, setFormError] = useState<string | null>(null)
  const [formSuccess, setFormSuccess] = useState<string | null>(null)

  if (isLoading) return <p className="text-muted-foreground">Loading module…</p>
  if (isError || !module) return <p className="text-destructive">Module not found.</p>

  const isMaster = userId === module.master_id
  const sortedTopics = [...module.topics].sort((a, b) => a.position - b.position)

  const handleAddTopic = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)
    setFormSuccess(null)

    if (!topicTitle.trim()) {
      setFormError("Title is required.")
      return
    }
    const position = parseInt(topicPosition, 10)
    if (isNaN(position) || position < 0) {
      setFormError("Position must be a non-negative integer.")
      return
    }

    try {
      await addTopic.mutateAsync({
        topic_id: crypto.randomUUID(),
        title: topicTitle.trim(),
        position,
        description: topicDescription.trim(),
      })
      setTopicTitle("")
      setTopicPosition("")
      setTopicDescription("")
      setFormSuccess("Topic added.")
    } catch (err) {
      setFormError(err instanceof ApiError ? err.detail : "Failed to add topic.")
    }
  }

  const handleRemoveTopic = async (topicId: string) => {
    try {
      await removeTopic.mutateAsync(topicId)
    } catch {
      // silently ignore
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">
            Topics{" "}
            <Badge variant="secondary" className="ml-1">
              {module.topic_count}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {sortedTopics.length === 0 && (
            <p className="text-sm text-muted-foreground">No topics yet.</p>
          )}
          {sortedTopics.length > 0 && (
            <ol className="space-y-2">
              {sortedTopics.map((topic) => (
                <li
                  key={topic.topic_id}
                  className="flex items-start justify-between gap-4 border rounded-md px-3 py-2"
                >
                  <div className="space-y-0.5 min-w-0">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="shrink-0">
                        #{topic.position}
                      </Badge>
                      <span className="font-medium truncate">{topic.title}</span>
                    </div>
                    {topic.description && (
                      <p className="text-xs text-muted-foreground">{topic.description}</p>
                    )}
                  </div>
                  {isMaster && (
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-destructive shrink-0"
                      onClick={() => handleRemoveTopic(topic.topic_id)}
                      disabled={removeTopic.isPending}
                    >
                      Remove
                    </Button>
                  )}
                </li>
              ))}
            </ol>
          )}
        </CardContent>
      </Card>

      {isMaster && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Add Topic</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAddTopic} className="space-y-3">
              <div className="space-y-1">
                <Label htmlFor="topicTitle">Title</Label>
                <Input
                  id="topicTitle"
                  value={topicTitle}
                  onChange={(e) => setTopicTitle(e.target.value)}
                  placeholder="e.g. Variables & Types"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="topicPosition">Position</Label>
                <Input
                  id="topicPosition"
                  type="number"
                  min={0}
                  value={topicPosition}
                  onChange={(e) => setTopicPosition(e.target.value)}
                  placeholder="0"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="topicDescription">Description (optional)</Label>
                <Input
                  id="topicDescription"
                  value={topicDescription}
                  onChange={(e) => setTopicDescription(e.target.value)}
                  placeholder="Brief description of this topic"
                />
              </div>

              {formError && <p className="text-sm text-destructive">{formError}</p>}
              {formSuccess && <p className="text-sm text-green-600">{formSuccess}</p>}

              <Separator />
              <Button type="submit" disabled={addTopic.isPending}>
                {addTopic.isPending ? "Adding…" : "Add Topic"}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
