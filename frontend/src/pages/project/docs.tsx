/**
 * Project workspace — Docs tab.
 *
 * Layout: fixed sidebar (FileTree) on the left, rendered Markdown on the right.
 * Internal links and [[WikiLinks]] navigate in-page via onNavigate.
 */

import { useState } from "react"
import { useParams } from "react-router-dom"
import { useProject } from "@/hooks/use-projects"
import { useDocsFile, useDocsTree } from "@/hooks/use-docs"
import { MarkdownViewer } from "@/components/markdown-viewer"
import { FileTree } from "@/components/file-tree"

// ---------------------------------------------------------------------------
// Docs content pane
// ---------------------------------------------------------------------------

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

  if (isLoading) {
    return <p className="text-muted-foreground text-sm">Loading…</p>
  }
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

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export function ProjectDocsPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const { data: project, isLoading: projectLoading } = useProject(projectId ?? "")
  const { data: files, isLoading: treeLoading } = useDocsTree(projectId ?? "")

  const [activeFile, setActiveFile] = useState<string | null>(null)

  if (!projectId) return null
  if (projectLoading) return <p className="text-muted-foreground">Loading…</p>

  const hasDocsRepo = !!project?.docs_repo_url

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
  }

  // Auto-select first file once tree loads
  const resolvedActive =
    activeFile ?? (files && files.length > 0 ? files[0] : null)

  return (
    <div className="flex h-full gap-0 overflow-hidden rounded-lg border border-border">
      {/* Sidebar */}
      <aside className="w-56 shrink-0 border-r border-border bg-muted/30">
        <div className="px-3 py-2 border-b border-border">
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Files
          </p>
        </div>
        <div className="overflow-y-auto h-[calc(100%-36px)]">
          <div className="py-1">
            {treeLoading ? (
              <p className="px-3 py-2 text-xs text-muted-foreground">Loading…</p>
            ) : (
              <FileTree
                files={files ?? []}
                activeFile={resolvedActive}
                onSelect={handleNavigate}
              />
            )}
          </div>
        </div>
      </aside>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="px-8 py-6 max-w-3xl">
          {resolvedActive ? (
            <DocsContent
              projectId={projectId}
              filePath={resolvedActive}
              onNavigate={handleNavigate}
            />
          ) : (
            <p className="text-muted-foreground text-sm">
              Select a file from the sidebar.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
