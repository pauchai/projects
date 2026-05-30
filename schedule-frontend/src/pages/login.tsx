import { useState } from "react"
import { useNavigate, useLocation } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useLogin } from "@/hooks/use-auth"
import { ApiError } from "@/api/client"

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const loginMutation = useLogin()

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")

  const from = (location.state as { from?: { pathname: string } } | null)?.from?.pathname ?? "/schedule/curators"

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    loginMutation.mutate(
      { email: email.trim(), password },
      {
        onSuccess: () => {
          navigate(from, { replace: true })
        },
      },
    )
  }

  const serverError =
    loginMutation.error instanceof ApiError
      ? loginMutation.error.detail
      : loginMutation.error
        ? "Login failed. Please try again."
        : null

  return (
    <div className="flex justify-center pt-16">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Schedule — Log in</CardTitle>
        </CardHeader>
        <CardContent>
          {serverError && (
            <p className="mb-4 text-sm text-destructive">{serverError}</p>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={loginMutation.isPending}
            >
              {loginMutation.isPending ? "Logging in..." : "Log in"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
