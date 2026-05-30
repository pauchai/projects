/**
 * Project workspace — Fund tab.
 *
 * Shows fund balance, transaction history, and distribution history.
 * Owners/admins can deposit and initiate distributions.
 */

import { useState } from "react"
import { useParams } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useAuthStore } from "@/stores/auth-store"
import { useProject } from "@/hooks/use-projects"
import { useFund, useDeposit, useDistribute } from "@/hooks/use-fund"

// ---------------------------------------------------------------------------
// DepositForm
// ---------------------------------------------------------------------------

function DepositForm({
  projectId,
  onClose,
}: {
  projectId: string
  onClose: () => void
}) {
  const depositMutation = useDeposit(projectId)
  const [amount, setAmount] = useState("")
  const [source, setSource] = useState("manual")
  const [refId, setRefId] = useState("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    depositMutation.mutate(
      {
        amount: Number(amount),
        source: source.trim(),
        ref_id: refId.trim() || null,
      },
      { onSuccess: onClose },
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Deposit</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="depositAmount">
              Amount <span className="text-destructive">*</span>
            </Label>
            <Input
              id="depositAmount"
              type="number"
              min="0.01"
              step="0.01"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.00"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="depositSource">Source</Label>
            <Input
              id="depositSource"
              value={source}
              onChange={(e) => setSource(e.target.value)}
              placeholder="e.g. product_sale, manual"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="depositRefId">Reference ID (optional)</Label>
            <Input
              id="depositRefId"
              value={refId}
              onChange={(e) => setRefId(e.target.value)}
              placeholder="e.g. product_id or transaction_id"
            />
          </div>
          <div className="flex gap-2">
            <Button type="submit" disabled={depositMutation.isPending}>
              {depositMutation.isPending ? "Depositing..." : "Deposit"}
            </Button>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
          </div>
          {depositMutation.isError && (
            <p className="text-sm text-destructive">
              {depositMutation.error instanceof Error
                ? depositMutation.error.message
                : "Failed to deposit"}
            </p>
          )}
        </form>
      </CardContent>
    </Card>
  )
}

// ---------------------------------------------------------------------------
// DistributeForm
// ---------------------------------------------------------------------------

function DistributeForm({
  projectId,
  balance,
  onClose,
}: {
  projectId: string
  balance: number
  onClose: () => void
}) {
  const distributeMutation = useDistribute(projectId)
  const [amount, setAmount] = useState("")
  const [note, setNote] = useState("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    distributeMutation.mutate(
      {
        amount: Number(amount),
        note: note.trim() || null,
      },
      { onSuccess: onClose },
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Distribute</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="distributeAmount">
              Amount <span className="text-destructive">*</span>
            </Label>
            <Input
              id="distributeAmount"
              type="number"
              min="0.01"
              step="0.01"
              max={balance}
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.00"
              required
            />
            <p className="text-xs text-muted-foreground">
              Available balance: ${balance.toFixed(2)}
            </p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="distributeNote">Note (optional)</Label>
            <Input
              id="distributeNote"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Reason for distribution"
            />
          </div>
          <div className="flex gap-2">
            <Button type="submit" disabled={distributeMutation.isPending}>
              {distributeMutation.isPending ? "Submitting..." : "Submit Request"}
            </Button>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
          </div>
          {distributeMutation.isError && (
            <p className="text-sm text-destructive">
              {distributeMutation.error instanceof Error
                ? distributeMutation.error.message
                : "Failed to submit distribution"}
            </p>
          )}
        </form>
      </CardContent>
    </Card>
  )
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export function ProjectFundPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const { data: project } = useProject(projectId ?? "")
  const { data: fund, isLoading, isError, error } = useFund(projectId ?? "")
  const userId = useAuthStore((s) => s.userId)
  const [showDeposit, setShowDeposit] = useState(false)
  const [showDistribute, setShowDistribute] = useState(false)

  const isManager =
    !!userId &&
    !!project &&
    (project.owner_id === userId ||
      project.memberships.some(
        (m) =>
          m.user_id === userId &&
          m.is_active &&
          (m.role === "owner" || m.role === "admin"),
      ))

  if (isLoading) {
    return <p className="text-muted-foreground">Loading fund...</p>
  }

  if (isError) {
    return (
      <p className="text-destructive">
        Failed to load fund:{" "}
        {error instanceof Error ? error.message : "Unknown error"}
      </p>
    )
  }

  const balance = fund?.balance ?? 0
  const transactions = fund?.transactions ?? []
  const distributions = fund?.distributions ?? []

  return (
    <div className="space-y-6">
      {/* Balance card */}
      <Card>
        <CardContent className="pt-6 pb-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Fund Balance</p>
              <p className="text-3xl font-bold">${balance.toFixed(2)}</p>
            </div>
            {isManager && (
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setShowDistribute(false)
                    setShowDeposit((v) => !v)
                  }}
                >
                  Deposit
                </Button>
                <Button
                  size="sm"
                  onClick={() => {
                    setShowDeposit(false)
                    setShowDistribute((v) => !v)
                  }}
                  disabled={balance <= 0}
                >
                  Distribute
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Forms */}
      {showDeposit && projectId && (
        <DepositForm projectId={projectId} onClose={() => setShowDeposit(false)} />
      )}
      {showDistribute && projectId && (
        <DistributeForm
          projectId={projectId}
          balance={balance}
          onClose={() => setShowDistribute(false)}
        />
      )}

      {/* Transactions */}
      {transactions.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
            Transactions
          </h3>
          <div className="space-y-2">
            {transactions.map((tx) => (
              <Card key={tx.transaction_id}>
                <CardContent className="py-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{tx.source}</p>
                    {tx.ref_id && (
                      <p className="text-xs text-muted-foreground font-mono">{tx.ref_id}</p>
                    )}
                    <p className="text-xs text-muted-foreground">
                      {new Date(tx.created_at).toLocaleString()}
                    </p>
                  </div>
                  <span className="text-sm font-semibold text-green-600">
                    +${tx.amount.toFixed(2)}
                  </span>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Distributions */}
      {distributions.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
            Distributions
          </h3>
          <div className="space-y-2">
            {distributions.map((dist) => (
              <Card key={dist.distribution_id}>
                <CardContent className="py-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">
                      {dist.note ?? "Distribution"}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Status: {dist.status} ·{" "}
                      {new Date(dist.created_at).toLocaleString()}
                    </p>
                  </div>
                  <span className="text-sm font-semibold text-orange-600">
                    −${dist.amount.toFixed(2)}
                  </span>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {transactions.length === 0 && distributions.length === 0 && (
        <p className="text-sm text-muted-foreground">No fund activity yet.</p>
      )}
    </div>
  )
}
