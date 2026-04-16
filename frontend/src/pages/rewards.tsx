import { useMyRewards, useMyRewardHistory } from "@/hooks/use-cohorts"

export function RewardsPage() {
  const { data: balance, isLoading: balanceLoading, isError: balanceError } = useMyRewards()
  const { data: history, isLoading: historyLoading, isError: historyError } = useMyRewardHistory()

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">My Rewards</h1>

      {/* Balance card */}
      {balanceLoading && <p className="text-muted-foreground">Loading balance…</p>}
      {balanceError && <p className="text-destructive">Failed to load reward balance.</p>}
      {balance && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div className="rounded border border-border px-4 py-3 space-y-1">
            <p className="text-xs text-muted-foreground">Total XP</p>
            <p className="text-2xl font-bold">{balance.total_xp}</p>
          </div>
          <div className="rounded border border-border px-4 py-3 space-y-1">
            <p className="text-xs text-muted-foreground">Credits</p>
            <p className="text-2xl font-bold">{balance.total_credits}</p>
          </div>
          <div className="rounded border border-border px-4 py-3 space-y-1">
            <p className="text-xs text-muted-foreground">Reputation</p>
            <p className="text-2xl font-bold">
              {balance.reputation_score != null
                ? Number(balance.reputation_score).toFixed(1)
                : "—"}
            </p>
          </div>
          <div className="rounded border border-border px-4 py-3 space-y-1">
            <p className="text-xs text-muted-foreground">Badges</p>
            <p className="text-2xl font-bold">{balance.badges.length}</p>
          </div>
        </div>
      )}

      {/* Badges list */}
      {balance && balance.badges.length > 0 && (
        <div>
          <h2 className="font-semibold mb-3">Badges</h2>
          <div className="flex flex-wrap gap-2">
            {balance.badges.map((badge) => (
              <span
                key={badge}
                className="rounded-full border border-border px-3 py-1 text-xs font-medium"
              >
                {badge}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Reward history */}
      <div>
        <h2 className="font-semibold mb-3">Reward History</h2>
        {historyLoading && <p className="text-muted-foreground">Loading history…</p>}
        {historyError && <p className="text-destructive">Failed to load reward history.</p>}
        {history && history.length === 0 && (
          <p className="text-muted-foreground text-sm">No rewards yet. Complete tasks to earn XP.</p>
        )}
        {history && history.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-muted-foreground">
                  <th className="pb-2 pr-4">Type</th>
                  <th className="pb-2 pr-4">Amount</th>
                  <th className="pb-2 pr-4">Event</th>
                  <th className="pb-2 pr-4">Cohort</th>
                  <th className="pb-2">Date</th>
                </tr>
              </thead>
              <tbody>
                {history.map((entry) => (
                  <tr key={entry.entry_id} className="border-b border-border">
                    <td className="py-2 pr-4 capitalize">{entry.reward_type}</td>
                    <td className="py-2 pr-4">
                      {entry.amount != null ? entry.amount : "—"}
                    </td>
                    <td className="py-2 pr-4 text-muted-foreground">
                      {entry.triggering_event ?? "—"}
                    </td>
                    <td className="py-2 pr-4 font-mono text-xs text-muted-foreground">
                      {entry.cohort_id ?? "—"}
                    </td>
                    <td className="py-2 text-muted-foreground">
                      {new Date(entry.granted_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
