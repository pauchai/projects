import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function LoginPage() {
  return (
    <div className="flex justify-center pt-12">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Log in</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">Login form coming in Phase F3.</p>
        </CardContent>
      </Card>
    </div>
  )
}
