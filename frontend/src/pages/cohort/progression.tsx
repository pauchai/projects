/**
 * Cohort workspace — Progression tab.
 * Topic experts + helper metrics.
 * Ported from "progression" tab of cohort-detail.tsx.
 */

import { useParams } from "react-router-dom"
import { Badge } from "@/components/ui/badge"
import { useCohort, useCohortHelperMetrics, useCohortTopicExperts } from "@/hooks/use-cohorts"

export function CohortProgressionPage() {
  const { cohortId } = useParams<{ cohortId: string }>()
  const { data: cohort, isLoading } = useCohort(cohortId ?? "")
  const { data: helperMetrics } = useCohortHelperMetrics(cohortId ?? "")
  const { data: topicExperts } = useCohortTopicExperts(cohortId ?? "")

  if (isLoading) return <p className="text-muted-foreground">Loading…</p>
  if (!cohort) return <p className="text-destructive">Cohort not found.</p>

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-semibold mb-3">Topic Experts</h2>
        {!topicExperts || topicExperts.length === 0 ? (
          <p className="text-muted-foreground text-sm">No topic experts yet.</p>
        ) : (
          <div className="space-y-2">
            {topicExperts.map((e) => (
              <div
                key={e.expert_id}
                className="flex items-center justify-between rounded border border-border px-3 py-2 text-sm"
              >
                <span className="font-mono text-xs">{e.learner_id}</span>
                <Badge variant="secondary">{e.topic_id}</Badge>
              </div>
            ))}
          </div>
        )}
      </div>

      <div>
        <h2 className="font-semibold mb-3">Helper Metrics</h2>
        {!helperMetrics || helperMetrics.length === 0 ? (
          <p className="text-muted-foreground text-sm">No metrics recorded yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-muted-foreground">
                  <th className="pb-2 pr-4">Learner</th>
                  <th className="pb-2 pr-4">Helped</th>
                  <th className="pb-2 pr-4">Answers</th>
                  <th className="pb-2 pr-4">Reviews</th>
                  <th className="pb-2">Avg Satisfaction</th>
                </tr>
              </thead>
              <tbody>
                {helperMetrics.map((m) => (
                  <tr key={m.learner_id} className="border-b border-border">
                    <td className="py-2 pr-4 font-mono text-xs">{m.learner_id}</td>
                    <td className="py-2 pr-4">{m.learners_helped}</td>
                    <td className="py-2 pr-4">{m.questions_answered}</td>
                    <td className="py-2 pr-4">{m.tasks_reviewed}</td>
                    <td className="py-2">
                      {m.average_satisfaction != null
                        ? Number(m.average_satisfaction).toFixed(2)
                        : "—"}
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
