/**
 * FileTree — sidebar file navigator for docs volumes.
 *
 * Receives a flat list of relative file paths and renders them grouped by
 * directory. Clicking a file calls onSelect(path).
 *
 * Example input:
 *   ["README.md", "guides/setup.md", "guides/deploy.md", "api.md"]
 *
 * Renders:
 *   📄 README.md
 *   📄 api.md
 *   📁 guides/
 *     📄 setup.md
 *     📄 deploy.md
 */

import { useState } from "react"
import { ChevronDown, ChevronRight, FileText, Folder } from "lucide-react"
import { cn } from "@/lib/utils"

// ---------------------------------------------------------------------------
// Tree building
// ---------------------------------------------------------------------------

interface FileNode {
  name: string
  path: string // full relative path from volume root
}

interface DirNode {
  name: string
  dirs: Map<string, DirNode>
  files: FileNode[]
}

function buildTree(paths: string[]): DirNode {
  const root: DirNode = { name: "", dirs: new Map(), files: [] }

  for (const p of paths) {
    const parts = p.split("/")
    let node = root
    for (let i = 0; i < parts.length - 1; i++) {
      const dir = parts[i]
      if (!node.dirs.has(dir)) {
        node.dirs.set(dir, { name: dir, dirs: new Map(), files: [] })
      }
      node = node.dirs.get(dir)!
    }
    node.files.push({ name: parts[parts.length - 1], path: p })
  }

  return root
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface FileItemProps {
  file: FileNode
  activeFile: string | null
  onSelect: (path: string) => void
  depth: number
}

function FileItem({ file, activeFile, onSelect, depth }: FileItemProps) {
  const isActive = file.path === activeFile
  return (
    <button
      type="button"
      onClick={() => onSelect(file.path)}
      style={{ paddingLeft: `${depth * 12 + 8}px` }}
      className={cn(
        "flex w-full items-center gap-1.5 rounded py-1 pr-2 text-left text-sm transition-colors",
        isActive
          ? "bg-primary/10 text-primary font-medium"
          : "text-muted-foreground hover:bg-muted hover:text-foreground",
      )}
    >
      <FileText className="h-3.5 w-3.5 shrink-0" />
      <span className="truncate">{file.name}</span>
    </button>
  )
}

interface DirItemProps {
  dir: DirNode
  activeFile: string | null
  onSelect: (path: string) => void
  depth: number
}

function DirItem({ dir, activeFile, onSelect, depth }: DirItemProps) {
  const [open, setOpen] = useState(true)
  const ChevronIcon = open ? ChevronDown : ChevronRight

  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
        className="flex w-full items-center gap-1.5 rounded py-1 pr-2 text-left text-sm font-medium text-foreground hover:bg-muted transition-colors"
      >
        <ChevronIcon className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
        <Folder className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
        <span className="truncate">{dir.name}</span>
      </button>
      {open && (
        <TreeLevel node={dir} activeFile={activeFile} onSelect={onSelect} depth={depth + 1} />
      )}
    </div>
  )
}

interface TreeLevelProps {
  node: DirNode
  activeFile: string | null
  onSelect: (path: string) => void
  depth: number
}

function TreeLevel({ node, activeFile, onSelect, depth }: TreeLevelProps) {
  return (
    <>
      {[...node.dirs.values()].map((dir) => (
        <DirItem
          key={dir.name}
          dir={dir}
          activeFile={activeFile}
          onSelect={onSelect}
          depth={depth}
        />
      ))}
      {node.files.map((file) => (
        <FileItem
          key={file.path}
          file={file}
          activeFile={activeFile}
          onSelect={onSelect}
          depth={depth}
        />
      ))}
    </>
  )
}

// ---------------------------------------------------------------------------
// FileTree (public)
// ---------------------------------------------------------------------------

interface FileTreeProps {
  files: string[]
  activeFile: string | null
  onSelect: (path: string) => void
  className?: string
}

export function FileTree({ files, activeFile, onSelect, className }: FileTreeProps) {
  const tree = buildTree(files)

  if (files.length === 0) {
    return (
      <p className="px-2 py-3 text-xs text-muted-foreground">No files found.</p>
    )
  }

  return (
    <nav className={cn("select-none", className)}>
      <TreeLevel node={tree} activeFile={activeFile} onSelect={onSelect} depth={0} />
    </nav>
  )
}
