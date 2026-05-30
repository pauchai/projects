import { useState, useEffect } from "react"
import { Lightbulb, Bug, Sparkles, HelpCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogClose,
} from "@/components/ui/dialog"
import { useAuthStore } from "@/stores/auth-store"
import { useSubmitFeature } from "@/hooks/use-features"
import { clientLogger } from "@/lib/client-logger"

const FEEDBACK_TYPES = [
  { value: "feature", label: "Feature", icon: Sparkles },
  { value: "bug", label: "Bug", icon: Bug },
  { value: "improvement", label: "Improvement", icon: Lightbulb },
  { value: "other", label: "Other", icon: HelpCircle },
] as const

export function FeedbackButton() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const [open, setOpen] = useState(false)
  const [type, setType] = useState<(typeof FEEDBACK_TYPES)[number]["value"]>("feature")
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [steps, setSteps] = useState("")
  const [attachLogs, setAttachLogs] = useState(true)
  const [logCount, setLogCount] = useState(0)
  const submitMutation = useSubmitFeature()

  useEffect(() => {
    clientLogger.init()
    const unsub = clientLogger.subscribe(() => setLogCount(clientLogger.getLogCount()))
    return unsub
  }, [])

  if (!isAuthenticated) return null

  const selectedType = FEEDBACK_TYPES.find((t) => t.value === type) ?? FEEDBACK_TYPES[0]

  const handleSubmit = async () => {
    if (!title.trim()) return

    let finalDescription = description.trim()
    if (type === "bug" && steps.trim()) {
      finalDescription += `\n\nSteps to reproduce:\n${steps.trim()}`
    }
    if (attachLogs) {
      finalDescription += `\n\n--- Browser logs ---\n${JSON.stringify(clientLogger.getSnapshot(), null, 2)}`
    }

    try {
      await submitMutation.mutateAsync({
        request_id: crypto.randomUUID(),
        title: `[${type}] ${title.trim()}`,
        description: finalDescription,
        category: type,
        priority: type === "bug" ? "high" : "normal",
      })
      setType("feature")
      setTitle("")
      setDescription("")
      setSteps("")
      setAttachLogs(true)
      setOpen(false)
    } catch {
      // handled by react query
    }
  }

  const SelectedIcon = selectedType.icon

  return (
    <>
      <div className="fixed bottom-6 right-6 z-40">
        <Button
          onClick={() => setOpen(true)}
          className="h-14 w-14 rounded-full shadow-lg"
          size="icon"
        >
          <SelectedIcon className="h-6 w-6" />
          <span className="sr-only">Submit feedback</span>
        </Button>
        {logCount > 0 && (
          <span className="absolute -top-1 -right-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-primary px-1 text-[11px] font-medium text-primary-foreground">
            {logCount}
          </span>
        )}
      </div>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Submit Feedback</DialogTitle>
            <DialogDescription>
              Help us improve the platform.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {/* Type selector */}
            <div>
              <label className="text-sm font-medium">Type</label>
              <div className="mt-1 grid grid-cols-2 gap-2">
                {FEEDBACK_TYPES.map((t) => {
                  const Icon = t.icon
                  const isActive = type === t.value
                  return (
                    <button
                      key={t.value}
                      type="button"
                      onClick={() => setType(t.value)}
                      className={`flex flex-1 items-center justify-center gap-1.5 rounded-md border px-3 py-2 text-sm transition-colors ${
                        isActive
                          ? "border-primary bg-primary/10 text-primary font-medium"
                          : "border-input text-muted-foreground hover:border-border hover:text-foreground"
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                      {t.label}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Title */}
            <div>
              <label className="text-sm font-medium">Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Brief title for your feedback"
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-ring"
                autoFocus
              />
            </div>

            {/* Description */}
            <div>
              <label className="text-sm font-medium">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe your feedback in detail"
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-ring"
                rows={3}
              />
            </div>

            {/* Steps to reproduce (only for bug) */}
            {type === "bug" && (
              <div>
                <label className="text-sm font-medium">Steps to reproduce</label>
                <textarea
                  value={steps}
                  onChange={(e) => setSteps(e.target.value)}
                  placeholder="1. Go to page..."
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-ring"
                  rows={3}
                />
              </div>
            )}

            {/* Attach logs checkbox */}
            <label className="flex items-start gap-3 rounded-md border border-input p-3 cursor-pointer hover:bg-accent transition-colors">
              <input
                type="checkbox"
                checked={attachLogs}
                onChange={(e) => setAttachLogs(e.target.checked)}
                className="mt-0.5"
              />
              <div>
                <span className="text-sm font-medium">Attach browser logs</span>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {logCount} entries recorded — helps diagnose issues
                </p>
              </div>
            </label>

            {/* Actions */}
            <div className="flex justify-end gap-2 pt-2">
              <DialogClose className="inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground transition-colors">
                Cancel
              </DialogClose>
              <Button
                onClick={handleSubmit}
                disabled={!title.trim() || submitMutation.isPending}
              >
                {submitMutation.isPending ? "Submitting..." : "Submit"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
