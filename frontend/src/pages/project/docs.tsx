/**
 * Project workspace — Docs tab.
 *
 * Renders Markdown documentation from the project's docs content volume.
 * Files are fetched via GET /projects/:id/docs/:file_path.
 */

import { useState } from "react"
import { useParams } from "react-router-dom"
import { useProject } from "@/hooks/use-projects"
import { useDocsFile } from "@/hooks/use-docs"
import { MarkdownViewer } from "@/components/markdown-viewer"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

function DocsContent({
  projectId,
  filePath,
}: {
  projectId: string
  filePath: string
}) {
  const { data: content, isLoading, isError } = useDocsFile(projectId, filePath)

  if (isLoading) return <p className="text-muted-foreground text-sm">Loading…</p>
  if (isError || content === undefined) {
    return (
      <p className="text-destructive text-sm">
        Failed to load <code>{filePath}</code>.
      </p>
    )
  }

  return <MarkdownViewer content={content} />
}

export function ProjectDocsPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const { data: project, isLoading } = useProject(projectId ?? "")
  const [filePath, setFilePath] = useState("README.md")
  const [activeFile, setActiveFile] = useState("README.md")

  if (!projectId) return null

  const hasDocsRepo = !!project?.docs_repo_url

  if (isLoading) return <p className="text-muted-foreground">Loading…</p>

  if (!hasDocsRepo) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <p className="text-lg font-semibold">No docs volume configured</p>
        <p className="mt-2 text-sm text-muted-foreground">
          Set a <strong>Docs Repo URL</strong> in project Settings and sync to enable
          documentation.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* File path input */}
      <div className="flex gap-2 max-w-lg">
        <Input
          value={filePath}
          onChange={(e) => setFilePath(e.target.value)}
          placeholder="e.g. README.md"
          className="font-mono text-sm"
        />
        <Button
          variant="outline"
          size="sm"
          onClick={() => setActiveFile(filePath.trim())}
          disabled={!filePath.trim()}
        >
          Open
        </Button>
      </div>

      {/* Rendered file */}
      {activeFile && (
        <DocsContent projectId={projectId} filePath={activeFile} />
      )}
    </div>
  )
}
