import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  useConsultationRequests,
  useSubmitConsultationRequest,
  useStartNegotiation,
  useAssignAppointment,
} from "@/hooks/use-schedule"
import type { ConsultationRequestResponse } from "@/api/types"

const STATUS_LABELS: Record<ConsultationRequestResponse["status"], string> = {
  pending: "Pending",
  negotiating: "Negotiating",
  confirmed: "Confirmed",
  cancelled: "Cancelled",
}

const STATUS_COLORS: Record<ConsultationRequestResponse["status"], string> = {
  pending: "bg-yellow-100 text-yellow-800",
  negotiating: "bg-blue-100 text-blue-800",
  confirmed: "bg-green-100 text-green-800",
  cancelled: "bg-gray-100 text-gray-500",
}

function RequestCard({ request }: { request: ConsultationRequestResponse }) {
  const startNegotiation = useStartNegotiation()
  const assignAppointment = useAssignAppointment()
  const [scheduledAt, setScheduledAt] = useState("")

  function handleNegotiate() {
    startNegotiation.mutate(request.request_id)
  }

  function handleAssign(e: React.FormEvent) {
    e.preventDefault()
    assignAppointment.mutate({
      requestId: request.request_id,
      data: { scheduled_at: new Date(scheduledAt).toISOString() },
    })
  }

  return (
    <div className="rounded-lg border p-4 shadow-sm">
      <div className="mb-2 flex items-start justify-between gap-2">
        <div>
          <p className="font-semibold">{request.student_name}</p>
          <p className="mt-1 text-sm text-gray-700">{request.request_text}</p>
        </div>
        <span
          className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[request.status]}`}
        >
          {STATUS_LABELS[request.status]}
        </span>
      </div>

      {request.recommended_curator_ids.length > 0 && (
        <p className="mt-2 text-xs text-gray-500">
          Recommended curators:{" "}
          <span className="font-mono">{request.recommended_curator_ids.join(", ")}</span>
        </p>
      )}

      {request.status === "pending" && request.recommended_curator_ids.length > 0 && (
        <Button
          size="sm"
          className="mt-3"
          onClick={handleNegotiate}
          disabled={startNegotiation.isPending}
        >
          {startNegotiation.isPending ? "Starting..." : "Start negotiation"}
        </Button>
      )}

      {request.status === "negotiating" && (
        <form onSubmit={handleAssign} className="mt-3 flex items-end gap-2">
          <div>
            <label className="block text-xs text-gray-500">Schedule at</label>
            <Input
              type="datetime-local"
              value={scheduledAt}
              onChange={(e) => setScheduledAt(e.target.value)}
              required
              className="text-sm"
            />
          </div>
          <Button type="submit" size="sm" disabled={assignAppointment.isPending}>
            {assignAppointment.isPending ? "Assigning..." : "Assign"}
          </Button>
        </form>
      )}

      {startNegotiation.isError && (
        <p className="mt-1 text-xs text-red-600">{String(startNegotiation.error)}</p>
      )}
      {assignAppointment.isError && (
        <p className="mt-1 text-xs text-red-600">{String(assignAppointment.error)}</p>
      )}
    </div>
  )
}

function NewRequestForm({ onClose }: { onClose: () => void }) {
  const submitRequest = useSubmitConsultationRequest()
  const [studentName, setStudentName] = useState("")
  const [requestText, setRequestText] = useState("")

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    submitRequest.mutate(
      { student_name: studentName, request_text: requestText },
      { onSuccess: onClose },
    )
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mb-6 flex flex-col gap-3 rounded-lg border p-4"
    >
      <h2 className="font-semibold">New consultation request</h2>
      <div>
        <label className="block text-sm font-medium">Student name</label>
        <Input
          value={studentName}
          onChange={(e) => setStudentName(e.target.value)}
          placeholder="Full name"
          required
        />
      </div>
      <div>
        <label className="block text-sm font-medium">Request</label>
        <textarea
          value={requestText}
          onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setRequestText(e.target.value)}
          placeholder="Describe what help is needed..."
          rows={3}
          required
          className="w-full rounded-md border px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>
      <div className="flex gap-2">
        <Button type="submit" disabled={submitRequest.isPending}>
          {submitRequest.isPending ? "Submitting..." : "Submit"}
        </Button>
        <Button type="button" variant="outline" onClick={onClose}>
          Cancel
        </Button>
      </div>
      {submitRequest.isError && (
        <p className="text-xs text-red-600">{String(submitRequest.error)}</p>
      )}
    </form>
  )
}

export function RequestsPage() {
  const { data: requests, isLoading, isError } = useConsultationRequests()
  const [showForm, setShowForm] = useState(false)

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Consultation Requests</h1>
        <Button onClick={() => setShowForm((v) => !v)}>
          {showForm ? "Cancel" : "New request"}
        </Button>
      </div>

      {showForm && <NewRequestForm onClose={() => setShowForm(false)} />}

      {isLoading && <p className="text-gray-500">Loading...</p>}
      {isError && <p className="text-red-600">Failed to load requests.</p>}

      {requests && requests.length === 0 && (
        <p className="text-gray-500">No requests yet.</p>
      )}

      <div className="flex flex-col gap-4">
        {requests?.map((req) => (
          <RequestCard key={req.request_id} request={req} />
        ))}
      </div>
    </div>
  )
}
