/**
 * Complaints page — bilingual.
 * Shows complaints where the current user needs to vote,
 * and allows filing a new complaint against a deal counterparty.
 */

import { useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  useCastVote,
  useEscalateComplaint,
  useFileComplaint,
  useMyComplaints,
} from "@/hooks/use-guarantorship"
import type { ComplaintCreate, ComplaintResponse } from "@/api/types"

// ─── Status badge ─────────────────────────────────────────────────────────────

function ComplaintStatusBadge({ status }: { status: string }) {
  const variant =
    status === "resolved"
      ? "default"
      : status === "escalated"
      ? "destructive"
      : "secondary"
  return <Badge variant={variant}>{status}</Badge>
}

// ─── File Complaint dialog ────────────────────────────────────────────────────

function FileComplaintDialog() {
  const [open, setOpen] = useState(false)
  const [dealId, setDealId] = useState("")
  const [againstId, setAgainstId] = useState("")
  const [description, setDescription] = useState("")
  const mutation = useFileComplaint()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const body: ComplaintCreate = {
      deal_id: dealId.trim(),
      against_id: againstId.trim(),
      description: description.trim(),
    }
    mutation.mutate(body, {
      onSuccess: () => {
        setOpen(false)
        setDealId("")
        setAgainstId("")
        setDescription("")
      },
    })
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger>
        <Button size="sm" variant="destructive">
          File complaint / Подать жалобу
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>File a Complaint / Подать жалобу</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4 pt-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="deal-id">Deal ID / ID сделки</Label>
            <Input
              id="deal-id"
              value={dealId}
              onChange={(e) => setDealId(e.target.value)}
              placeholder="Enter deal ID..."
              required
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="against-id">
              Against user ID / ID нарушителя
            </Label>
            <Input
              id="against-id"
              value={againstId}
              onChange={(e) => setAgainstId(e.target.value)}
              placeholder="Enter user ID..."
              required
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="complaint-description">
              Description / Описание
            </Label>
            <Textarea
              id="complaint-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the issue..."
              rows={4}
              required
            />
          </div>
          {mutation.isError && (
            <p className="text-sm text-destructive">
              {String((mutation.error as Error)?.message ?? "Error")}
            </p>
          )}
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? "Submitting…" : "Submit / Отправить"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ─── Complaint card ───────────────────────────────────────────────────────────

const VERDICT_OPTIONS = [
  { value: "compensate_initiator", label: "Compensate initiator / Компенсировать инициатору" },
  { value: "compensate_counterparty", label: "Compensate counterparty / Компенсировать контрагенту" },
  { value: "dismiss", label: "Dismiss / Отклонить" },
]

function ComplaintCard({ complaint }: { complaint: ComplaintResponse }) {
  const voteMutation = useCastVote()
  const escalateMutation = useEscalateComplaint()

  const canVote =
    complaint.status === "voting" || complaint.status === "escalated"
  const canEscalate = complaint.status === "voting"

  return (
    <div className="rounded-md border p-4 flex flex-col gap-3 text-sm">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-0.5">
          <span className="font-medium">
            Deal: <code className="text-xs">{complaint.deal_id}</code>
          </span>
          <span className="text-xs text-muted-foreground">
            Filed by: <code>{complaint.filed_by_id}</code> against{" "}
            <code>{complaint.against_id}</code>
          </span>
        </div>
        <ComplaintStatusBadge status={complaint.status} />
      </div>

      {/* Description */}
      <p className="text-muted-foreground italic text-xs">
        "{complaint.description}"
      </p>

      {/* Verdict */}
      {complaint.verdict && (
        <p className="text-xs font-medium">
          Verdict / Решение:{" "}
          <Badge variant="default">{complaint.verdict}</Badge>
        </p>
      )}

      {/* Deadline */}
      {complaint.voting_deadline && complaint.status !== "resolved" && (
        <p className="text-xs text-muted-foreground">
          Deadline / Срок голосования:{" "}
          {new Date(complaint.voting_deadline).toLocaleDateString()}
        </p>
      )}

      {/* Escalation level */}
      {complaint.escalation_level > 0 && (
        <p className="text-xs text-muted-foreground">
          Escalation level / Уровень эскалации: {complaint.escalation_level}
        </p>
      )}

      {/* Vote buttons */}
      {canVote && (
        <div className="flex flex-col gap-2">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Cast your vote / Проголосовать
          </p>
          <div className="flex flex-wrap gap-2">
            {VERDICT_OPTIONS.map((opt) => (
              <Button
                key={opt.value}
                size="sm"
                variant="outline"
                disabled={voteMutation.isPending}
                onClick={() =>
                  voteMutation.mutate({
                    complaintId: complaint.complaint_id,
                    vote: opt.value,
                  })
                }
              >
                {opt.label}
              </Button>
            ))}
          </div>
          {voteMutation.isError && (
            <p className="text-xs text-destructive">
              {String((voteMutation.error as Error)?.message ?? "Error")}
            </p>
          )}
        </div>
      )}

      {/* Escalate button */}
      {canEscalate && (
        <div>
          <Button
            size="sm"
            variant="outline"
            disabled={escalateMutation.isPending}
            onClick={() => escalateMutation.mutate(complaint.complaint_id)}
          >
            {escalateMutation.isPending
              ? "Escalating…"
              : "Escalate / Эскалировать"}
          </Button>
          {escalateMutation.isError && (
            <p className="text-xs text-destructive mt-1">
              {String((escalateMutation.error as Error)?.message ?? "Error")}
            </p>
          )}
        </div>
      )}
    </div>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export function ComplaintsPage() {
  const complaintsQuery = useMyComplaints()

  return (
    <div className="container py-8 max-w-2xl flex flex-col gap-8">

      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold">
          Complaints / Жалобы
        </h1>
        <div className="mt-3 flex flex-col gap-2 text-sm leading-relaxed text-muted-foreground">
          <p>
            When a deal goes wrong, any participant can file a complaint.
            Guarantors of both parties vote on the verdict. Unanimous consensus
            resolves the complaint; otherwise it can be escalated to
            guarantors-of-guarantors.
          </p>
          <p>
            Если сделка нарушена, любой участник может подать жалобу. Поручители
            обеих сторон голосуют по делу. Единогласный консенсус закрывает
            жалобу; в противном случае она может быть эскалирована до
            поручителей поручителей.
          </p>
        </div>
      </div>

      {/* File complaint */}
      <section className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium">
            File a complaint / Подать жалобу
          </h2>
          <FileComplaintDialog />
        </div>
      </section>

      {/* Active complaints */}
      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-medium">
          Complaints requiring your vote / Жалобы, требующие вашего голоса
        </h2>

        {complaintsQuery.isLoading && (
          <p className="text-sm text-muted-foreground">Loading… / Загрузка…</p>
        )}

        {complaintsQuery.isError && (
          <p className="text-sm text-destructive">
            Failed to load complaints. / Не удалось загрузить жалобы.
          </p>
        )}

        {complaintsQuery.data?.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No active complaints. / Активных жалоб нет.
          </p>
        )}

        {complaintsQuery.data && complaintsQuery.data.length > 0 && (
          <div className="flex flex-col gap-3">
            {complaintsQuery.data.map((c: ComplaintResponse) => (
              <ComplaintCard key={c.complaint_id} complaint={c} />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
