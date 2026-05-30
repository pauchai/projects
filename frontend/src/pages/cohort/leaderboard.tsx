/**
 * Cohort workspace — Leaderboard tab.
 * Ported from "leaderboard" tab of cohort-detail.tsx.
 */

import { useParams } from "react-router-dom"
import { useCohort, useCohortLeaderboard } from "@/hooks/use-cohorts"
import { useAuthStore } from "@/stores/auth-store"

export function CohortLeaderboardPage() {
  const { cohortId } = useParams<{ cohortId: string }>()
  const userId = useAuthStore((s) => s.userId)
  const { data: cohort, isLoading } = useCohort(cohortId ?? "")
  const { data: leaderboard } = useCohortLeaderboard(cohortId ?? "")

  if (isLoading) return <p className="text-muted-foreground">Loading…</p>
  if (!cohort) return <p className="text-destructive">Cohort not found.</p>

  return (
    <div>
      {!leaderboard || leaderboard.length === 0 ? (
        <p className="text-muted-foreground text-sm">
          No leaderboard data yet. Complete tasks to earn XP.
        </p>
      ) : (
        <div className="space-y-2">
          {leaderboard.map((entry) => (
            <div
              key={entry.learner_id}
              className={`flex items-center gap-4 rounded border border-border px-4 py-3 text-sm ${
                entry.learner_id === userId ? "bg-muted" : ""
              }`}
            >
              <span className="w-6 text-center font-bold text-muted-foreground">
                {entry.rank}
              </span>
              <span className="flex-1 font-mono text-xs">{entry.learner_id}</span>
              <span className="font-semibold">{entry.total_xp} XP</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
