import { Link } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { FeatureRequestResponse } from "@/api/types"

/** Human-readable status labels and color variants */
const STATUS_CONFIG: Record<
  string,
  { label: string; variant: "default" | "secondary" | "outline" | "destructive" }
> = {
  submitted: { label: "Submitted", variant: "outline" },
  planned: { label: "Planned", variant: "secondary" },
  in_progress: { label: "In Progress", variant: "default" },
  done: { label: "Done", variant: "secondary" },
  rejected: { label: "Rejected", variant: "destructive" },
}

interface FeatureCardProps {
  feature: FeatureRequestResponse
}

export function FeatureCard({ feature }: FeatureCardProps) {
  const statusConfig = STATUS_CONFIG[feature.status] ?? {
    label: feature.status,
    variant: "secondary" as const,
  }

  return (
    <Link to={`/features/${feature.request_id}`} className="block">
      <Card className="transition-colors hover:border-primary/50">
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between gap-2">
            <CardTitle className="text-lg leading-snug">
              {feature.title}
            </CardTitle>
            <Badge variant={statusConfig.variant} className="shrink-0">
              {statusConfig.label}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <p className="mb-3 line-clamp-2 text-sm text-muted-foreground">
            {feature.description}
          </p>
          <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            {feature.category && (
              <Badge variant="outline" className="text-xs">
                {feature.category}
              </Badge>
            )}
            {feature.priority && (
              <Badge variant="outline" className="text-xs">
                {feature.priority}
              </Badge>
            )}
            <span className="ml-auto">
              {new Date(feature.created_at).toLocaleDateString()}
            </span>
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}
