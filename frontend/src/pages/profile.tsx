import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useAuthStore } from "@/stores/auth-store"

export function ProfilePage() {
  const { email, displayName } = useAuthStore()

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">My Profile</h1>
      <Card>
        <CardHeader>
          <CardTitle>{displayName ?? "User"}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">{email}</p>
          <p className="mt-4 text-muted-foreground">
            Profile dashboard with your projects coming in Phase F8.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
