/**
 * Module workspace — Settings tab.
 * Visible to module master only (enforced by layout).
 *
 * Sections:
 * - Info (read-only)
 * - Content Volume: set repo_url, sync volume, sync lessons from manifest
 */

import { useState, useEffect } from "react"
import { useParams } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useModule } from "@/hooks/use-modules"
import {
  useSetRepoUrl,
  useSyncModuleVolume,
  useSyncLessonsFromManifest,
} from "@/hooks/use-lessons"

export function ModuleSettingsPage() {
  const { moduleId } = useParams<{ moduleId: string }>()
  const { data: module, isLoading, isError } = useModule(moduleId ?? "")

  const setRepoUrlMutation = useSetRepoUrl(moduleId ?? "")
  const syncVolumeMutation = useSyncModuleVolume(moduleId ?? "")
  const syncLessonsMutation = useSyncLessonsFromManifest(moduleId ?? "")

  const [repoUrl, setRepoUrl] = useState("")
  const [repoUrlInitialized, setRepoUrlInitialized] = useState(false)

  useEffect(() => {
    if (module && !repoUrlInitialized) {
      setRepoUrl(module.repo_url ?? "")
      setRepoUrlInitialized(true)
    }
  }, [module, repoUrlInitialized])

  if (isLoading) return <p className="text-muted-foreground">Loading…</p>
  if (isError || !module) return <p className="text-destructive">Module not found.</p>

  const handleSaveRepoUrl = () => {
    setRepoUrlMutation.mutate(repoUrl.trim() || null)
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <h2 className="text-xl font-bold">Module Settings</h2>

      {/* Info */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Info</CardTitle>
        </CardHeader>
        <CardContent className="text-sm space-y-2">
          <div>
            <span className="text-muted-foreground">Module ID: </span>
            <span className="font-mono text-xs">{module.module_id}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Title: </span>
            <span>{module.title}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Master: </span>
            <span className="font-mono text-xs">{module.master_id}</span>
          </div>
        </CardContent>
      </Card>

      {/* Content Volume */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Content Volume</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Repo URL */}
          <div className="space-y-2">
            <Label htmlFor="repoUrl">Repo URL</Label>
            <p className="text-xs text-muted-foreground">
              Git repository URL (include token for private repos:{" "}
              <code>https://&lt;token&gt;@github.com/…</code>).
            </p>
            <div className="flex gap-2">
              <Input
                id="repoUrl"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://<token>@github.com/org/repo.git"
                className="font-mono text-sm flex-1"
              />
              <Button
                variant="outline"
                size="sm"
                onClick={handleSaveRepoUrl}
                disabled={setRepoUrlMutation.isPending}
              >
                {setRepoUrlMutation.isPending ? "Saving…" : "Save"}
              </Button>
            </div>
            {setRepoUrlMutation.isSuccess && (
              <p className="text-xs text-emerald-600">Repo URL saved.</p>
            )}
            {setRepoUrlMutation.isError && (
              <p className="text-xs text-destructive">Failed to save repo URL.</p>
            )}
          </div>

          {/* Sync volume */}
          <div className="space-y-1">
            <p className="text-sm font-medium">Sync Volume</p>
            <p className="text-xs text-muted-foreground">
              Clone or pull the repository into the local volume.
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => syncVolumeMutation.mutate()}
              disabled={syncVolumeMutation.isPending || !module.repo_url}
            >
              {syncVolumeMutation.isPending ? "Syncing…" : "Sync Volume"}
            </Button>
            {syncVolumeMutation.isSuccess && (
              <p className="text-xs text-emerald-600">
                {syncVolumeMutation.data?.message ?? "Volume synced."}
              </p>
            )}
            {syncVolumeMutation.isError && (
              <p className="text-xs text-destructive">Sync failed.</p>
            )}
          </div>

          {/* Sync lessons from manifest */}
          <div className="space-y-1">
            <p className="text-sm font-medium">Import Lessons from Manifest</p>
            <p className="text-xs text-muted-foreground">
              Parse <code>lessons.json</code> in the volume and upsert lessons into the
              database.
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => syncLessonsMutation.mutate()}
              disabled={syncLessonsMutation.isPending || !module.repo_url}
            >
              {syncLessonsMutation.isPending ? "Importing…" : "Import Lessons"}
            </Button>
            {syncLessonsMutation.isSuccess && (
              <p className="text-xs text-emerald-600">Lessons imported.</p>
            )}
            {syncLessonsMutation.isError && (
              <p className="text-xs text-destructive">Import failed.</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
