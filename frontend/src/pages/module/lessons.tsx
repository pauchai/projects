/**
 * Module workspace — Lessons tab.
 *
 * Shows a list of lessons from the module's content volume.
 * Clicking a lesson renders its content_path file via MarkdownViewer.
 */

import { useState } from "react"
import { useParams } from "react-router-dom"
import { useLessons, useLessonFile } from "@/hooks/use-lessons"
import { MarkdownViewer } from "@/components/markdown-viewer"
import { Button } from "@/components/ui/button"
import type { LessonResponse } from "@/api/types"

function LessonContent({
  moduleId,
  lesson,
}: {
  moduleId: string
  lesson: LessonResponse
}) {
  const filePath = lesson.content_path
  const { data: content, isLoading, isError } = useLessonFile(moduleId, filePath)

  if (!filePath) {
    return (
      <p className="text-muted-foreground text-sm">
        No content file set for this lesson.
      </p>
    )
  }

  if (isLoading) return <p className="text-muted-foreground text-sm">Loading…</p>
  if (isError || content === undefined) {
    return <p className="text-destructive text-sm">Failed to load lesson content.</p>
  }

  return <MarkdownViewer content={content} />
}

export function ModuleLessonsPage() {
  const { moduleId } = useParams<{ moduleId: string }>()
  const { data: lessons, isLoading, isError } = useLessons(moduleId ?? "")
  const [selectedLesson, setSelectedLesson] = useState<LessonResponse | null>(null)

  if (!moduleId) return null

  if (isLoading) return <p className="text-muted-foreground">Loading lessons…</p>
  if (isError) return <p className="text-destructive">Failed to load lessons.</p>

  if (!lessons || lessons.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <p className="text-lg font-semibold">No lessons yet</p>
        <p className="mt-2 text-sm text-muted-foreground">
          Sync a content volume and import a <code>lessons.json</code> manifest to
          populate this module's lessons.
        </p>
      </div>
    )
  }

  return (
    <div className="flex gap-6">
      {/* Sidebar: lesson list */}
      <aside className="w-56 shrink-0">
        <h3 className="mb-3 text-sm font-semibold text-muted-foreground uppercase tracking-wide">
          Lessons
        </h3>
        <ul className="space-y-1">
          {[...lessons]
            .sort((a, b) => a.position - b.position)
            .map((lesson) => (
              <li key={lesson.lesson_id}>
                <Button
                  variant={
                    selectedLesson?.lesson_id === lesson.lesson_id ? "default" : "ghost"
                  }
                  size="sm"
                  className="w-full justify-start text-left"
                  onClick={() => setSelectedLesson(lesson)}
                >
                  <span className="mr-2 text-xs text-muted-foreground tabular-nums">
                    {lesson.position}.
                  </span>
                  {lesson.title}
                  {lesson.has_homework && (
                    <span
                      className="ml-auto text-xs text-amber-500"
                      title="Has homework"
                    >
                      HW
                    </span>
                  )}
                </Button>
              </li>
            ))}
        </ul>
      </aside>

      {/* Main: lesson content */}
      <main className="flex-1 min-w-0">
        {selectedLesson ? (
          <>
            <h2 className="mb-4 text-xl font-bold">{selectedLesson.title}</h2>
            <LessonContent moduleId={moduleId} lesson={selectedLesson} />
          </>
        ) : (
          <p className="text-muted-foreground">Select a lesson to read its content.</p>
        )}
      </main>
    </div>
  )
}
