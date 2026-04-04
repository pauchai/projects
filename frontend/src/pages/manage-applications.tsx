import { useParams } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function ManageApplicationsPage() {
  const { projectId } = useParams<{ projectId: string }>()

  return (
    <div>
      <Card>
        <CardHeader>
          <CardTitle>Manage Applications</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Application management for project{" "}
            <code className="text-foreground">{projectId}</code> coming in Phase F7.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
