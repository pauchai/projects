import { useParams } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>()

  return (
    <div>
      <Card>
        <CardHeader>
          <CardTitle>Project Detail</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Details for project <code className="text-foreground">{projectId}</code> coming in Phase F5.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
