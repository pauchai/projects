import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function CreateProjectPage() {
  return (
    <div className="flex justify-center pt-12">
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle>Create a new project</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Project creation form coming in Phase F6.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
