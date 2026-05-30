/**
 * MarkdownViewer — renders Markdown (from a string) in Obsidian-like style.
 *
 * Features:
 * - GitHub-flavoured Markdown (tables, strikethrough, task lists)
 * - Math (KaTeX via remark-math + rehype-katex)
 * - Syntax highlighting (rehype-highlight)
 * - Wiki-style links [[Page]] — calls onNavigate("page.md") when clicked
 * - Obsidian callouts: > [!note], > [!warning], > [!tip], > [!danger]
 * - Internal .md links open in-page via onNavigate; external links open in new tab
 *
 * Usage:
 *   <MarkdownViewer content={markdownString} />
 *   <MarkdownViewer content={markdownString} onNavigate={(path) => setActiveFile(path)} />
 */

import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import remarkMath from "remark-math"
import remarkWikiLink from "remark-wiki-link"
import rehypeKatex from "rehype-katex"
import rehypeHighlight from "rehype-highlight"
import "katex/dist/katex.min.css"
import "highlight.js/styles/github-dark.css"

// ---------------------------------------------------------------------------
// Callout preprocessing
// ---------------------------------------------------------------------------

const CALLOUT_TYPES = ["note", "tip", "warning", "danger", "info", "success"] as const
type CalloutType = (typeof CALLOUT_TYPES)[number]

const CALLOUT_RE = /^> \[!(note|tip|warning|danger|info|success)\](.*)\n((?:> .*\n?)*)/gim

function preprocessCallouts(md: string): string {
  return md.replace(CALLOUT_RE, (_match, type, title, body) => {
    const cleanBody = body
      .split("\n")
      .map((line: string) => line.replace(/^> /, ""))
      .join("\n")
    return `<callout type="${type}" title="${title.trim()}">\n${cleanBody}</callout>\n`
  })
}

// ---------------------------------------------------------------------------
// Callout styling
// ---------------------------------------------------------------------------

const CALLOUT_STYLES: Record<CalloutType, { border: string; bg: string; icon: string }> = {
  note:    { border: "border-blue-500",    bg: "bg-blue-50 dark:bg-blue-950/30",       icon: "ℹ" },
  tip:     { border: "border-green-500",   bg: "bg-green-50 dark:bg-green-950/30",     icon: "💡" },
  warning: { border: "border-amber-500",   bg: "bg-amber-50 dark:bg-amber-950/30",     icon: "⚠" },
  danger:  { border: "border-red-500",     bg: "bg-red-50 dark:bg-red-950/30",         icon: "🔴" },
  info:    { border: "border-sky-500",     bg: "bg-sky-50 dark:bg-sky-950/30",         icon: "📌" },
  success: { border: "border-emerald-500", bg: "bg-emerald-50 dark:bg-emerald-950/30", icon: "✅" },
}

// ---------------------------------------------------------------------------
// Link helpers
// ---------------------------------------------------------------------------

function isExternal(href: string): boolean {
  return /^https?:\/\//i.test(href)
}

/**
 * Resolves a relative link against the current file's directory.
 * e.g. currentFile="docs/intro.md", href="architecture.md" → "docs/architecture.md"
 */
function resolveRelative(href: string, currentFile?: string): string {
  if (!currentFile || isExternal(href) || href.startsWith("/")) return href
  const dir = currentFile.includes("/")
    ? currentFile.slice(0, currentFile.lastIndexOf("/") + 1)
    : ""
  return dir + href
}

// ---------------------------------------------------------------------------
// Component factory — receives onNavigate + currentFile at render time
// ---------------------------------------------------------------------------

/* eslint-disable @typescript-eslint/no-explicit-any */
function buildComponents(
  onNavigate?: (path: string) => void,
  currentFile?: string,
): Record<string, React.ComponentType<any>> {
  return {
    // Callout block (custom tag injected by preprocessCallouts)
    callout: ({ node: _node, ...props }: any) => {
      const type = (props.type ?? "note") as CalloutType
      const title = props.title as string | undefined
      const style = CALLOUT_STYLES[type] ?? CALLOUT_STYLES.note
      return (
        <div
          className={[
            "my-4 rounded-md border-l-4 px-4 py-3",
            style.border,
            style.bg,
          ].join(" ")}
        >
          {title && (
            <div className="mb-1 flex items-center gap-2 font-semibold text-sm uppercase tracking-wide">
              <span>{style.icon}</span>
              <span>{title}</span>
            </div>
          )}
          <div className="text-sm">{props.children}</div>
        </div>
      )
    },

    // Links — internal .md → onNavigate (in-page); external → new tab
    a: ({ children, href, ...props }: any) => {
      const resolvedHref = resolveRelative(href ?? "", currentFile)

      if (!isExternal(resolvedHref) && onNavigate) {
        return (
          <a
            href="#"
            onClick={(e) => {
              e.preventDefault()
              onNavigate(resolvedHref)
            }}
            className="text-primary underline underline-offset-4 hover:opacity-80 cursor-pointer"
            {...props}
          >
            {children}
          </a>
        )
      }

      return (
        <a
          href={resolvedHref}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary underline underline-offset-4 hover:opacity-80"
          {...props}
        >
          {children}
        </a>
      )
    },

    // Code blocks
    pre: ({ children, ...props }: any) => (
      <pre
        className="my-4 overflow-x-auto rounded-md bg-muted p-4 text-sm leading-relaxed"
        {...props}
      >
        {children}
      </pre>
    ),

    // Inline code
    code: ({ inline, children, ...props }: any) =>
      inline ? (
        <code className="rounded bg-muted px-1 py-0.5 font-mono text-sm" {...props}>
          {children}
        </code>
      ) : (
        <code className="font-mono text-sm" {...props}>
          {children}
        </code>
      ),

    // Headings
    h1: ({ children, ...props }: any) => (
      <h1 className="mt-8 mb-4 text-3xl font-bold tracking-tight" {...props}>{children}</h1>
    ),
    h2: ({ children, ...props }: any) => (
      <h2 className="mt-6 mb-3 text-2xl font-semibold" {...props}>{children}</h2>
    ),
    h3: ({ children, ...props }: any) => (
      <h3 className="mt-5 mb-2 text-xl font-semibold" {...props}>{children}</h3>
    ),
    h4: ({ children, ...props }: any) => (
      <h4 className="mt-4 mb-2 text-lg font-medium" {...props}>{children}</h4>
    ),

    // Paragraphs
    p: ({ children, ...props }: any) => (
      <p className="my-3 leading-7" {...props}>{children}</p>
    ),

    // Lists
    ul: ({ children, ...props }: any) => (
      <ul className="my-3 ml-6 list-disc space-y-1" {...props}>{children}</ul>
    ),
    ol: ({ children, ...props }: any) => (
      <ol className="my-3 ml-6 list-decimal space-y-1" {...props}>{children}</ol>
    ),
    li: ({ children, ...props }: any) => (
      <li className="leading-7" {...props}>{children}</li>
    ),

    // Blockquote (fallback for non-callout blockquotes)
    blockquote: ({ children, ...props }: any) => (
      <blockquote
        className="my-4 border-l-4 border-muted-foreground/30 pl-4 text-muted-foreground italic"
        {...props}
      >
        {children}
      </blockquote>
    ),

    // Horizontal rule
    hr: (props: any) => <hr className="my-6 border-border" {...props} />,

    // Tables
    table: ({ children, ...props }: any) => (
      <div className="my-4 overflow-x-auto">
        <table className="w-full border-collapse text-sm" {...props}>{children}</table>
      </div>
    ),
    th: ({ children, ...props }: any) => (
      <th className="border border-border bg-muted px-3 py-2 text-left font-semibold" {...props}>
        {children}
      </th>
    ),
    td: ({ children, ...props }: any) => (
      <td className="border border-border px-3 py-2" {...props}>{children}</td>
    ),

    // Images
    img: ({ src, alt, ...props }: any) => (
      <img src={src} alt={alt ?? ""} className="my-4 max-w-full rounded-md" {...props} />
    ),
  }
}
/* eslint-enable @typescript-eslint/no-explicit-any */

// ---------------------------------------------------------------------------
// MarkdownViewer
// ---------------------------------------------------------------------------

interface MarkdownViewerProps {
  content: string
  className?: string
  /** Path of the currently displayed file — used to resolve relative links. */
  currentFile?: string
  /** Called when an internal .md link or [[WikiLink]] is clicked. */
  onNavigate?: (path: string) => void
}

export function MarkdownViewer({
  content,
  className = "",
  currentFile,
  onNavigate,
}: MarkdownViewerProps) {
  const processed = preprocessCallouts(content)
  const components = buildComponents(onNavigate, currentFile)

  return (
    <div className={["prose-reset text-foreground", className].join(" ")}>
      <ReactMarkdown
        remarkPlugins={[
          remarkGfm,
          remarkMath,
          [
            remarkWikiLink,
            {
              // [[Architecture]] → "architecture.md"
              pageResolver: (name: string) => [
                name.toLowerCase().replace(/\s+/g, "-") + ".md",
              ],
              hrefTemplate: (permalink: string) => permalink,
              aliasDivider: "|",
            },
          ],
        ]}
        rehypePlugins={[rehypeKatex, rehypeHighlight]}
        components={components}
      >
        {processed}
      </ReactMarkdown>
    </div>
  )
}
