import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function ProjectsListPage() {
  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">Projects</h1>
      <Card>
        <CardHeader>
          <CardTitle>Browse projects</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Project listing with search and filters coming in Phase F4.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
