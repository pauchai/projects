import { useState } from "react"
import { Lightbulb } from "lucide-react"
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

export function FloatingFeatureButton() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const [open, setOpen] = useState(false)
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const submitMutation = useSubmitFeature()

  if (!isAuthenticated) return null

  const handleSubmit = async () => {
    if (!title.trim()) return
    try {
      await submitMutation.mutateAsync({
        request_id: crypto.randomUUID(),
        title: title.trim(),
        description: description.trim(),
      })
      setTitle("")
      setDescription("")
      setOpen(false)
    } catch {
      // handled by react query
    }
  }

  return (
    <>
      <Button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-40 h-14 w-14 rounded-full shadow-lg"
        size="icon"
      >
        <Lightbulb className="h-6 w-6" />
        <span className="sr-only">Submit feature request</span>
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Submit Feature Request</DialogTitle>
            <DialogDescription>
              Suggest a new feature for the platform.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Brief title for your idea"
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-ring"
                autoFocus
              />
            </div>

            <div>
              <label className="text-sm font-medium">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe what you'd like to see"
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-ring"
                rows={4}
              />
            </div>

            <div className="flex justify-end gap-2">
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
