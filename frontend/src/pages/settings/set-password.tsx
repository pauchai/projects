/**
 * Set Password page — allows users to set a local password
 * (for accounts that were created via OAuth originally).
 *
 * Accessed via /settings/password — linked from /settings/security
 * when the user doesn't have local credentials.
 */

import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator"
import { useSetPassword } from "@/hooks/use-set-password"
import { ApiError } from "@/api/client"

export function SetPasswordPage() {
  const navigate = useNavigate()
  const setPassword = useSetPassword()
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [fieldError, setFieldError] = useState<string | null>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setFieldError(null)

    if (password.length < 6) {
      setFieldError("Password must be at least 6 characters")
      return
    }

    if (password !== confirmPassword) {
      setFieldError("Passwords do not match")
      return
    }

    setPassword.mutate(password, {
      onSuccess: () => {
        navigate("/settings/security")
      },
    })
  }

  const serverError =
    setPassword.error instanceof ApiError
      ? setPassword.error.detail
      : setPassword.error
        ? "Failed to set password"
        : null

  return (
    <div className="max-w-md mx-auto">
      <Link
        to="/settings/security"
        className="text-sm text-muted-foreground hover:text-foreground"
      >
        &larr; Back to Security Settings
      </Link>

      <h1 className="text-2xl font-bold mt-4 mb-6">Set Password</h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Create a password for your account
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <p className="text-sm text-muted-foreground mb-4">
              Set a password to sign in with email and password
              in addition to your connected OAuth providers.
            </p>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 6 characters"
                disabled={setPassword.isPending}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <Input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Repeat password"
                disabled={setPassword.isPending}
              />
            </div>

            {(fieldError || serverError) && (
              <p className="text-sm text-destructive">
                {fieldError || serverError}
              </p>
            )}

            <Separator />

            <Button
              type="submit"
              className="w-full"
              disabled={setPassword.isPending}
            >
              {setPassword.isPending ? "Setting password..." : "Set Password"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}