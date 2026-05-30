import { useState } from "react"
import { Button } from "@/components/ui/button"
import { useCurators } from "@/hooks/use-schedule"
import { useOffers } from "@/hooks/use-schedule"
import { useRespondToOffer } from "@/hooks/use-schedule"
import type { OfferResponse } from "@/api/types"

const STATUS_LABELS: Record<OfferResponse["status"], string> = {
  pending: "Pending",
  accepted: "Accepted",
  declined: "Declined",
}

const STATUS_COLORS: Record<OfferResponse["status"], string> = {
  pending: "bg-yellow-100 text-yellow-800",
  accepted: "bg-green-100 text-green-800",
  declined: "bg-gray-100 text-gray-500",
}

function OfferCard({ offer }: { offer: OfferResponse }) {
  const respond = useRespondToOffer()

  function handle(action: "accept" | "decline") {
    respond.mutate({ offerId: offer.offer_id, data: { action } })
  }

  return (
    <div className="rounded-lg border p-4 shadow-sm">
      <div className="mb-2 flex items-start justify-between gap-2">
        <div className="flex-1">
          <p className="font-semibold">{offer.student_name}</p>
          <p className="mt-1 text-sm text-gray-700">{offer.request_text}</p>
          <p className="mt-1 font-mono text-xs text-gray-400">
            request: {offer.request_id}
          </p>
        </div>
        <span
          className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[offer.status]}`}
        >
          {STATUS_LABELS[offer.status]}
        </span>
      </div>

      {offer.status === "pending" && (
        <div className="mt-3 flex gap-2">
          <Button
            size="sm"
            onClick={() => handle("accept")}
            disabled={respond.isPending}
          >
            Accept
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => handle("decline")}
            disabled={respond.isPending}
          >
            Decline
          </Button>
        </div>
      )}

      {respond.isError && (
        <p className="mt-1 text-xs text-red-600">{String(respond.error)}</p>
      )}
    </div>
  )
}

export function OffersPage() {
  const { data: curators, isLoading: curatorsLoading } = useCurators()
  const [selectedCuratorId, setSelectedCuratorId] = useState("")

  const { data: offers, isLoading: offersLoading, isError } = useOffers(selectedCuratorId)

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">Incoming Offers</h1>

      {/* Curator selector */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700">
          Select your curator profile
        </label>
        <select
          className="mt-1 rounded-md border px-3 py-2 text-sm shadow-sm bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          value={selectedCuratorId}
          onChange={(e) => setSelectedCuratorId(e.target.value)}
        >
          <option value="">— choose curator —</option>
          {curators?.map((c) => (
            <option key={c.curator_id} value={c.curator_id}>
              {c.name}
            </option>
          ))}
        </select>
        {curatorsLoading && (
          <p className="mt-1 text-xs text-gray-400">Loading curators...</p>
        )}
      </div>

      {/* Offers list */}
      {!selectedCuratorId && (
        <p className="text-gray-500">Select a curator above to see their offers.</p>
      )}

      {selectedCuratorId && offersLoading && (
        <p className="text-gray-500">Loading offers...</p>
      )}

      {selectedCuratorId && isError && (
        <p className="text-red-600">Failed to load offers.</p>
      )}

      {selectedCuratorId && offers && offers.length === 0 && (
        <p className="text-gray-500">No offers yet.</p>
      )}

      <div className="flex flex-col gap-4">
        {offers?.map((offer) => (
          <OfferCard key={offer.offer_id} offer={offer} />
        ))}
      </div>
    </div>
  )
}
