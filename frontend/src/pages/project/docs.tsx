/**
 * Project workspace — Docs tab.
 *
 * Renders Markdown documentation from the project's docs content volume.
 * Internal links (.md) and [[WikiLinks]] open in-page via onNavigate.
 * External links open in a new tab.
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
  onNavigate,
}: {
  projectId: string
  filePath: string
  onNavigate: (path: string) => void
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

  return (
    <MarkdownViewer
      content={content}
      currentFile={filePath}
      onNavigate={onNavigate}
    />
  )
}

export function ProjectDocsPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const { data: project, isLoading } = useProject(projectId ?? "")
  const [inputValue, setInputValue] = useState("README.md")
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

  const handleNavigate = (path: string) => {
    setActiveFile(path)
    setInputValue(path)
  }

  return (
    <div className="space-y-4">
      {/* File path bar */}
      <div className="flex gap-2 max-w-lg">
        <Input
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="e.g. README.md"
          className="font-mono text-sm"
          onKeyDown={(e) => {
            if (e.key === "Enter") handleNavigate(inputValue.trim())
          }}
        />
        <Button
          variant="outline"
          size="sm"
          onClick={() => handleNavigate(inputValue.trim())}
          disabled={!inputValue.trim()}
        >
          Open
        </Button>
      </div>

      {/* Rendered file */}
      {activeFile && (
        <DocsContent
          projectId={projectId}
          filePath={activeFile}
          onNavigate={handleNavigate}
        />
      )}
    </div>
  )
}
