import { useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { useMyEarnings, useReleaseEarning } from "@/hooks/use-earnings"
import { ApiError } from "@/api/client"

export function EarningsPage() {
  const { data: summary, isLoading, isError } = useMyEarnings()
  const releaseEarning = useReleaseEarning()
  const [releaseError, setReleaseError] = useState<string | null>(null)
  const [releaseSuccess, setReleaseSuccess] = useState<string | null>(null)

  const handleRelease = async (commissionId: string) => {
    setReleaseError(null)
    setReleaseSuccess(null)
    try {
      await releaseEarning.mutateAsync(commissionId)
      setReleaseSuccess("Payout released successfully.")
    } catch (e) {
      setReleaseError(e instanceof ApiError ? e.detail : "Failed to release payout.")
    }
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">My Earnings</h1>

      {isLoading && <p className="text-muted-foreground">Loading earnings…</p>}
      {isError && <p className="text-destructive">Failed to load earnings.</p>}

      {/* Summary cards */}
      {summary && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-2">
          <div className="rounded border border-border px-4 py-3 space-y-1">
            <p className="text-xs text-muted-foreground">Pending</p>
            <p className="text-2xl font-bold">{Number(summary.total_pending).toFixed(2)}</p>
          </div>
          <div className="rounded border border-border px-4 py-3 space-y-1">
            <p className="text-xs text-muted-foreground">Released</p>
            <p className="text-2xl font-bold">{Number(summary.total_released).toFixed(2)}</p>
          </div>
        </div>
      )}

      {releaseError && <p className="text-destructive text-sm">{releaseError}</p>}
      {releaseSuccess && (
        <p className="text-sm text-green-600 dark:text-green-400">{releaseSuccess}</p>
      )}

      {/* Commissions list */}
      {summary && (
        <div>
          <h2 className="font-semibold mb-3">Commissions</h2>
          {summary.commissions.length === 0 && (
            <p className="text-muted-foreground text-sm">No commissions yet.</p>
          )}
          <div className="space-y-3">
            {summary.commissions.map((c) => {
              const eligibleAt = new Date(c.release_eligible_at)
              const isEligible = eligibleAt <= new Date()
              return (
                <Card key={c.commission_id}>
                  <CardContent className="pt-4 pb-4 flex flex-wrap items-start justify-between gap-3">
                    <div className="space-y-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge
                          variant={c.status === "pending" ? "outline" : "secondary"}
                          className="text-xs capitalize"
                        >
                          {c.status}
                        </Badge>
                        <span className="text-lg font-bold">
                          {Number(c.total_amount).toFixed(2)}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Base {Number(c.base_amount).toFixed(2)} + Bonus{" "}
                        {Number(c.bonus_amount).toFixed(2)}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Module:{" "}
                        <span className="font-mono">{c.module_id}</span>
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Cohort:{" "}
                        <span className="font-mono">{c.cohort_id}</span>
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Earned {new Date(c.earned_at).toLocaleDateString()} · Eligible{" "}
                        {eligibleAt.toLocaleDateString()}
                      </p>
                      {c.released_at && (
                        <p className="text-xs text-muted-foreground">
                          Released {new Date(c.released_at).toLocaleDateString()}
                        </p>
                      )}
                    </div>

                    {c.status === "pending" && (
                      <Button
                        size="sm"
                        disabled={!isEligible || releaseEarning.isPending}
                        onClick={() => handleRelease(c.commission_id)}
                        title={
                          !isEligible
                            ? `Hold period ends ${eligibleAt.toLocaleDateString()}`
                            : undefined
                        }
                      >
                        Release
                      </Button>
                    )}
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
